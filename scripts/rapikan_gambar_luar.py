#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merapikan gambar "asing" yang tersisa setelah migrasi Blogger.

Kenapa perlu:
  Isi artikel lama banyak yang menyalin gambar dari situs lain (pks.or.id,
  solopos, timlo, ...) memakai alamat http://. Situs baru berjalan di https://
  (GitHub Pages), dan browser MEMBLOKIR gambar http:// di halaman https://.
  Kalau dibiarkan, pengunjung melihat ikon gambar rusak.

Yang dilakukan skrip ini, untuk setiap <img> yang bukan /images/uploads/...:
  1. Gambar inline (data:image/...;base64) diubah menjadi berkas biasa.
  2. Alamat http:// dicoba dinaikkan ke https:// lalu diunduh ke repo.
  3. Kalau tetap gagal (situsnya sudah mati), tag <img> dibuang supaya tidak
     ada ikon rusak, dan alamatnya dicatat di _migrasi/gambar-luar.md agar
     pengurus bisa mengunggah ulang fotonya bila penting.
  4. Gambar pelacak (facebook pixel dll.) dibuang tanpa dicatat.
  5. Front matter "image" yang menunjuk gambar mati diperbaiki: dipakai gambar
     lokal pertama di isi artikel, atau dihapus agar tema memakai gambar bawaan.

Cara pakai (dari folder situs):
    python scripts/rapikan_gambar_luar.py --cek     # lihat rencana saja
    python scripts/rapikan_gambar_luar.py           # jalankan
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html as html_lib
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (compatible; migrasi-pks/1.0)"
REFERER = "https://dpdpksboyolali.blogspot.com/"

# Tag <img ...> utuh (termasuk kalau ditulis multi-baris).
IMG_TAG = re.compile(r"<img\b[^>]*?>", re.I | re.S)
SRC_ATTR = re.compile(r'\bsrc\s*=\s*(["\'])(.*?)\1', re.I | re.S)
ALT_ATTR = re.compile(r'\balt\s*=\s*(["\'])(.*?)\1', re.I | re.S)
# <a ...> ... </a> yang membungkus gambar (lightbox Blogger)
A_WRAP = re.compile(r"<a\b[^>]*?href\s*=\s*([\"'])(.*?)\1[^>]*>\s*(<img\b[^>]*?>)\s*</a>", re.I | re.S)
# Tautan gambar lokal yang membungkus gambar lokal lain (kasus lightbox Blogger:
# href memakai ukuran asli, src memakai ukuran lain -> nama berkas bisa berbeda)
A_IMG_LOKAL = re.compile(
    r'<a\b([^>]*?)href\s*=\s*(["\'])(/images/uploads/[^"\']+)\2([^>]*)>\s*'
    r'(<img\b[^>]*?src\s*=\s*(["\'])(/images/uploads/[^"\']+)\6[^>]*>)',
    re.I | re.S)
SEPARATOR_KOSONG = re.compile(r'<div\b[^>]*class="[^"]*separator[^"]*"[^>]*>\s*</div>', re.I | re.S)
# Wadah keterangan gambar Blogger: <table class="tr-caption-container">…</table>.
# Kalau gambarnya dibuang, tabel ini tersisa sebagai kotak kosong.
TABEL_CAPTION = re.compile(
    r'<table\b[^>]*class="[^"]*tr-caption-container[^"]*"[^>]*>.*?</table>', re.I | re.S)
# Div yang isinya hanya spasi, &nbsp;, atau <br>
DIV_KOSONG = re.compile(r'<div\b[^>]*>(?:\s|&nbsp;|<br\s*/?>)*</div>', re.I)
# Tautan tanpa isi, mis. <a href="..." imageanchor="1"></a> yang gambarnya sudah dibuang
A_KOSONG = re.compile(r'<a\b[^>]*>\s*</a>', re.I | re.S)
# Sisa kode Facebook SDK yang menempel saat artikel disalin dari situs lain.
# Iframe-nya tidak terlihat, alamatnya sudah mati, dan hanya memperlambat halaman.
SISA_EMBED = (
    re.compile(r'<iframe\b[^>]*id="fb_xdm_frame[^"]*"[^>]*>\s*</iframe>', re.I | re.S),
    re.compile(r'<div\b[^>]*id="fb-root"[^>]*>\s*</div>', re.I | re.S),
)

# Gambar pelacak / bukan konten: langsung dibuang, tidak perlu dicatat.
PELACAK = (
    "staticxx.facebook.com",
    "s-static.ak.facebook.com",
    "google-analytics.com",
    "googletagmanager.com",
    "doubleclick.net",
    "feeds.feedburner.com",
)

EXT_SAH = {"jpg", "jpeg", "png", "gif", "webp", "avif", "svg"}

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


# ---------------------------------------------------------------------------
# Bantu
# ---------------------------------------------------------------------------
def slugify(teks: str, maks: int = 40) -> str:
    t = re.sub(r"[^a-z0-9]+", "-", teks.lower()).strip("-")
    return (t[:maks].rstrip("-") or "gambar")


def nama_berkas(url: str, ext_paksa: str = "") -> str:
    """Nama berkas lokal: ringkas + hash agar unik dan tidak bentrok."""
    path = urllib.parse.urlparse(url).path
    inti = urllib.parse.unquote(path.rsplit("/", 1)[-1])
    inti, titik, ext = inti.rpartition(".")
    if not titik:
        inti, ext = inti, ""
    ext = (ext_paksa or ext).lower()[:4]
    if ext not in EXT_SAH:
        ext = "jpg"
    return f"{slugify(inti or 'gambar')}-{hashlib.sha1(url.encode()).hexdigest()[:8]}.{ext}"


def ekstensi_dari_ctipe(ctipe: str) -> str:
    ctipe = (ctipe or "").lower()
    for k, v in (("jpeg", "jpg"), ("jpg", "jpg"), ("png", "png"), ("gif", "gif"),
                 ("webp", "webp"), ("avif", "avif"), ("svg", "svg")):
        if k in ctipe:
            return v
    return "jpg"


def unduh(url: str, ulang: int = 0):
    """Kembalikan (data, ekstensi) atau (None, '') bila gagal.

    Batas waktu dibuat pendek (12 detik) karena banyak situs sumber sudah mati;
    menunggu lama untuk situs yang tidak akan pernah menjawab hanya memperlambat
    seluruh proses.
    """
    for percobaan in range(ulang + 1):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Referer": REFERER,
                              "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"})
            with urllib.request.urlopen(req, timeout=12, context=CTX) as resp:
                ctipe = resp.headers.get("Content-Type", "")
                data = resp.read()
            # Halaman HTML (404 yang dibalut) jangan disimpan sebagai gambar
            if not data or ctipe.startswith("text/"):
                return None, ""
            return data, ekstensi_dari_ctipe(ctipe)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError,
                ValueError):
            if percobaan < ulang:
                time.sleep(1.0)
    return None, ""


def tanggal_artikel(teks_fm: str) -> tuple[str, str]:
    """Ambil tahun & bulan dari front matter untuk folder gambar."""
    m = re.search(r"^date:\s*['\"]?(\d{4})-(\d{2})", teks_fm, re.M)
    return (m.group(1), m.group(2)) if m else ("lain", "lain")


def pisah_front_matter(isi: str) -> tuple[str, str]:
    if isi.startswith("---"):
        akhir = isi.find("\n---", 3)
        if akhir != -1:
            return isi[: akhir + 4], isi[akhir + 4:]
    return "", isi


# ---------------------------------------------------------------------------
# Inti
# ---------------------------------------------------------------------------
class Perapi:
    def __init__(self, root: Path, cek: bool, hapus_mati: bool):
        self.root = root
        self.cek = cek
        self.hapus_mati = hapus_mati
        self.stat = {"inline": 0, "diunduh": 0, "mati": 0, "pelacak": 0, "lokal": 0, "tautan": 0, "embed": 0, "wadah": 0}
        self.mati: list[tuple[str, str, str]] = []   # (berkas, judul, url)
        # Alamat yang sama sering muncul di banyak artikel. Hasil percobaan
        # pertama disimpan di sini supaya situs yang mati tidak ditunggu berulang
        # kali (ini yang membuat proses migrasi jadi lambat).
        self.cache: dict[str, str | None] = {}

    def simpan(self, data: bytes, nama: str, tahun: str, bulan: str) -> str:
        """Tulis berkas gambar, kembalikan URL publiknya."""
        tujuan = self.root / "static" / "images" / "uploads" / tahun / bulan / nama
        if not self.cek:
            tujuan.parent.mkdir(parents=True, exist_ok=True)
            tujuan.write_bytes(data)
        return f"/images/uploads/{tahun}/{bulan}/{nama}"

    def ada(self, url: str) -> bool:
        """Apakah berkas gambar di alamat lokal ini benar-benar ada di static/?"""
        rel = url.lstrip("/")
        return (self.root / "static" / rel).exists()

    def selaraskan_tautan(self, html: str) -> str:
        """Perbaiki tautan lightbox yang menunjuk berkas tidak ada.

        Blogger menyimpan tautan gambar memakai ukuran asli sedangkan yang
        ditampilkan memakai ukuran lain. Keduanya menjadi nama berkas berbeda
        saat diunduh, sehingga tautannya bisa menunjuk berkas yang tidak ada.
        Solusinya: arahkan tautan ke berkas yang dipakai gambarnya.
        """
        def ganti(m: re.Match) -> str:
            href = html_lib.unescape(m.group(3))
            src = html_lib.unescape(m.group(7))
            if href == src or self.ada(href):
                return m.group(0)
            if not self.ada(src):
                return m.group(0)
            self.stat["tautan"] += 1
            return (f'<a{m.group(1)}href="{src}"{m.group(4)}>' + m.group(5))

        return A_IMG_LOKAL.sub(ganti, html)

    def proses_gambar(self, tag: str, tahun: str, bulan: str) -> str:
        """Kembalikan tag pengganti, atau '' bila gambar dibuang."""
        m = SRC_ATTR.search(tag)
        if not m:
            return tag
        kutip, url = m.group(1), html_lib.unescape(m.group(2))

        if not url or url.startswith("/images/"):
            self.stat["lokal"] += 1
            return tag

        # 1. Gambar inline base64 -> berkas biasa
        if url.startswith("data:image/"):
            try:
                head, b64 = url.split(",", 1)
                ext = ekstensi_dari_ctipe(head)
                data = base64.b64decode(b64)
            except (ValueError, TypeError):
                return ""
            nama = nama_berkas("inline-" + hashlib.sha1(url.encode()).hexdigest(), ext)
            lokal = self.simpan(data, nama, tahun, bulan)
            self.stat["inline"] += 1
            return tag[: m.start(2)] + lokal + tag[m.end(2):]

        # 2. Protokol-relatif (//host/...) -> https
        if url.startswith("//"):
            url = "https:" + url

        host = urllib.parse.urlparse(url).netloc.lower()
        if any(host.endswith(h) for h in PELACAK):
            self.stat["pelacak"] += 1
            return ""

        # 3. Alamat ini sudah pernah dicoba? Pakai hasilnya, jangan ulangi.
        if url in self.cache:
            lokal = self.cache[url]
            if lokal:
                return tag[: m.start(2)] + lokal + tag[m.end(2):]
            self.stat["mati"] += 1
            return "" if self.hapus_mati else tag

        # 4. Coba unduh: https dulu (kalau masih http), lalu alamat aslinya
        calon = [url]
        if url.startswith("http://"):
            calon.insert(0, "https://" + url[len("http://"):])
        data = ext = None
        dipakai = ""
        for u in calon:
            data, ext = unduh(u)
            if data:
                dipakai = u
                break
        if data:
            nama = nama_berkas(dipakai, ext)
            lokal = self.simpan(data, nama, tahun, bulan)
            self.cache[url] = lokal
            self.stat["diunduh"] += 1
            return tag[: m.start(2)] + lokal + tag[m.end(2):]

        # 5. Gagal: catat sekali, lalu buang tag (opsional) supaya tidak ada
        #    ikon gambar rusak di halaman.
        self.cache[url] = None
        self.stat["mati"] += 1
        self.mati.append(("", "", url))
        return "" if self.hapus_mati else tag

    def proses_berkas(self, path: Path) -> bool:
        asli = path.read_text(encoding="utf-8")
        fm, isi = pisah_front_matter(asli)
        tahun, bulan = tanggal_artikel(fm)

        # Buang pembungkus <a> yang menautkan gambar mati (lightbox Blogger)
        def ganti_a(m: re.Match) -> str:
            tag = self.proses_gambar(m.group(3), tahun, bulan)
            if not tag:
                return ""
            return m.group(0).replace(m.group(3), tag)

        baru = A_WRAP.sub(ganti_a, isi)
        baru = IMG_TAG.sub(lambda m: self.proses_gambar(m.group(0), tahun, bulan), baru)
        baru = self.selaraskan_tautan(baru)

        # Sisa wadah gambar yang kini kosong
        baru = SEPARATOR_KOSONG.sub("", baru)
        for pola in SISA_EMBED:
            baru, n = pola.subn("", baru)
            self.stat["embed"] += n

        # Tabel keterangan gambar yang gambarnya sudah tidak ada
        def buang_tabel(m: re.Match) -> str:
            if "<img" in m.group(0).lower():
                return m.group(0)
            self.stat["wadah"] += 1
            return ""

        baru = TABEL_CAPTION.sub(buang_tabel, baru)

        # Div kosong berlapis (sisa <div class="separator"> yang dibuka berkali-kali)
        for _ in range(4):
            baru, n1 = DIV_KOSONG.subn("", baru)
            baru, n2 = A_KOSONG.subn("", baru)
            self.stat["wadah"] += n1 + n2
            if not (n1 or n2):
                break

        baru = re.sub(r"(?:<br\s*/?>\s*){3,}", "<br /><br />", baru, flags=re.I)
        baru = re.sub(r"\n{3,}", "\n\n", baru)

        if baru == isi and fm == pisah_front_matter(asli)[0]:
            return False

        # Perbaiki gambar sampul (front matter) bila menunjuk gambar luar/mati
        if fm:
            m = re.search(r'^image:\s*["\']?(.+?)["\']?\s*$', fm, re.M)
            if m:
                url_sampul = m.group(1).strip().strip('"\'')
                if not url_sampul.startswith("/images/uploads/"):
                    lokal = re.search(r'src="(/images/uploads/[^"]+)"', baru)
                    if lokal:
                        fm = fm[: m.start(1)] + lokal.group(1) + fm[m.end(1):]
                    else:
                        fm = re.sub(r'^image:.*\n', "", fm, flags=re.M)

        if not self.cek:
            path.write_text(fm + baru, encoding="utf-8")
        return True


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", default=".", help="folder situs Hugo")
    p.add_argument("--cek", action="store_true", help="hitung saja, tidak menulis")
    p.add_argument("--biarkan-mati", action="store_true",
                   help="gambar mati dibiarkan (tidak dibuang) meski tampil rusak")
    a = p.parse_args()

    root = Path(a.out).resolve()
    if not (root / "hugo.toml").exists():
        print(f"{root} bukan folder situs Hugo (hugo.toml tidak ada).")
        return 1

    perapi = Perapi(root, a.cek, hapus_mati=not a.biarkan_mati)
    berkas = sorted((root / "content").rglob("*.md"))
    diubah = 0
    for f in berkas:
        if f.name == "_index.md":
            continue
        if perapi.proses_berkas(f):
            diubah += 1
            if diubah % 50 == 0:
                print(f"  ... {diubah} berkas dirapikan")

    s = perapi.stat
    print(f"\nBerkas diperiksa : {len(berkas)}")
    print(f"Berkas diubah    : {diubah}")
    print(f"Gambar lokal     : {s['lokal']}")
    print(f"Gambar diunduh   : {s['diunduh']}")
    print(f"Gambar inline    : {s['inline']} (base64 dijadikan berkas)")
    print(f"Gambar mati      : {s['mati']} ({'dibuang' if not a.biarkan_mati else 'dibiarkan'})")
    print(f"Gambar pelacak   : {s['pelacak']} (dibuang)")
    print(f"Tautan diperbaiki: {s['tautan']}")
    print(f"Sisa embed dibuang: {s['embed']}")
    print(f"Wadah kosong dibuang: {s['wadah']}")

    if perapi.mati and not a.cek:
        lap = root / "_migrasi" / "gambar-luar.md"
        lap.parent.mkdir(parents=True, exist_ok=True)
        baris = ["# Gambar luar yang tidak bisa diselamatkan", "",
                 "Gambar-gambar ini menunjuk ke situs lain yang sudah mati "
                 "(atau memblokir unduhan), sehingga tidak bisa dipindahkan ke repo.",
                 "Tag gambarnya sudah dibuang dari artikel agar tidak muncul ikon rusak.",
                 "Bila foto tersebut penting, unggah ulang lewat panel admin.", "",
                 "| Alamat asli |", "| --- |"]
        baris += [f"| {u} |" for _, _, u in perapi.mati]
        lap.write_text("\n".join(baris) + "\n", encoding="utf-8")
        print(f"\nDaftar gambar mati: _migrasi/gambar-luar.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
