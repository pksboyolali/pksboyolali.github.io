#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrasi konten Blogger (Google Takeout, berkas feed.atom) menjadi artikel Hugo.

Cara pakai (dari folder situs, yang berisi hugo.toml):

    # 1. Uji coba: hanya menampilkan rencana, tidak menulis apa pun
    python scripts/migrasi_blogger.py --cek

    # 2. Uji 5 artikel dulu, lihat hasilnya di content/posts/
    python scripts/migrasi_blogger.py --batas 5

    # 3. Migrasi penuh + unduh gambar (perkiraan: 807 artikel, ±772 gambar)
    python scripts/migrasi_blogger.py

    # 4. Tanpa mengunduh gambar (gambar tetap menunjuk ke server Blogger)
    python scripts/migrasi_blogger.py --tanpa-gambar

Hasil:
  content/posts/<slug>.md        artikel (satu berkas per artikel)
  static/images/uploads/YYYY/MM/ gambar hasil unduhan
  _migrasi/laporan.md            laporan hasil migrasi
  _migrasi/komentar.yaml         arsip komentar lama (tidak dirender)

Catatan penting:
- Alamat lama (/2015/10/judul-artikel.html) dipertahankan lewat "url:" di front
  matter, jadi tautan dan hasil pencarian Google tidak rusak.
- Artikel yang masih berstatus draf atau menunggu moderasi di Blogger ikut
  dimigrasi sebagai "draft: true" (tidak tampil di situs, tetap bisa dibuka
  lewat admin).
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Pengaturan dasar
# ---------------------------------------------------------------------------
NS = {"a": "http://www.w3.org/2005/Atom", "b": "http://schemas.google.com/blogger/2018"}
WIB = timezone(timedelta(hours=7))  # situs ini memakai waktu Indonesia Barat

FEED_BAWAAN = Path(
    "../Takeout/Blogger/Blogs/DPD PKS BOYOLALI/feed.atom"
)

# Domain lama yang tautannya harus diubah menjadi tautan internal.
DOMAIN_LAMA = (
    "dpdpksboyolali.blogspot.com",
    "www.dpdpksboyolali.blogspot.com",
    "pksboyolali.blogspot.com",
    "boyolali.pks.id",
)

# Nama label di Blogger (huruf besar) -> nama kategori di situs.
# Kategori ini harus sama persis dengan folder content/categories/ dan pilihan
# "Kategori" di static/admin/config.yml.
KATEGORI = {
    "PILKADA": "Pilkada",
    "TOPIK PILIHAN": "Topik Pilihan",
    "INSPIRASI": "Inspirasi",
    "FRAKSI PKS": "Fraksi PKS",
    "KIPRAH KAMI": "Kiprah Kami",
    "SEPUTAR PKS": "Seputar PKS",
    "OASE": "Oase",
    "HAROKAH": "Harokah",
    "SEPUTAR BOYOLALI": "Seputar Boyolali",
    "RAGAM": "Ragam",
}

# Singkatan yang hurufnya harus tetap besar saat nama kategori dibuat otomatis.
SINGKATAN = {"PKS", "DPD", "DPW", "DPC", "MPR", "DPR", "DPRD", "RI", "PILKADA"}

# Host gambar milik Blogger/Google. Gambar dari host lain (situs berita) ikut
# diunduh supaya tidak rusak ketika situs lama memblokir hotlink atau memakai
# http:// (browser memblokir gambar http di halaman https).
HOST_UNDUH = ("blogger.googleusercontent.com", "firebasestorage.googleapis.com", "bp.blogspot.com")

UA = "Mozilla/5.0 (compatible; migrasi-pks/1.0)"

IMG_SRC = re.compile(r'(<img\b[^>]*?\bsrc\s*=\s*)(["\'])(.*?)\2', re.I | re.S)
A_HREF = re.compile(r'(<a\b[^>]*?\bhref\s*=\s*)(["\'])(.*?)\2', re.I | re.S)
ATTR_STYLE = re.compile(r'\s+style\s*=\s*(["\']).*?\1', re.I | re.S)
UKURAN_GAMBAR = re.compile(r"/s\d+(-[a-z]+)?/")
TAG_KOSONG = re.compile(r"<(span|b|i|em|strong|div|p)\b[^>]*>\s*(?:<br\s*/?>)?\s*</\1>", re.I)


# ---------------------------------------------------------------------------
# Bantu
# ---------------------------------------------------------------------------
def yq(nilai: str) -> str:
    """Teks aman untuk YAML (string berkutip ganda)."""
    return json.dumps(nilai, ensure_ascii=False)


def slugify(teks: str, maks: int = 70) -> str:
    t = unicodedata.normalize("NFKD", teks).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    if len(t) > maks:
        t = t[:maks].rsplit("-", 1)[0]
    return t or "artikel"


def nama_kategori(label: str) -> str:
    """'FRAKSI PKS' -> 'Fraksi PKS'."""
    label = (label or "").strip()
    if not label:
        return ""
    if label.upper() in KATEGORI:
        return KATEGORI[label.upper()]
    kata = []
    for k in label.split():
        kata.append(k.upper() if k.upper() in SINGKATAN else k.capitalize())
    return " ".join(kata)


def tanggal_wib(teks: str) -> datetime | None:
    if not teks:
        return None
    try:
        d = datetime.fromisoformat(teks.replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(WIB)


def iso_wib(d: datetime) -> str:
    """2015-10-11T07:33:00+07:00"""
    return d.strftime("%Y-%m-%dT%H:%M:%S") + "+07:00"


def nama_berkas_gambar(url: str) -> str:
    """Nama berkas lokal yang rapi + pendek + unik (hash 8 huruf dari URL)."""
    bersih = urllib.parse.urlparse(url).path.rsplit("/", 1)[-1]
    bersih = urllib.parse.unquote(bersih)
    inti, titik, ext = bersih.rpartition(".")
    if not titik:
        inti, ext = bersih, "jpg"
    ext = ext.lower()[:4]
    if ext not in ("jpg", "jpeg", "png", "gif", "webp", "svg", "avif"):
        ext = "jpg"
    inti = slugify(inti, 50)
    return f"{inti}-{hashlib.sha1(url.encode()).hexdigest()[:8]}.{ext}"


def perbesar_gambar(url: str) -> str:
    """Blogger menyimpan beberapa ukuran: /s320/, /s640/, /s1600/.
    Kita minta yang paling besar supaya tidak buram di layar lebar."""
    if "googleusercontent" in url or "blogspot" in url:
        return UKURAN_GAMBAR.sub("/s1600/", url, count=1)
    return url


def unduh(url: str, tujuan: Path, ulang: int = 2) -> bool:
    """Unduh satu berkas. Berkas yang sudah ada dilewati (bisa dijalankan ulang)."""
    if tujuan.exists() and tujuan.stat().st_size > 0:
        return True
    tujuan.parent.mkdir(parents=True, exist_ok=True)
    for percobaan in range(ulang + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()
            if not data:
                return False
            tujuan.write_bytes(data)
            return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            if percobaan < ulang:
                time.sleep(1.5 * (percobaan + 1))
    return False


# ---------------------------------------------------------------------------
# Pengolahan isi artikel
# ---------------------------------------------------------------------------
class Pengolah:
    def __init__(self, out: Path, unduh_gambar: bool, cek: bool = False, eksternal: bool = True):
        self.out = out
        self.unduh_gambar = unduh_gambar
        self.cek = cek  # mode cek: jangan sentuh jaringan sama sekali
        self.eksternal = eksternal  # unduh juga gambar dari situs lain
        self.stat = {"gambar_ok": 0, "gambar_gagal": 0, "gambar_luar": 0, "tautan": 0}
        self.gagal: list[str] = []

    # -- gambar ------------------------------------------------------------
    def gambar(self, html: str, tahun: str, bulan: str) -> str:
        def ganti(m: re.Match) -> str:
            awal, kutip, url = m.group(1), m.group(2), m.group(3)
            if not url or url.startswith("data:"):
                return m.group(0)
            # URL di HTML memakai &amp; — untuk diunduh harus & biasa
            url_bersih = html_lib.unescape(url)
            host = urllib.parse.urlparse(url_bersih).netloc.lower()
            milik_blogger = any(host.endswith(h) for h in HOST_UNDUH)
            if not milik_blogger and not self.eksternal:
                self.stat["gambar_luar"] += 1
                return m.group(0)  # gambar situs lain: biarkan apa adanya
            if not self.unduh_gambar:
                return m.group(0)

            asli = perbesar_gambar(url_bersih) if milik_blogger else url_bersih
            nama = nama_berkas_gambar(asli)
            lokal = f"/images/uploads/{tahun}/{bulan}/{nama}"
            tujuan = self.out / "static" / "images" / "uploads" / tahun / bulan / nama
            if self.cek:                      # mode cek: hitung saja, tanpa unduh
                self.stat["gambar_ok"] += 1
                return f"{awal}{kutip}{lokal}{kutip}"
            if unduh(asli, tujuan):
                self.stat["gambar_ok"] += 1
                return f"{awal}{kutip}{lokal}{kutip}"
            # gagal: coba ukuran asli, lalu menyerah dan pertahankan URL lama
            if asli != url_bersih and unduh(url_bersih, tujuan):
                self.stat["gambar_ok"] += 1
                return f"{awal}{kutip}{lokal}{kutip}"
            self.stat["gambar_gagal"] += 1
            self.gagal.append(url_bersih)
            return m.group(0)

        return IMG_SRC.sub(ganti, html)

    # -- tautan ------------------------------------------------------------
    def tautan(self, html: str, tahun: str, bulan: str) -> str:
        def ganti(m: re.Match) -> str:
            awal, kutip, url = m.group(1), m.group(2), m.group(3)
            if not url:
                return m.group(0)
            url_bersih = html_lib.unescape(url)

            # Gambar yang dibungkus tautan (lightbox Blogger): arahkan ke berkas lokal.
            # Nama berkasnya sama dengan <img> karena keduanya dinormalkan ke /s1600/.
            if re.search(r"\.(jpe?g|png|gif|webp|avif)$", url_bersih, re.I):
                host = urllib.parse.urlparse(url_bersih).netloc.lower()
                milik_blogger = any(host.endswith(h) for h in HOST_UNDUH)
                if self.unduh_gambar and (milik_blogger or self.eksternal):
                    asli = perbesar_gambar(url_bersih) if milik_blogger else url_bersih
                    self.stat["tautan"] += 1
                    return (f"{awal}{kutip}/images/uploads/{tahun}/{bulan}/"
                            f"{nama_berkas_gambar(asli)}{kutip}")

            # Tautan ke halaman lain di blog lama -> jadikan tautan internal
            u = urllib.parse.urlparse(url_bersih)
            if u.netloc.lower() in DOMAIN_LAMA:
                self.stat["tautan"] += 1
                tujuan = u.path or "/"
                if u.query:
                    tujuan += "?" + u.query
                return f"{awal}{kutip}{tujuan}{kutip}"

            # Tautan label lama: /search/label/SEPUTAR%20PKS -> /kategori/seputar-pks/
            if "/search/label/" in url_bersih:
                label = urllib.parse.unquote(url_bersih.split("/search/label/")[-1].split("?")[0])
                kat = nama_kategori(label.replace("+", " "))
                if kat:
                    self.stat["tautan"] += 1
                    return f"{awal}{kutip}/kategori/{slugify(kat)}{kutip}"
            return m.group(0)

        return A_HREF.sub(ganti, html)

    # -- pembersihan -------------------------------------------------------
    def bersihkan(self, html: str) -> str:
        """Buang sisa-sisa gaya dari situs lain yang menempel saat copy-paste."""
        h = ATTR_STYLE.sub("", html)          # style="font-size:14px;..." dsb.
        h = re.sub(r"<o:p>\s*</o:p>", "", h, flags=re.I)
        h = re.sub(r"<xml>.*?</xml>", "", h, flags=re.I | re.S)
        for _ in range(3):                     # bersihkan tag kosong berlapis
            h = TAG_KOSONG.sub("", h)
        h = re.sub(r"<p>\s*</p>", "", h, flags=re.I)
        h = re.sub(r"(<br\s*/?>\s*){3,}", "<br /><br />", h, flags=re.I)
        h = re.sub(r"[ \t]+\n", "\n", h)
        h = re.sub(r"\n{3,}", "\n\n", h)
        return h.strip()

    def gambar_pertama(self, html: str) -> str:
        m = IMG_SRC.search(html)
        return m.group(3) if m else ""


# ---------------------------------------------------------------------------
# Feed
# ---------------------------------------------------------------------------
def baca_feed(path: Path):
    root = ET.parse(path).getroot()
    artikel, halaman, komentar = [], [], []
    for e in root.findall("a:entry", NS):
        jenis = (e.findtext("b:type", default="", namespaces=NS) or "").upper()
        if jenis == "POST":
            artikel.append(e)
        elif jenis == "PAGE":
            halaman.append(e)
        elif jenis == "COMMENT":
            komentar.append(e)
    return root, artikel, halaman, komentar


def teks(e: ET.Element, tag: str) -> str:
    return (e.findtext(tag, default="", namespaces=NS) or "").strip()


def main() -> int:
    p = argparse.ArgumentParser(
        description="Migrasi artikel Blogger (Takeout) menjadi konten Hugo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--feed", default=str(FEED_BAWAAN), help="berkas feed.atom hasil Takeout")
    p.add_argument("--out", default=".", help="folder situs Hugo (bawaan: folder saat ini)")
    p.add_argument("--tanpa-gambar", action="store_true", help="jangan unduh gambar")
    p.add_argument("--tanpa-gambar-eksternal", action="store_true",
                   help="gambar dari situs berita lain dibiarkan menunjuk ke alamat aslinya")
    p.add_argument("--batas", type=int, default=0, help="batasi jumlah artikel (untuk uji coba)")
    p.add_argument("--cek", action="store_true", help="hanya tampilkan rencana, tidak menulis berkas")
    a = p.parse_args()

    feed = Path(a.feed)
    if not feed.exists():
        print(f"Berkas feed tidak ditemukan:\n  {feed}\n"
              f"Unduh lewat Blogger: Setelan > Cadangkan konten, atau pakai Google Takeout.")
        return 1

    out = Path(a.out).resolve()
    if not (out / "hugo.toml").exists():
        print(f"Folder {out} tidak berisi hugo.toml. Jalankan dari folder situs "
              f"atau pakai --out.")
        return 1

    root, artikel, halaman, komentar = baca_feed(feed)
    judul_blog = teks(root, "a:title")
    print(f"Blog       : {judul_blog}")
    print(f"Artikel    : {len(artikel)}")
    print(f"Halaman    : {len(halaman)}")
    print(f"Komentar   : {len(komentar)}")
    print(f"Gambar     : {'diunduh ke repo' if not a.tanpa_gambar else 'tetap di server Blogger'}")
    print(f"Mode       : {'CEK (tidak menulis)' if a.cek else 'TULIS'}")
    print()

    if a.batas:
        artikel = artikel[: a.batas]
        print(f"Dibatasi: {len(artikel)} artikel pertama\n")

    olah = Pengolah(out, not a.tanpa_gambar, cek=a.cek, eksternal=not a.tanpa_gambar_eksternal)
    dipakai: dict[str, int] = {}     # hindari dua artikel dengan nama berkas sama
    ditulis = 0
    baris_laporan = []

    for e in artikel:
        status = teks(e, "b:status").upper()
        judul = teks(e, "a:title") or "(tanpa judul)"
        tgl = tanggal_wib(teks(e, "a:published")) or tanggal_wib(teks(e, "b:created"))
        if tgl is None:
            print(f"  ! lewati (tanggal tidak terbaca): {judul}")
            continue

        alamat_lama = teks(e, "b:filename")          # contoh: /2015/10/judul.html
        isi = e.findtext("a:content", default="", namespaces=NS) or ""

        tahun, bulan = tgl.strftime("%Y"), tgl.strftime("%m")
        isi = olah.gambar(isi, tahun, bulan)         # gambar dulu (isi folder dipakai tautan)
        isi = olah.tautan(isi, tahun, bulan)
        isi = olah.bersihkan(isi)

        # Kategori dari label Blogger
        label = [teks_c.get("term", "") for teks_c in e.findall("a:category", NS)]
        kategori = []
        for l in label:
            k = nama_kategori(l)
            if k and k not in kategori:
                kategori.append(k)

        # Nama berkas: dari alamat lama, supaya mudah dicari
        inti = alamat_lama.rstrip("/").rsplit("/", 1)[-1]
        inti = inti[:-5] if inti.endswith(".html") else inti
        nama = slugify(inti or judul, 80)
        dipakai[nama] = dipakai.get(nama, 0) + 1
        if dipakai[nama] > 1:                         # judul sama di bulan berbeda
            nama = f"{nama}-{dipakai[nama]}"

        gambar_sampul = olah.gambar_pertama(isi)
        draft = status in ("DRAFT", "PENDING_MODERATION")

        fm = ["---", f"title: {yq(judul)}", f"date: {iso_wib(tgl)}"]
        if alamat_lama:
            fm.append(f"url: {yq(alamat_lama)}")
        if kategori:
            fm.append("categories: [" + ", ".join(yq(k) for k in kategori) + "]")
        else:
            fm.append("categories: []")
        fm.append("tags: []")
        if gambar_sampul:
            fm.append(f"image: {yq(gambar_sampul)}")
        fm.append(f"draft: {'true' if draft else 'false'}")
        fm.append("---")
        dokumen = "\n".join(fm) + "\n\n" + isi + "\n"

        tujuan = out / "content" / "posts" / f"{nama}.md"
        if not a.cek:
            tujuan.parent.mkdir(parents=True, exist_ok=True)
            tujuan.write_text(dokumen, encoding="utf-8")

        ditulis += 1
        baris_laporan.append((judul, nama, tgl.strftime("%Y-%m-%d"), status, ", ".join(kategori)))
        if ditulis % 50 == 0:
            print(f"  ... {ditulis} artikel")

    # ---- komentar (arsip) -------------------------------------------------
    if komentar and not a.cek:
        folder = out / "_migrasi"
        folder.mkdir(parents=True, exist_ok=True)
        baris = ["# Arsip komentar Blogger. Tidak ditampilkan di situs.",
                 "# Disimpan agar isinya tidak hilang saat blog lama ditutup.", ""]
        for c in komentar:
            baris.append(f"- artikel: {yq(teks(c, 'a:title'))}")
            baris.append(f"  penulis: {yq(teks(c, 'a:author/a:name'))}")
            baris.append(f"  tanggal: {yq(teks(c, 'a:published'))}")
            isi_c = re.sub(r"<[^>]+>", " ", c.findtext("a:content", default="", namespaces=NS) or "")
            baris.append(f"  isi: {yq(' '.join(isi_c.split()))}")
        (folder / "komentar.yaml").write_text("\n".join(baris) + "\n", encoding="utf-8")

    # ---- laporan ---------------------------------------------------------
    if not a.cek:
        folder = out / "_migrasi"
        folder.mkdir(parents=True, exist_ok=True)
        lap = [
            "# Laporan migrasi Blogger → Hugo",
            "",
            f"- Sumber: `{feed.name}`",
            f"- Waktu: {datetime.now().strftime('%d-%m-%Y %H:%M')}",
            f"- Artikel ditulis: {ditulis}",
            f"- Gambar diunduh: {olah.stat['gambar_ok']}, gagal: {olah.stat['gambar_gagal']}",
            f"- Gambar situs lain (tidak diunduh): {olah.stat['gambar_luar']}",
            f"- Tautan disesuaikan: {olah.stat['tautan']}",
            f"- Komentar diarsipkan: {len(komentar)}",
            "",
            "## Daftar artikel",
            "",
            "| Judul | Berkas | Tanggal | Status | Kategori |",
            "| --- | --- | --- | --- | --- |",
        ]
        for j, n, t, s, k in baris_laporan:
            lap.append(f"| {j.replace('|', '/')} | `{n}` | {t} | {s} | {k} |")
        if olah.gagal:
            lap += ["", "## Gambar yang gagal diunduh", ""]
            lap += [f"- {u}" for u in olah.gagal[:300]]
        (folder / "laporan.md").write_text("\n".join(lap) + "\n", encoding="utf-8")

    print()
    print(f"Selesai. {ditulis} artikel ditulis ke content/posts/")
    print(f"Gambar: {olah.stat['gambar_ok']} diunduh, {olah.stat['gambar_gagal']} gagal, "
          f"{olah.stat['gambar_luar']} milik situs lain (dibiarkan)")
    if olah.gagal:
        print("Daftar gambar gagal ada di _migrasi/laporan.md — jalankan ulang skrip untuk mencoba lagi.")
    if not a.cek:
        print("\nLangkah berikutnya:")
        print("  python scripts/pra_build.py     (buat halaman arsip)")
        print("  hugo server                     (lihat hasilnya di http://localhost:1313)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
