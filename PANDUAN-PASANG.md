# Panduan Pemasangan — Situs DPD PKS Boyolali

Panduan ini untuk **orang teknis** yang memasang situs dari nol sampai tayang di
`https://boyolali.pks.my.id`. Tidak perlu bisa menulis kode; cukup mengikuti langkah
berurutan dan menyalin-tempel.

Panduan untuk pengurus yang **menulis berita** ada di berkas terpisah:
[`PANDUAN-PENGGUNAAN.md`](PANDUAN-PENGGUNAAN.md).

---

## 0. Gambaran sistem

| Bagian | Keterangan |
|---|---|
| Hugo | Pembuat situs statis. Mengubah berkas Markdown menjadi HTML. |
| Sveltia CMS | Panel admin di `/admin/` untuk menulis berita lewat browser. Menyimpan langsung ke GitHub. |
| GitHub | Tempat menyimpan berkas situs (repositori) sekaligus mesin publikasinya. |
| GitHub Pages | Tempat situs ditayangkan. **Gratis**, tanpa server, tanpa tagihan bulanan. |
| Domain | `boyolali.pks.my.id`, diarahkan ke GitHub Pages lewat DNS. |

Alur kerja setelah terpasang:

```
Pengurus menulis di /admin/  ->  tersimpan sebagai berkas di GitHub
                             ->  GitHub Actions membangun situs (2-3 menit)
                             ->  tayang di boyolali.pks.my.id
```

**Biaya:** Rp0. Yang diperlukan hanya akun GitHub gratis dan domain `pks.id`
yang sudah ada.

---

## 1. Yang perlu disiapkan

1. **Akun GitHub** (gratis) — daftar di https://github.com/signup.
2. **Git** (opsional, hanya bila mengunggah lewat komputer) — https://git-scm.com/downloads.
   Cara termudah: unggah lewat halaman web GitHub, tanpa memasang apa pun.
3. **Hugo** (opsional, hanya untuk mencoba di komputer) — lihat bagian 9.
4. **Akses ke pengaturan DNS `pks.id`** — biasanya dipegang pengurus DPP.
   Tanpa ini situs tetap tayang, hanya alamatnya masih `username.github.io`.

---

## 2. Membuat repositori

1. Masuk ke GitHub, klik **+** di kanan atas → **New repository**.
2. Isi:
   - **Repository name:** `pksboyolali.github.io` — **harus persis ini** bila akun
     GitHub-nya bernama `pksboyolali`. Nama berakhiran `.github.io` membuat GitHub
     menempatkan situs di **akar** (`https://pksboyolali.github.io/`), bukan di
     subfolder. Ini bukan sekadar kerapian: panel admin menyusun alamat gambar
     tanpa menyertakan subfolder, sehingga situs di subfolder membuat pratinjau
     gambar di admin patah. Bila akunnya bernama lain, pakai pola
     `NAMA-AKUN.github.io`.
   - **Visibility:** **Public** — GitHub Pages gratis hanya untuk repositori publik.
   - **Jangan** centang "Add a README file" (kita sudah punya).
3. Klik **Create repository**.

---

## 3. Mengunggah berkas situs

### Cara A — lewat halaman web (tanpa memasang apa pun)

1. Di halaman repositori yang masih kosong, klik **uploading an existing file**.
2. Buka folder situs di komputer, **pilih semua isi folder** (bukan foldernya),
   lalu seret ke jendela browser.
   - Di Windows: masuk ke folder, tekan `Ctrl+A`, seret.
   - Pastikan folder `.github`, `content`, `layouts`, `static`, `data`, `scripts`
     ikut terunggah. Folder tersembunyi (diawali titik) kadang tidak terlihat —
     aktifkan "Hidden items" di Windows Explorer.
3. Tulis pesan commit: `Versi awal situs`, klik **Commit changes**.
4. Tunggu hingga semua berkas selesai diunggah (bisa beberapa menit karena ada
   ±800 gambar).

### Cara B — lewat Git (lebih rapi untuk pembaruan berikutnya)

```bash
cd folder-situs
git init
git add .
git commit -m "Versi awal situs"
git branch -M main
git remote add origin https://github.com/pksboyolali/pksboyolali.github.io.git
git push -u origin main
```

> Bila akun GitHub-nya bukan `pksboyolali`, sesuaikan dua bagian alamat itu.

---

## 4. Mengizinkan GitHub membangun situs

Ada dua pengaturan yang **wajib**, kalau terlewat situs tidak akan tayang.

### 4a. Izin tulis untuk workflow

Situs ini punya langkah otomatis yang menulis kembali ke repositori (memberi
alamat pendek artikel baru dan membuat halaman arsip). Tanpa izin ini, proses
gagal di tengah.

1. Buka repositori → **Settings** → **Actions** → **General**.
2. Gulir ke **Workflow permissions**.
3. Pilih **Read and write permissions** → **Save**.

### 4b. Sumber GitHub Pages

1. Masih di **Settings** → **Pages**.
2. Bagian **Build and deployment** → **Source**: pilih **GitHub Actions**
   (bukan "Deploy from a branch").
3. Tidak perlu memilih tema; situs sudah punya tampilan sendiri.

**Tanda pengaturan ini sudah benar:** di tab **Actions** hanya ada satu proses
per publikasi, yaitu **Publikasi situs**. Bila muncul juga proses bernama
**pages build and deployment**, artinya sumber Pages masih "Deploy from a
branch" — proses itu akan menimpa hasil build Hugo beberapa detik setelah
publikasi selesai. Rinciannya di bagian 12.

### 4c. Jalankan publikasi pertama

1. Buka tab **Actions**.
2. Bila muncul tombol **I understand my workflows, go ahead and enable them**, klik.
3. Klik workflow **Publikasi situs** di kiri → tombol **Run workflow** → **Run workflow**.
4. Tunggu 3–5 menit. Tanda centang hijau berarti berhasil.

Setelah selesai, situs bisa dibuka di `https://pksboyolali.github.io/`
(alamat sementara). Alamat ini akan diganti domain sendiri pada langkah 5.

---

## 5. Memasang domain sendiri

Rencana domain situs ini berjalan dua tahap:

| Tahap | Domain | Keterangan |
|---|---|---|
| Sekarang | `boyolali.pks.my.id` | domain yang sudah dipegang sendiri |
| Menyusul | `boyolali.pks.id` | setelah disetujui DPP; lihat bagian 5e |

**Batas penting:** GitHub Pages hanya bisa memasang **satu domain utama** per
situs. Jadi `boyolali.pks.id` nanti **tidak bisa** ditambahkan begitu saja di
samping yang lama — perlu salah satu cara di bagian 5e.

### 5a. Berkas CNAME tidak dipakai lagi

Karena situs ini terbit lewat workflow **GitHub Actions**, GitHub **mengabaikan**
berkas CNAME. Domain sepenuhnya diatur di **Settings → Pages**. Berkas
`CNAME.nanti` di akar repositori kini hanya catatan; boleh dibiarkan, boleh
dihapus, tidak berpengaruh ke situs.

### 5b. Pengaturan DNS

`boyolali.pks.my.id` adalah subdomain, jadi cukup **satu catatan CNAME**. Di
panel DNS `pks.my.id` tambahkan:

| Jenis | Nama/Host | Nilai/Tujuan | TTL |
|---|---|---|---|
| CNAME | `boyolali` | `pksboyolali.github.io` | 3600 (atau bawaan) |

> `pksboyolali.github.io` adalah alamat akun, **bukan** alamat repositori.
> Contoh: akun `pksboyolali` → `pksboyolali.github.io`.

Bila penyedia DNS meminta titik di akhir, tulis `pksboyolali.github.io.` — keduanya benar.
Jangan memakai catatan `A` untuk subdomain, dan jangan memakai wildcard `*.pks.my.id`.

### 5c. Daftarkan domain di GitHub

Kerjakan **berdekatan** dengan 5b: daftarkan dulu, lalu segera pasang DNS.

1. **Settings** → **Pages** → **Custom domain**.
2. Isi `boyolali.pks.my.id` → **Save**.
3. Tunggu pemeriksaan DNS (bisa 10 menit sampai 24 jam; biasanya di bawah 1 jam).
4. Setelah muncul tulisan "DNS check successful", centang **Enforce HTTPS**.
   Sertifikat HTTPS dibuat otomatis dan gratis, butuh beberapa menit.

> Selama DNS belum benar, alamat `https://pksboyolali.github.io/` sudah
> dialihkan ke domain baru. Jadi situs bisa tampak mati untuk sementara —
> itu wajar, bukan build yang gagal.

### 5d. Bila memakai `www`

Tidak perlu. Situs ini memakai subdomain langsung tanpa `www`.

### 5e. Nanti: memakai dua domain sekaligus

Ada tiga pilihan. Semuanya butuh kendali atas DNS domain yang bersangkutan.

| Cara | Hasil | Kebutuhan |
|---|---|---|
| **A. Alihkan (301)** domain lama ke baru | Pengunjung domain lama otomatis pindah ke domain baru. Alamat di bilah peramban berubah. | DNS domain lama bisa membuat aturan redirect (Cloudflare Redirect Rules, atau fitur "URL forwarding" di penyedia domain) |
| **B. Cloudflare Worker** di depan domain kedua | **Kedua domain benar-benar hidup**, isi sama, alamat tetap masing-masing. | Domain kedua dikelola lewat Cloudflare (gratis, batas 100.000 permintaan/hari) |
| **C. Tukar domain utama** | Domain baru jadi utama; domain lama dialihkan (butuh cara A juga) | Sama seperti A |

Yang **tidak bisa**: menaruh dua nilai di `CNAME` atau menambah dua domain di
Settings → Pages. Catatan CNAME `boyolali.pks.id` yang menunjuk ke
`pksboyolali.github.io` akan menghasilkan halaman 404 dari GitHub, karena
domain itu tidak terdaftar sebagai domain situs.

**Saran:** pakai cara A. Untuk pengunjung hasilnya sama saja — tetap sampai ke
situs yang sama, hanya alamatnya menyesuaikan. Cara B baru dipakai bila DPP
memang ingin `boyolali.pks.id` tampil apa adanya di bilah alamat.

Saat memilih domain baru sebagai utama, jangan lupa menyesuaikan tiga tempat:
`hugo.toml` (`baseURL`), `static/admin/config.yml` (`site_url` dan `display_url`),
lalu **Settings → Pages → Custom domain**.

---

## 6. Menyiapkan panel admin (CMS)

### 6a. Nama repositori di pengaturan CMS

Isian `repo:` di `static/admin/config.yml` sudah berisi
`pksboyolali/pksboyolali.github.io`, jadi **tidak perlu diubah** selama situs
memakai akun GitHub itu.

Bila kelak repositori dipindah ke akun lain, ubah baris itu beserta `site_url`
dan `display_url` tepat di bawahnya — ketiganya harus menunjuk ke alamat yang
sama, karena Sveltia memakai `site_url` untuk menyusun alamat gambar media.

### 6b. Masuk pertama kali

Situs ini memakai cara masuk **token GitHub** — tidak perlu server OAuth, tidak
perlu layanan pihak ketiga, jadi tetap gratis.

1. Buka `https://pksboyolali.github.io/admin/` (atau `https://boyolali.pks.my.id/admin/`
   bila domain sudah aktif).
2. Klik **Sign In with Token**.
3. Akan muncul jendela berisi tautan ke halaman pembuatan token GitHub dengan
   izin yang sudah terpilih. Buka tautan itu.
4. Di GitHub:
   - **Token name:** `CMS Situs PKS Boyolali`
   - **Expiration:** pilih `90 days` atau `No expiration`
   - **Repository access:** **Only select repositories** → pilih repo situs.
   - **Permissions:** `Contents` → **Read and write**
     (tambahkan `Pull requests` → Read and write bila memakai alur editorial).
   - Klik **Generate token**, lalu **salin** token yang muncul (hanya tampil sekali).
5. Kembali ke jendela CMS, tempel token, klik **Sign In**.

Token tersimpan di browser yang dipakai. Bila berganti komputer atau menghapus
data browser, ulangi langkah 3–5 (token lama masih bisa dipakai).

> **Keamanan:** token ini setara kata sandi repo. Jangan dibagikan di grup
> WhatsApp. Bila bocor, buka GitHub → Settings → Developer settings →
> Personal access tokens → **Revoke**, lalu buat token baru.

### 6c. Memberi akses ke pengurus lain

Ada dua pilihan:

| Cara | Kelebihan | Kekurangan |
|---|---|---|
| **Bagikan satu token** (paling mudah) | Pengurus tidak perlu punya akun GitHub | Jejak perubahan tercatat atas nama pemilik token; sulit dicabut per orang |
| **Undang sebagai collaborator** (disarankan) | Setiap orang punya token sendiri, bisa dicabut sendiri | Perlu akun GitHub dan undangan |

Untuk cara kedua: **Settings** → **Collaborators** → **Add people** → masukkan
akun GitHub pengurus → pilih peran **Write**. Setelah menerima undangan, orang
tersebut membuat token sendiri seperti langkah 6b.

### 6d. Kenapa "Sign in with GitHub" tidak dipakai

Di halaman masuk admin ada dua pilihan: **token** dan **akun GitHub**. Yang
dipakai hanya **token**.

**Sebabnya:** tanpa server OAuth sendiri, Sveltia memakai layanan OAuth milik
Netlify (`api.netlify.com/auth`). Layanan itu hanya bekerja untuk situs yang
terdaftar di Netlify. Untuk situs GitHub Pages, alamat itu menjawab **404 Not
Found**, sehingga tombolnya berujung pada halaman kosong atau pesan galat.

Karena itu `static/admin/config.yml` memuat baris:

```yaml
auth_methods: [token]
```

Baris ini menyembunyikan tombol GitHub supaya tidak ada yang menekan tombol
yang sudah pasti gagal. Token tetap tersedia dan itulah cara masuk yang resmi.

Tombol **Work with Local Repository** tidak perlu dimatikan: Sveltia hanya
menampilkannya bila alamat situs dibuka dari `localhost` atau `127.0.0.1`
(pratinjau lokal). Di situs online tombol itu tidak pernah muncul — sudah
diperiksa langsung di `pksboyolali.github.io/admin/`.

**Bila suatu saat ingin tombol GitHub hidup lagi**, ada dua jalan:

| Jalan | Yang perlu disiapkan | Kerumitan |
|---|---|---|
| **Sveltia CMS Authenticator di Cloudflare Workers** (disarankan) | Deploy worker dari `github.com/sveltia/sveltia-cms-auth`, buat GitHub OAuth App (callback: `https://NAMA-WORKER.workers.dev/callback`), isi `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `ALLOWED_DOMAINS=boyolali.pks.my.id` | Sedang — perlu akun Cloudflare gratis |
| **Netlify sebagai penyedia OAuth** | Buat situs Netlify kosong, pasang OAuth App GitHub dengan callback `https://api.netlify.com/auth/done`, isi Client ID/Secret di Netlify, lalu tambahkan `site_domain: boyolali.pks.my.id` | Ringan — tanpa kode, tapi bergantung layanan pihak ketiga |

Setelah salah satu jalan siap, tambahkan `base_url:` (jalan pertama) atau
`site_domain:` (jalan kedua) pada blok `backend:` di `config.yml`, lalu **hapus**
baris `auth_methods: [token]`.

---

## 7. Daftar periksa setelah tayang

Buka `https://boyolali.pks.my.id` dan periksa:

- [ ] Beranda tampil dengan susunan berita (Sorotan, 2 kolom, 3 kolom).
- [ ] Menu header dan dropdown berfungsi, termasuk di ponsel (tombol garis tiga).
- [ ] Klik salah satu berita → halaman artikel terbuka, gambar dan isi tampil.
- [ ] Artikel lama tetap di alamat aslinya, contoh:
      `https://boyolali.pks.my.id/2015/10/judul-artikel.html`
- [ ] Arsip tahun/bulan: `https://boyolali.pks.my.id/2015/10/`
- [ ] Kategori: `https://boyolali.pks.my.id/kategori/seputar-pks/`
- [ ] Pencarian (ikon kaca pembesar) mengembalikan hasil.
- [ ] Halaman statis: `/profil-fraksi/`, `/profil-pengurus/`, `/aspirasi/`, `/gabung/`.
- [ ] Formulir Aspirasi dan Gabung PKS terkirim dan barisnya masuk ke Sheets
      (lihat bagian 10).
- [ ] Footer menampilkan alamat, telepon, email, dan ikon media sosial.
- [ ] `/admin/` bisa dibuka dan bisa masuk.
- [ ] Alamat `http://` otomatis dialihkan ke `https://`.

---

## 8. Perawatan rutin

| Keperluan | Cara |
|---|---|
| Menulis berita | Lewat `/admin/` (lihat PANDUAN-PENGGUNAAN.md) |
| Mengubah tampilan | Ubah berkas di `layouts/` lalu commit; situs dibangun ulang otomatis |
| Menambah kategori | Lihat bagian 10 |
| Mencadangkan isi | Tab **Code** → tombol **Code** hijau → **Download ZIP** (simpan berkala) |
| Melihat riwayat perubahan | Tab **Commits** |
| Mengembalikan berkas yang salah | Buka berkas → **History** → pilih versi lama → **Restore** |

---

## 9. Mencoba di komputer sendiri (opsional)

Diperlukan bila ingin mengubah tampilan dan melihat hasilnya sebelum tayang.

1. Pasang Hugo versi **0.169.0 atau lebih baru**:
   - Windows: `winget install Hugo.Hugo.Extended`
   - macOS: `brew install hugo`
   - Linux: unduh dari https://github.com/gohugoio/hugo/releases
2. Pasang Python 3 (untuk skrip bantu).
3. Di folder situs, jalankan:

   ```bash
   python scripts/pra_build.py     # menyiapkan arsip & alamat artikel baru
   hugo server                     # buka http://localhost:1313
   ```

4. Untuk melihat pratinjau seperti di server (termasuk pencarian), jalankan:

   ```bash
   hugo --minify
   npx pagefind --site public
   ```

   Lalu layani folder `public/` dengan server statis apa pun.

> Pencarian memakai Pagefind yang indeksnya dibuat saat publikasi, jadi di
> `hugo server` biasa kotak pencarian belum berisi hasil. Ini normal.

---

## 10. Memasang formulir Aspirasi dan Gabung PKS

Dua halaman, **Aspirasi** dan **Gabung PKS**, berisi formulir. Karena situs ini
statis (tidak punya server sendiri), kiriman formulir ditampung oleh **Google
Apps Script** lalu disimpan ke **Google Sheets**. Tidak ada email yang dikirim.

Hasil akhirnya: dua berkas Sheets terpisah — satu untuk aspirasi, satu untuk
pendaftaran — dan satu alamat `/exec` yang dipakai kedua formulir.

### 10a. Buat dua berkas Sheets

1. Buka <https://sheets.new>, beri nama **Aspirasi PKS Boyolali**.
2. Buka lagi <https://sheets.new>, beri nama **Gabung PKS Boyolali**.
3. Jangan mengetik apa pun. Judul kolom dibuat otomatis oleh skrip.

### 10b. Ambil ID kedua berkas

Buka masing-masing berkas. Alamatnya berbentuk:

```
https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890/edit
                                      └────────── ini ID-nya ──────────┘
```

Catat kedua ID.

### 10c. Pasang skrip

1. Buka <https://script.google.com> → **New project**.
2. Hapus isi `Code.gs`, lalu tempel seluruh isi berkas
   `scripts/formulir-apps-script.gs` dari repositori ini.
3. Pada bagian **KONFIGURASI** di paling atas, ganti dua nilai berikut:

   ```js
   var ID_SHEET = {
     aspirasi: 'TEMPEL_ID_SHEET_ASPIRASI',
     gabung: 'TEMPEL_ID_SHEET_GABUNG',
   };
   ```

4. Simpan (Ctrl+S). Beri nama proyek, misalnya **Formulir PKS Boyolali**.

### 10d. Terbitkan sebagai Web App

1. Klik **Deploy** → **New deployment**.
2. Klik ikon gerigi di sebelah "Select type" → pilih **Web app**.
3. Isi:
   - **Description**: `Formulir situs v1`
   - **Execute as**: `Me`
   - **Who has access**: `Anyone`
4. Klik **Deploy**. Saat diminta memberi izin, ikuti sampai selesai
   (pilih akun → **Advanced** → **Go to … (unsafe)** → **Allow**).
   Peringatan "unsafe" muncul karena skrip ini buatan sendiri, bukan aplikasi
   yang sudah terdaftar di Google.
5. Salin **Web app URL** yang berakhiran `/exec`.

> Simpan URL itu. Satu URL dipakai untuk **kedua** formulir — formulir
> mengirim penanda `_jenis` agar skrip tahu harus menulis ke berkas Sheets
> yang mana.

### 10e. Tempel URL ke CMS

1. Buka `/admin/` → **Halaman Tunggal** → **Aspirasi**.
2. Isi **Alamat pengiriman formulir** dengan URL `/exec` tadi. Simpan.
3. Lakukan hal yang sama pada **Gabung PKS** (URL-nya sama).

Selama isian itu masih kosong, formulir tetap tampil tetapi tombol **Kirim**
dimatikan dan pengunjung diarahkan menghubungi kantor lewat telepon/email.
Jadi halaman boleh tayang lebih dulu sebelum formulir siap.

### 10f. Uji sekali

1. Buka halaman **Aspirasi** di situs, isi formulir dengan data uji, kirim.
2. Buka berkas **Aspirasi PKS Boyolali** di Sheets. Satu baris baru harus muncul
   lengkap dengan waktu kirim.
3. Ulangi untuk **Gabung PKS** dan periksa berkas Sheets yang satunya.
4. Hapus baris data uji.

### 10g. Yang perlu diingat

- **Setiap kali skrip diubah**, terbitkan versi baru: **Deploy** →
  **Manage deployments** → ikon pensil → **Version: New version** → **Deploy**.
  Tanpa itu, perubahan tidak terpakai.
- **Versi terbaru skrip ini** mengubah bentuk penyimpanan nomor HP (tanpa
  awalan `0`/`62`) dan cara penulisan kolom. Bila sebelumnya sudah memasang
  versi lama, tempel ulang berkas `scripts/formulir-apps-script.gs` lalu
  terbitkan **New version** — tanpa itu nomor HP tetap tersimpan dengan awalan
  `0` dan isian baru tidak dikenali.
- **Kolom NIK sudah tersedia** di kedua Sheets meskipun isian NIK dimatikan.
  Saat nanti NIK perlu dikumpulkan, cukup nyalakan **Tampilkan isian NIK** di
  CMS — skrip tidak perlu disentuh lagi.
- **Jangan menaruh data kiriman di repositori.** Semua isi formulir hanya ada
  di Sheets. Atur akses berkas Sheets lewat tombol **Share** (hanya pengurus).
- **Menghentikan formulir**: kosongkan kembali isian **Alamat pengiriman
  formulir** di CMS. Kiriman baru tidak akan diterima.
- **Batas**: Apps Script gratis menampung sekitar 20.000 kiriman/hari — jauh di
  atas kebutuhan situs ini. Kuota Sheets 10 juta sel per berkas.

### 10h. Menambah atau mengubah isian formulir

Lima isian pokok sudah tetap dan tidak bisa dihapus: **Nama lengkap**,
**Nomor HP / WhatsApp**, **Email**, **Kecamatan**, dan **Desa / Kelurahan**.
Kecamatan dan desa berpasangan — daftar desa menyesuaikan kecamatan yang
dipilih.

Selebihnya bebas. Buka `/admin/` → **Halaman Tunggal** → **Aspirasi** atau
**Gabung PKS** → **Isian tambahan formulir**. Tiap isian punya:

| Kolom | Arti |
|---|---|
| **Kunci** | Nama mesin, huruf kecil tanpa spasi (`rt_rw`, `usia`). Dipakai sebagai penanda data. |
| **Label** | Teks yang tampil di formulir, sekaligus judul kolom baru di Sheets. |
| **Jenis isian** | Teks satu baris, teks panjang, email, nomor telepon, angka saja, atau pilihan (dropdown). |
| **Wajib diisi** | Bila dinyalakan, kiriman dengan isian kosong ditolak. |
| **Lebar isian** | Penuh, atau setengah — dua isian setengah akan berdampingan di layar lebar. |
| **Daftar pilihan** | Hanya untuk jenis "pilihan". Satu baris satu pilihan. |
| **Teks bantuan** | Keterangan kecil di bawah isian. |

**Skrip Apps Script tidak perlu diubah.** Skrip menulis data menurut *nama
kolom*, bukan urutan. Begitu ada isian baru, kolomnya dibuat sendiri dan
disisipkan sebelum kolom **Status** — jadi Status dan Catatan tetap di ujung.

> Yang perlu dirapikan hanya bila isian **dihapus atau labelnya diganti**:
> kolom lama di Sheets tidak ikut terhapus, dan kolom dengan judul baru muncul
> di sebelahnya. Hapus kolom lama itu manual bila sudah tidak dipakai.

### 10i. Bentuk nomor HP yang disimpan

Formulir hanya menerima angka, tanda `+` di awal sebagai kode negara, spasi,
dan tanda hubung. Huruf dibuang begitu diketik, dan kiriman dengan nomor yang
tidak masuk akal ditolak sebelum terkirim.

Yang **masuk ke Sheets** sudah dibersihkan: tanpa `0`, `62`, maupun `+62`.

| Diketik | Tersimpan |
|---|---|
| `081234567890` | `81234567890` |
| `+62 812-3456-7890` | `81234567890` |
| `6281234567890` | `81234567890` |

Data lama yang terlanjur tersimpan dengan awalan `0` bisa disamakan dengan
rumus bantu di kolom kosong, misalnya
`=IF(LEFT(C2;1)="0";MID(C2;2;20);C2)`, lalu hasilnya disalin ke kolom aslinya
(**Paste special → Values only**). Bila Sheets Anda memakai koma sebagai
pemisah argumen, ganti `;` menjadi `,`.

---

## 11. Menambah kategori baru

Kategori yang ada sekarang: Fraksi PKS, Harokah, Inspirasi, Kiprah Kami, Oase,
Pilkada, Ragam, Seputar Boyolali, Seputar PKS, Topik Pilihan.

Untuk menambah, misalnya "Ekonomi":

1. **Buat halaman kategori**
   - Di GitHub: masuk `content/categories/` → **Add file** → **Create new file**.
   - Nama berkas: `ekonomi/_index.md` (folder `ekonomi` dibuat otomatis).
   - Isi:

     ```yaml
     ---
     title: "Ekonomi"
     ---
     ```

2. **Daftarkan di CMS** — buka `static/admin/config.yml`, cari `name: categories`,
   lalu tambahkan baris `- Ekonomi` pada daftar `options`. Daftar ini muncul di
   dua tempat (koleksi Artikel dan halaman gabungan); tambahkan di keduanya.
3. **Tambahkan ke menu** (opsional) lewat **Header & Menu** di admin, pilih
   kategori `Ekonomi`.
4. Commit. Situs dibangun ulang otomatis.

---

## 12. Bila ada masalah

| Gejala | Penyebab dan solusi |
|---|---|
| Halaman putih / 404 setelah push | Buka tab **Actions**. Bila merah, buka prosesnya dan baca baris merah paling atas. Sering karena salah ketik di YAML. |
| **Beranda menampilkan isi README/panduan, bukan tampilan situs** | Sumber Pages masih **Deploy from a branch**. GitHub merender `README.md` menjadi beranda (Jekyll) dan hasilnya menimpa build Hugo. Perbaiki: **Settings → Pages → Source: GitHub Actions** → **Save**, lalu jalankan ulang **Publikasi situs**. Bila pilihannya sudah "GitHub Actions" tetapi gejala ini tetap muncul, ganti dulu ke "Deploy from a branch", **Save**, lalu kembalikan ke "GitHub Actions", **Save**, dan jalankan ulang workflow. |
| Di tab Actions ada dua proses: **Publikasi situs** dan **pages build and deployment** | Tanda sumber Pages masih branch. Setelah sumber diubah ke GitHub Actions, proses `pages build and deployment` tidak muncul lagi dan hanya build Hugo yang tayang. |
| Proses gagal: "Resource not accessible" / "permission denied" | **Settings → Actions → General → Workflow permissions** belum **Read and write**. |
| Situs tampil tanpa warna/gambar | Alamat domain belum cocok. Periksa `hugo.toml` bagian `baseURL` dan **Settings → Pages → Custom domain**. |
| "DNS check unsuccessful" | Catatan CNAME belum ada atau salah. Nilai harus `pksboyolali.github.io` (bukan alamat repo). Tunggu hingga 1 jam. |
| HTTPS tidak bisa dicentang | Tunggu sertifikat selesai dibuat (bisa 15–60 menit setelah DNS benar). |
| `/admin/` kosong atau "repo not found" | `repo:` di `static/admin/config.yml` tidak cocok dengan nama repositori. Lihat bagian 6a. |
| Login CMS gagal "not authorized" | Token tidak punya izin `Contents: Read and write`, atau akun tidak punya akses tulis ke repo. |
| Tombol **Sign in with GitHub** berakhir di halaman kosong / 404 | Belum ada server OAuth. Tanpa itu Sveltia memakai `api.netlify.com` yang menjawab 404 untuk situs GitHub Pages. Pakai **token**; rincian di bagian 6d. |
| Gambar tidak muncul di artikel | Berkas gambar belum terunggah. Pastikan folder `static/images/uploads/` ikut ter-commit. |
| Pencarian tidak menemukan apa pun | Indeks Pagefind belum dibuat. Pastikan langkah "Indeks pencarian" di workflow tidak dihapus. |
| Berita baru tidak muncul | Proses build masih berjalan (±3 menit) atau artikel tersimpan sebagai draf. Cek tab **Actions**. |
| Berkas `.md` berubah sendiri setelah publikasi | Normal: workflow menambahkan `slug:` dan halaman arsip otomatis, lalu menyimpannya kembali. |
| Tombol **Kirim** mati dan muncul nomor telepon | Isian **Alamat pengiriman formulir** di CMS masih kosong. Lihat bagian 10e. |
| Formulir terkirim, tapi Sheets tetap kosong | ID Sheets salah, atau skrip belum diterbitkan ulang setelah diubah. Buka Apps Script → **Executions** untuk melihat galatnya. |
| Muncul pesan "Terjadi kesalahan di server" | Buka Apps Script → **Executions**, baca pesan galatnya. Sering karena ID Sheets belum diisi. |
| Desa/kelurahan tidak bisa dipilih | Kecamatan belum dipilih. Dropdown desa memang menunggu pilihan kecamatan. |

---

## 13. Batas dan catatan teknis

- Repositori publik GitHub gratis; ukuran disarankan di bawah **1 GB**.
  Situs ini ±150 MB termasuk ±800 gambar.
- GitHub Pages: kuota lunak **100 GB/bulan** lalu lintas dan **10 build/jam**.
  Untuk situs sekabupaten, angka ini sangat longgar.
- Gambar disarankan di bawah 300 KB dan lebar maksimal 1400 px. Skrip
  `scripts/optimalkan_gambar.py` bisa memperkecil gambar lama sekaligus.
- Jangan mengubah `content/arsip/` secara manual — isinya dibuat ulang otomatis.
- Berkas `static/_redirects` hanya dipakai bila suatu saat pindah ke Netlify;
  di GitHub Pages berkas ini diabaikan dan tidak mengganggu.

---

## 14. Memindahkan situs ke akun/organisasi lain

1. GitHub: **Settings** → gulir bawah → **Transfer ownership**.
2. Setelah pindah, perbarui:
   - `repo:` di `static/admin/config.yml`
   - nilai CNAME DNS bila nama akun berubah
3. Undang ulang para pengurus sebagai collaborator.
