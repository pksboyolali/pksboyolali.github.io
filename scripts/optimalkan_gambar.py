#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memperkecil gambar di static/images/uploads/ tanpa mengubah nama berkas.

Kenapa perlu:
  Hasil unduhan dari Blogger masih berukuran asli (sering 1600 px ke atas,
  rata-rata ±200 KB). Untuk situs berita, lebar 1400 px sudah lebih dari cukup
  (kolom artikel hanya ±750 px di layar besar). Tanpa langkah ini, repo GitHub
  membengkak dan halaman terasa lambat dibuka di jaringan seluler.

Yang dilakukan:
  - Gambar yang lebih lebar dari --lebar diperkecil (rasio tetap).
  - JPEG disimpan ulang dengan mutu 82 dan mode progressive.
  - PNG disimpan ulang dengan kompresi maksimal (transparansi tetap aman).
  - Nama berkas TIDAK diubah, jadi tidak ada tautan di artikel yang rusak.
  - Gambar yang tidak menghasilkan penghematan berarti dibiarkan apa adanya.

Cara pakai (dari folder situs):
    python scripts/optimalkan_gambar.py --cek      # lihat perkiraan penghematan
    python scripts/optimalkan_gambar.py            # jalankan
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path

from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None          # gambar besar dari kamera tetap diproses
EKSTENSI = {".jpg", ".jpeg", ".png", ".webp"}


def ukuran_manusia(n: int) -> str:
    for satuan in ("B", "KB", "MB", "GB"):
        if n < 1024 or satuan == "GB":
            return f"{n:.1f} {satuan}" if satuan != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} GB"


def optimalkan(path: Path, lebar_maks: int, mutu: int, cek: bool) -> tuple[int, int]:
    """Kembalikan (ukuran sebelum, ukuran sesudah). Sesudah=0 bila gagal dibaca."""
    asli_bytes = path.read_bytes()
    sebelum = len(asli_bytes)
    try:
        with Image.open(io.BytesIO(asli_bytes)) as im:
            im = ImageOps.exif_transpose(im)          # foto ponsel jangan miring
            skala = min(1.0, lebar_maks / im.width) if im.width else 1.0
            if skala < 1.0:
                im = im.resize((round(im.width * skala), round(im.height * skala)),
                               Image.LANCZOS)

            ext = path.suffix.lower()
            if ext in (".jpg", ".jpeg"):
                if im.mode not in ("RGB", "L"):
                    im = im.convert("RGB")
                opsi = dict(format="JPEG", quality=mutu, optimize=True, progressive=True)
            elif ext == ".png":
                opsi = dict(format="PNG", optimize=True, compress_level=9)
            else:
                opsi = dict(format="WEBP", quality=mutu, method=4)

            buf = io.BytesIO()
            im.save(buf, **opsi)
            hasil = buf.getvalue()
    except (OSError, ValueError):
        return sebelum, 0                            # berkas rusak / bukan gambar

    # Hanya pakai hasil baru bila benar-benar lebih kecil (minimal 3%)
    if len(hasil) < sebelum * 0.97:
        if not cek:
            path.write_bytes(hasil)
        return sebelum, len(hasil)
    return sebelum, sebelum


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--folder", default="static/images/uploads", help="folder gambar")
    p.add_argument("--lebar", type=int, default=1400, help="lebar maksimum (px)")
    p.add_argument("--mutu", type=int, default=82, help="mutu JPEG/WEBP (1-95)")
    p.add_argument("--cek", action="store_true", help="hitung saja, tidak menulis")
    a = p.parse_args()

    folder = Path(a.folder)
    if not folder.is_dir():
        print(f"Folder tidak ditemukan: {folder}\nJalankan dari folder situs.")
        return 1

    berkas = sorted(f for f in folder.rglob("*") if f.suffix.lower() in EKSTENSI)
    total_awal = total_akhir = 0
    diubah = 0
    print(f"{len(berkas)} gambar diperiksa (lebar maks {a.lebar}px, mutu {a.mutu})"
          + ("  [MODE CEK]" if a.cek else ""))

    for i, f in enumerate(berkas, 1):
        awal, akhir = optimalkan(f, a.lebar, a.mutu, a.cek)
        total_awal += awal
        total_akhir += akhir or awal
        if akhir and akhir < awal:
            diubah += 1
        if i % 100 == 0:
            print(f"  ... {i}/{len(berkas)}")

    hemat = total_awal - total_akhir
    print(f"\nGambar diperkecil : {diubah}")
    print(f"Ukuran sebelum    : {ukuran_manusia(total_awal)}")
    print(f"Ukuran sesudah    : {ukuran_manusia(total_akhir)}")
    if total_awal:
        print(f"Hemat             : {ukuran_manusia(hemat)} "
              f"({hemat / total_awal * 100:.0f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
