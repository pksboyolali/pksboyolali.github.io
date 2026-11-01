#!/usr/bin/env python3
"""
Persiapan sebelum situs dibangun. Dijalankan otomatis oleh GitHub (lihat .github/workflows/hugo.yml)
dan bisa dijalankan sendiri di komputer sebelum `hugo server`:

    python scripts/pra_build.py          (Windows: python scripts\\pra_build.py)

Tugasnya:
 1. Memberi "alamat pendek" (slug:) pada artikel BARU yang belum punya, dari judulnya.
    Dipotong di batas kata (maks_kata, maks_huruf di data/identitas.yaml > alamat_artikel).
    Artikel yang sudah punya url: atau slug: tidak disentuh, jadi alamat lama tidak berubah.
 2. Membuat halaman arsip tahun (/2026/) dan bulan (/2025/10/) di content/arsip/,
    hanya untuk periode yang punya artikel. Halaman yang tidak lagi diperlukan dihapus.

Opsi: --cek  hanya menampilkan apa yang akan diubah, tanpa menulis berkas.
"""
import json, os, re, sys, tomllib, unicodedata
from datetime import datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))
BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus",
         "September", "Oktober", "November", "Desember"]
FM = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)


# ---------- bantu ----------
def baca_konfigurasi(root):
    """Batas alamat: data/identitas.yaml (alamat_artikel), cadangan hugo.toml, lalu bawaan 8 kata / 70 huruf."""
    maks_kata, maks_huruf = 8, 70
    try:
        with open(os.path.join(root, "data", "identitas.yaml"), encoding="utf-8") as f:
            y = f.read()
        k = re.search(r"^[ \t]+maks_kata[ \t]*:[ \t]*(\d+)", y, re.M)
        h = re.search(r"^[ \t]+maks_huruf[ \t]*:[ \t]*(\d+)", y, re.M)
        if k: maks_kata = int(k.group(1))
        if h: maks_huruf = int(h.group(1))
    except FileNotFoundError:
        try:
            with open(os.path.join(root, "hugo.toml"), "rb") as f:
                a = tomllib.load(f).get("params", {}).get("alamat_artikel", {})
            maks_kata, maks_huruf = int(a.get("maks_kata", maks_kata)), int(a.get("maks_huruf", maks_huruf))
        except Exception:
            pass
    return max(1, maks_kata), max(10, maks_huruf)


def nilai(fm, kunci):
    """Ambil nilai satu baris 'kunci: nilai' di front matter (tanpa memerlukan PyYAML)."""
    m = re.search(r"^" + re.escape(kunci) + r"[ \t]*:[ \t]*(.*?)[ \t]*$", fm, re.M)
    if not m:
        return ""
    v = m.group(1)
    if v.startswith('"'):
        try:
            return json.loads(v)
        except Exception:
            return v.strip('"')
    if v.startswith("'"):
        return v.strip("'").replace("''", "'")
    return v


def baca_tanggal(s):
    s = (s or "").strip().strip("'\"")
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00").replace(" ", "T", 1))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=WIB)
    return d.astimezone(WIB)


def slug_pendek(judul, maks_kata, maks_huruf):
    t = unicodedata.normalize("NFKD", judul).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"['\u2019`\"]", "", t)
    kata = [k for k in re.split(r"[^a-z0-9]+", t) if k]
    kata = kata[:maks_kata]
    while len("-".join(kata)) > maks_huruf and len(kata) > 1:
        kata.pop()                       # buang kata terakhir, bukan memotong di tengah kata
    s = "-".join(kata)
    return s[:maks_huruf].strip("-")


def tulis(path, isi, cek):
    try:
        with open(path, encoding="utf-8", newline="") as f:
            if f.read() == isi:
                return False
    except FileNotFoundError:
        pass
    if not cek:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(isi)
    return True


# ---------- proses ----------
def kumpulkan(root):
    posts = []
    for dp, _, fs in os.walk(os.path.join(root, "content", "posts")):
        for fn in fs:
            if not fn.endswith(".md") or fn.startswith("_index"):
                continue
            path = os.path.join(dp, fn)
            with open(path, encoding="utf-8", newline="") as f:
                teks = f.read()
            m = FM.match(teks)
            if not m:
                continue
            fm = m.group(1)
            posts.append({"path": path, "teks": teks, "fm": fm, "m": m,
                          "judul": nilai(fm, "title"), "tgl": baca_tanggal(nilai(fm, "date")),
                          "url": nilai(fm, "url"), "slug": nilai(fm, "slug"),
                          "draft": nilai(fm, "draft").lower() == "true"})
    return posts


def beri_alamat(posts, maks_kata, maks_huruf, cek):
    dipakai = {}
    for p in posts:                      # alamat yang sudah ada, per bulan
        if p["tgl"] is None:
            continue
        kunci = (p["tgl"].year, p["tgl"].month)
        nama = p["slug"] or os.path.splitext(os.path.basename(p["url"].rstrip("/")))[0]
        if nama:
            dipakai.setdefault(kunci, set()).add(nama)
    diubah = 0
    for p in sorted(posts, key=lambda x: (x["tgl"] or datetime.min.replace(tzinfo=WIB))):
        if p["url"] or p["slug"] or not p["judul"]:
            continue
        kunci = (p["tgl"].year, p["tgl"].month) if p["tgl"] else (0, 0)
        s = slug_pendek(p["judul"], maks_kata, maks_huruf) or "artikel"
        asli, n = s, 2
        while s in dipakai.setdefault(kunci, set()):
            s = f"{asli}-{n}"; n += 1
        dipakai[kunci].add(s)
        fm = p["fm"]
        nl = "\r\n" if "\r\n" in p["teks"][:200] else "\n"
        sisip = f"slug: {s}"
        kosong = re.search(r"^slug[ \t]*:[ \t]*(?:\"\"|'')?[ \t]*$", fm, re.M)   # "slug:" kosong dari CMS: ganti, jangan ganda
        baris = re.search(r"^title[ \t]*:.*$", fm, re.M)
        if kosong:
            fm_baru = fm[:kosong.start()] + sisip + fm[kosong.end():]
        elif baris:
            fm_baru = fm[:baris.end()] + nl + sisip + fm[baris.end():]
        else:
            fm_baru = fm + nl + sisip
        isi = p["teks"][:p["m"].start(1)] + fm_baru + p["teks"][p["m"].end(1):]
        if tulis(p["path"], isi, cek):
            diubah += 1
            print(f"  alamat: {os.path.relpath(p['path'])}  ->  {s}")
    return diubah


def buat_arsip(root, posts, cek):
    periode = {}
    for p in posts:
        if p["draft"] or p["tgl"] is None:
            continue
        periode[(p["tgl"].year, p["tgl"].month)] = periode.get((p["tgl"].year, p["tgl"].month), 0) + 1
    isi = {}
    judul_tahun = {}
    for (y, m), n in periode.items():
        judul_tahun[y] = judul_tahun.get(y, 0) + n
    cat = "# Dibuat otomatis oleh scripts/pra_build.py. Jangan diedit; akan ditimpa.\n"
    dasar = "layout: \"arsip\"\noutputs: [\"HTML\"]\nsitemap:\n  disable: true\n"
    isi["content/arsip/_index.md"] = f"---\n{cat}title: \"Arsip\"\nbuild:\n  render: never\n  list: never\n---\n"
    for y in sorted(judul_tahun):
        isi[f"content/arsip/{y}/_index.md"] = f"---\n{cat}title: \"Arsip {y}\"\nurl: \"/{y}/\"\ntahun: {y}\n{dasar}---\n"
    for (y, m) in sorted(periode):
        isi[f"content/arsip/{y}/{m:02d}/_index.md"] = (
            f"---\n{cat}title: \"Arsip {BULAN[m]} {y}\"\nurl: \"/{y}/{m:02d}/\"\ntahun: {y}\nbulan: {m}\n{dasar}---\n")
    ubah = 0
    for rel, teks in isi.items():
        if tulis(os.path.join(root, *rel.split("/")), teks, cek):
            ubah += 1
    # hapus halaman arsip yang tidak diperlukan lagi
    hapus = 0
    ada = {os.path.normpath(os.path.join(root, *r.split("/"))) for r in isi}
    for dp, _, fs in os.walk(os.path.join(root, "content", "arsip")):
        for fn in fs:
            p = os.path.normpath(os.path.join(dp, fn))
            if p not in ada:
                hapus += 1
                if not cek:
                    os.remove(p)
    if not cek:                          # rapikan folder kosong
        for dp, ds, fs in sorted(os.walk(os.path.join(root, "content", "arsip")), reverse=True):
            if not os.listdir(dp):
                os.rmdir(dp)
    print(f"  arsip: {len(judul_tahun)} tahun, {len(periode)} bulan | berkas diubah: {ubah}, dihapus: {hapus}")
    return ubah + hapus


def main():
    cek = "--cek" in sys.argv
    root = os.getcwd()
    if not os.path.exists(os.path.join(root, "hugo.toml")):
        sys.exit("Jalankan dari folder situs (yang berisi hugo.toml).")
    maks_kata, maks_huruf = baca_konfigurasi(root)
    posts = kumpulkan(root)
    print(f"Artikel ditemukan: {len(posts)} (alamat: maks {maks_kata} kata / {maks_huruf} huruf)" + ("  [MODE CEK]" if cek else ""))
    a = beri_alamat(posts, maks_kata, maks_huruf, cek)
    posts = kumpulkan(root) if not cek and a else posts
    b = buat_arsip(root, posts, cek)
    print("Selesai." if (a or b) else "Selesai, tidak ada yang perlu diubah.")


if __name__ == "__main__":
    main()
