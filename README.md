# Situs DPD PKS Boyolali

Situs statis berbasis **Hugo**, tampilannya diadopsi dari tema WordPress DPP (`pksejahtera`), dengan panel admin
**Sveltia CMS** di `/admin/`. Konten berasal dari blog Blogger lama (807 artikel, 2011–2026) yang sudah dimigrasikan.

Dua panduan terpisah:

| Berkas | Untuk siapa | Isi |
|---|---|---|
| **[PANDUAN-PASANG.md](PANDUAN-PASANG.md)** | orang teknis | memasang dari nol: GitHub, Pages, domain `boyolali.pks.my.id`, token CMS |
| **[PANDUAN-PENGGUNAAN.md](PANDUAN-PENGGUNAAN.md)** | pengurus | menulis berita, banner, menu, halaman — tanpa istilah teknis |

---

## Menjalankan di komputer

**Cara termudah (Windows, tanpa memasang apa pun):** klik dua kali berkas berikut di folder ini.

| Berkas | Kegunaan |
|---|---|
| `Pratinjau.cmd` | Menyalakan server lokal, lalu membuka `http://localhost:1313` (situs, di peramban bawaan) dan `http://localhost:1313/admin/` (admin, **otomatis di Edge/Chrome**) |
| `Pratinjau-Draf.cmd` | Sama, tetapi artikel berstatus **draf** ikut ditampilkan |
| `Buka-Admin.cmd` | Hanya membuka halaman admin di Edge/Chrome saat server sudah menyala |

**Peramban untuk admin:** Sveltia CMS hanya berjalan di peramban berbasis Chromium — **Edge, Chrome, Brave, Opera**.
Firefox dan Zen (mesin Gecko) tidak didukung, halaman admin akan menolak atau berputar tanpa henti. Karena itu
`Pratinjau.cmd` membuka situs di peramban bawaan, tetapi halaman admin sengaja dilempar ke Edge/Chrome.

Berkas pustaka admin (`static/admin/sveltia-cms.js`, 2,6 MB) disimpan **lokal**, tidak lagi diambil dari CDN.
Ini membuat admin tetap terbuka walau internet lambat atau CDN terblokir — penyebab umum halaman berputar terus.


Hugo yang dipakai ada di `_tools\hugo.exe` (v0.169.0 extended), jadi tidak perlu memasang Hugo. Folder `_tools`
sudah masuk `.gitignore` supaya tidak ikut terunggah ke GitHub. Mematikan server: tutup jendela hitamnya atau tekan `Ctrl+C`.

Pratinjau pertama butuh ±30 detik karena membangun 900+ halaman; setelah itu setiap perubahan langsung terlihat.

Di halaman admin versi lokal, Sveltia menawarkan **“Work with Local Repository”**. Pilih folder `pks-boyolali` ini
untuk menelusuri collection, tabel artikel, dan formulir **tanpa login GitHub**. Perubahan yang disimpan di mode ini
langsung menulis ke berkas di disk (bisa dibatalkan dengan `git checkout -- .`), jadi untuk sekadar melihat-lihat
cukup sampai membuka formulir.

Bila ingin memakai perintah `hugo` dari terminal mana pun, pasang Hugo extended versi ≥ 0.145
(`winget install Hugo.Hugo.Extended`), lalu:

```bash
python scripts/pra_build.py     # alamat pendek artikel baru + halaman arsip
hugo server                     # buka http://localhost:1313
```

`pra_build.py` cukup dijalankan bila ada artikel baru. Di GitHub, langkah ini berjalan otomatis.

Untuk pratinjau yang mendekati hasil akhir (termasuk pencarian):

```bash
hugo --minify
npx pagefind --site public      # indeks pencarian; tanpa ini kotak cari kosong
```

---

## Struktur

| Lokasi | Isi |
|---|---|
| `hugo.toml` | Pengaturan teknis Hugo (alamat situs, alamat kategori, versi minimum) |
| `data/identitas.yaml` | Identitas, kontak, media sosial, tombol bagikan, panjang alamat artikel (**bisa diedit lewat admin**) |
| `data/menu.yaml` | Menu header |
| `data/beranda.yaml` | Banner slider dan susunan beranda |
| `data/kunjungi.yaml` | Gambar "Kunjungi Juga" di sidebar |
| `data/wilayah.yaml` | 22 kecamatan + 267 desa/kelurahan Kabupaten Boyolali, untuk dropdown bertingkat pada formulir |
| `content/posts/` | Artikel (807 berkas hasil migrasi) |
| `content/pages/` | Halaman statis (Profil Fraksi, Profil Pengurus, Aspirasi, Gabung PKS). Data anggota fraksi dan susunan pengurus disimpan di front matter masing-masing berkas, bukan di `data/` |
| `content/berita/`, `content/inspirasi/` | Halaman gabungan "Semua Berita" dan "Semua Inspirasi" |
| `content/categories/` | Judul kategori dan pengalihan dari alamat label lama |
| `content/arsip/` | Arsip tahun/bulan, **dibuat otomatis** (jangan diedit) |
| `layouts/` | Templat halaman |
| `static/assets/`, `static/images/` | CSS, JavaScript, logo, gambar |
| `static/assets/zoom.js` | Efek zoom gambar artikel: klik gambar → membesar mengapung, klik di luar atau `Esc` menutup. Pustaka `medium-zoom` ada di `static/assets/vendor/` |
| `static/assets/form.js` | Dropdown desa/kelurahan mengikuti kecamatan, lalu mengirim formulir ke Apps Script |
| `layouts/partials/formulir.html` | Formulir Aspirasi dan Gabung PKS (satu partial, dibedakan lewat `jenis`) |
| `static/admin/config.yml` | Pengaturan admin CMS |
| `scripts/` | Skrip bantu (lihat tabel di bawah) |
| `.github/workflows/hugo.yml` | Publikasi otomatis ke GitHub Pages |
| `_migrasi/` | Laporan migrasi Blogger dan arsip komentar lama |

### Skrip bantu

| Skrip | Kegunaan |
|---|---|
| `scripts/pra_build.py` | Memberi alamat pendek artikel baru, membuat halaman arsip tahun/bulan. Dijalankan otomatis saat publikasi. |
| `scripts/migrasi_blogger.py` | Mengubah `feed.atom` hasil Google Takeout menjadi artikel Hugo. Sekali pakai (sudah dijalankan). |
| `scripts/rapikan_gambar_luar.py` | Menyelamatkan gambar dari situs lain, membuang sisa kode pelacak. Sekali pakai (sudah dijalankan). |
| `scripts/optimalkan_gambar.py` | Memperkecil gambar di `static/images/uploads/` (lebar maks 1400 px). Bisa dijalankan kapan saja. |
| `scripts/formulir-apps-script.gs` | Kode Google Apps Script penampung kiriman formulir → dua berkas Sheets. Bukan bagian build Hugo; ditempel manual di script.google.com. Cara pasang: `PANDUAN-PASANG.md` bagian 10. |

---

## Hasil migrasi

| Hal | Jumlah |
|---|---|
| Artikel | 807 (2011–2026) |
| Komentar lama | 19 (diarsipkan di `_migrasi/komentar.yaml`, tidak ditampilkan) |
| Gambar | ±790 berkas, 85 MB setelah diperkecil |
| Alamat lama | Dipertahankan lewat `url:` di front matter, mis. `/2014/01/judul.html` |

Catatan penting: **jangan menghapus field `url:`** pada artikel hasil migrasi. Field itu yang menjaga alamat lama
tetap hidup. Di panel admin field ini disembunyikan (`widget: hidden`) tetapi tetap ikut tersimpan.

Rincian per artikel ada di `_migrasi/laporan.md`.

---

## Pengaturan dasar (identitas)

Semua pengaturan dasar ada di `data/identitas.yaml`, dan bisa diubah di admin lewat menu **Identitas situs**:
nama situs, jenis dan wilayah (judul header dibuat otomatis), kontak di footer, media sosial, tombol bagikan, dan panjang
alamat artikel baru. Untuk DPW/DPD lain cukup mengganti isi berkas ini.

Halaman daftar kategori (`/kategori/`) dan daftar tag (`/tag/`) sengaja tidak ditampilkan di menu maupun footer, tetapi tetap
bisa dibuka lewat alamat. Untuk menampilkannya, tambahkan menu dengan alamat `/kategori/` atau `/tag/` di admin (Header & Menu).

---

## Versi Hugo & Sveltia CMS

Situs ini membutuhkan Hugo **0.169.0 atau lebih baru** (standar maupun extended). Versi minimum dikunci di `hugo.toml`,
jadi Hugo yang terlalu lama akan menampilkan pesan yang jelas. GitHub Actions memakai versi tetap `0.169.0`
(`HUGO_VERSION` di `.github/workflows/hugo.yml`). Sebaiknya Hugo di komputer sama atau sedikit lebih baru.

```bash
hugo version                      # cek versi
winget install Hugo.Hugo.Extended # Windows
brew install hugo                 # macOS
```

Menaikkan versi: ubah `HUGO_VERSION` di workflow dan `min` di `hugo.toml` bersamaan, setelah dicoba di komputer.

> Sejak Hugo 0.145, kunci front matter `_build` diganti `build:`. Skrip `pra_build.py` sudah memakai bentuk baru.

**Sveltia CMS** dimuat dari CDN dengan versi yang ditulis langsung di `static/admin/index.html`
(saat ini `@sveltia/cms@0.256.1`). Cara cek versi terbaru:

```bash
curl -s https://registry.npmjs.org/@sveltia/cms/latest | grep -o '"version":"[^"]*"'
```

Atau buka https://www.npmjs.com/package/@sveltia/cms dan lihat nomor versi di kanan atas. Untuk menaikkan:
ganti angka versi pada `src` di `static/admin/index.html`, buka `/admin/`, lalu pastikan daftar koleksi
dan formulir artikel masih tampil normal (bila konfigurasi tidak cocok, CMS menampilkan pesan kesalahan
di halaman masuk).

---

## Alamat situs

| Jenis | Bentuk |
|---|---|
| Artikel lama | Sesuai alamat aslinya, mis. `/2014/01/judul.html` |
| Artikel baru | `/2026/10/judul-singkat/` |
| Kategori | `/kategori/seputar-pks/`, daftar semua: `/kategori/` |
| Tag | `/tag/nama-tag/`, daftar semua: `/tag/` |
| Arsip | `/2014/` dan `/2014/01/` |
| Halaman berikutnya | `/kategori/seputar-pks/halaman/2/` |
| Pencarian | `/cari/` |
| Admin | `/admin/` |

---

## Publikasi

Setiap `git push` ke cabang `main` (atau penyimpanan lewat admin CMS) memicu GitHub Actions: membuat alamat pendek dan
arsip, membangun situs, membuat indeks pencarian (Pagefind), lalu mempublikasikannya.

Pengaturan awal yang wajib:
1. **Settings → Actions → General → Workflow permissions** → **Read and write permissions** (dipakai untuk menyimpan
   `slug:` dan halaman arsip kembali ke repo).
2. **Settings → Pages → Source: GitHub Actions**.
3. **Settings → Pages → Custom domain**: `boyolali.pks.my.id`, lalu pasang catatan CNAME di DNS.
   Berkas CNAME di repositori tidak dipakai karena situs terbit lewat GitHub Actions.
