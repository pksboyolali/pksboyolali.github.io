/**
 * ============================================================================
 *  Formulir Aspirasi & Gabung PKS — DPD PKS Boyolali
 *  Backend Google Apps Script (Web App) + Google Sheets
 * ============================================================================
 *
 *  CARA PASANG (ringkas, detail di PANDUAN-PASANG.md):
 *   1. Buat DUA berkas Google Sheets baru:
 *        - "Aspirasi PKS Boyolali"
 *        - "Gabung PKS Boyolali"
 *      Cukup buat berkas kosong, judul kolom dibuat otomatis oleh skrip ini.
 *   2. Ambil ID masing-masing berkas dari URL-nya:
 *        https://docs.google.com/spreadsheets/d/<ID>/edit
 *      Tempelkan ke ID_SHEET di bawah.
 *   3. Buka https://script.google.com → New project → tempel isi berkas ini.
 *   4. Deploy → New deployment → type "Web app"
 *        - Execute as        : Me
 *        - Who has access    : Anyone
 *      Lalu salin URL yang berakhiran /exec.
 *   5. Tempel URL itu ke isian "Alamat pengiriman formulir" pada halaman
 *      Aspirasi dan Gabung PKS di CMS. Satu URL dipakai untuk keduanya —
 *      formulir mengirim penanda "_jenis" untuk memilih berkas Sheets.
 *
 *  CATATAN PENTING
 *   - Tidak ada email yang dikirim. Data hanya masuk ke Sheets.
 *   - Kolom NIK selalu tersedia. Bila NIK belum diaktifkan di formulir,
 *     kolomnya tetap ada tetapi berisi kosong. Jadi saat nanti NIK
 *     diaktifkan di CMS, skrip ini TIDAK perlu diubah lagi.
 *   - Isian tambahan diatur di CMS (Halaman Tunggal → Aspirasi / Gabung PKS).
 *     Skrip ini menulis data berdasarkan NAMA KOLOM, bukan urutan, dan
 *     membuat kolom baru sendiri bila ada isian baru. Jadi menambah isian di
 *     CMS TIDAK perlu mengubah atau men-deploy ulang skrip ini.
 *   - Nomor HP disimpan tanpa awalan 0, 62, maupun +62.
 *     Contoh: 081234567890 / +62 812-3456-7890 → 81234567890.
 *   - Setiap kali kode ini diubah, lakukan Deploy → Manage deployments →
 *     Edit → Version: New version, agar perubahan ikut terpakai.
 */

// ---------------------------------------------------------------------------
// 1. KONFIGURASI — hanya bagian ini yang perlu Anda ubah
// ---------------------------------------------------------------------------

var ID_SHEET = {
  // Tempel ID berkas Sheets di antara tanda kutip.
  aspirasi: '1s65l7NsUCmIrWjSunzhtF_a0rjNXHhLo1Tk5IW-GiCU',
  gabung: '1Nj3MLCNFME7dnCvKM2z8b-Z5wNIxz870sj90-7Raxec',
};

var ZONA_WAKTU = 'Asia/Jakarta'; // zona waktu pencatatan
var MIN_DETIK = 3; // kiriman lebih cepat dari ini dianggap bot
var MAKS_MENIT = 720; // formulir kedaluwarsa setelah 12 jam

// ---------------------------------------------------------------------------
// 2. PENGATURAN PER JENIS FORMULIR
// ---------------------------------------------------------------------------

var PENGATURAN = {
  aspirasi: {
    namaTab: 'Aspirasi',
    // Urutan kolom awal. Dipakai hanya saat tab masih kosong; sesudahnya
    // skrip mengikuti judul kolom yang sudah ada di Sheets.
    kolom: [
      'Waktu',
      'Nama',
      'No. HP',
      'Email',
      'Kecamatan',
      'Desa/Kelurahan',
      'Kategori',
      'Isi aspirasi',
      'NIK',
      'Status',
      'Catatan',
    ],
    // Dipakai bila formulir tidak mengirim daftar isian wajib (_wajib).
    wajibBawaan: ['kategori', 'pesan'],
  },
  gabung: {
    namaTab: 'Gabung',
    kolom: [
      'Waktu',
      'Nama',
      'No. HP',
      'Email',
      'Kecamatan',
      'Desa/Kelurahan',
      'Pekerjaan',
      'Alasan bergabung',
      'NIK',
      'Status',
      'Catatan',
    ],
    wajibBawaan: ['alasan'],
  },
};

// Judul kolom untuk isian yang sudah dikenal. Isian baru yang belum ada di
// sini memakai label yang dikirim formulir (dari CMS).
var LABEL = {
  nama: 'Nama',
  hp: 'No. HP',
  email: 'Email',
  kecamatan: 'Kecamatan',
  desa: 'Desa/Kelurahan',
  nik: 'NIK',
  kategori: 'Kategori',
  pesan: 'Isi aspirasi',
  pekerjaan: 'Pekerjaan',
  alasan: 'Alasan bergabung',
};

// Isian yang ditangani khusus — tidak boleh menjadi kolom tambahan.
var KUNCI_INTI = ['nama', 'hp', 'email', 'kecamatan', 'desa', 'nik'];
var KUNCI_KHUSUS = ['_jenis', '_waktu', '_jebakan', '_wajib', '_label', 'setuju'];

// 22 kecamatan Kabupaten Boyolali — dipakai untuk menolak kiriman asal-asalan.
var KECAMATAN = [
  'Ampel', 'Andong', 'Banyudono', 'Boyolali', 'Cepogo', 'Gladagsari',
  'Juwangi', 'Karanggede', 'Kemusu', 'Klego', 'Mojosongo', 'Musuk',
  'Ngemplak', 'Nogosari', 'Sambi', 'Sawit', 'Selo', 'Simo',
  'Tamansari', 'Teras', 'Wonosamodro', 'Wonosegoro',
];

// ---------------------------------------------------------------------------
// 3. TITIK MASUK WEB APP
// ---------------------------------------------------------------------------

/**
 * Dipanggil saat formulir dikirim (POST).
 * Selalu membalas JSON; formulir memakai mode "no-cors" sehingga isi balasan
 * tidak terbaca oleh peramban, tetapi balasan ini berguna saat diuji manual.
 */
function doPost(e) {
  try {
    var p = (e && e.parameter) || {};
    var jenis = String(p._jenis || 'aspirasi').toLowerCase();
    var atur = PENGATURAN[jenis];

    if (!atur) {
      return balas({ ok: false, pesan: 'Jenis formulir tidak dikenal: ' + jenis });
    }

    // --- Jebakan bot: kolom tersembunyi yang tidak boleh diisi manusia.
    if (p._jebakan) {
      // Dibalas "berhasil" supaya bot tidak tahu dirinya ditolak.
      return balas({ ok: true, pesan: 'Terima kasih.' });
    }

    // --- Pintu waktu: kiriman terlalu cepat dianggap bot.
    var waktuMuat = Number(p._waktu || 0);
    if (waktuMuat > 0) {
      var selisihDetik = (Date.now() - waktuMuat) / 1000;
      if (selisihDetik < MIN_DETIK) {
        return balas({ ok: true, pesan: 'Terima kasih.' });
      }
      if (selisihDetik > MAKS_MENIT * 60) {
        return balas({
          ok: false,
          pesan: 'Halaman sudah terlalu lama terbuka. Muat ulang lalu kirim lagi.',
        });
      }
    }

    // --- Rapikan dan periksa isian inti.
    var nama = bersih(p.nama, 80);
    var hp = rapikanHp(p.hp);
    var email = bersih(p.email, 100);
    var kecamatan = bersih(p.kecamatan, 40);
    var desa = bersih(p.desa, 60);
    var nik = String(p.nik || '').replace(/\D/g, '');

    if (!nama) return gagal('Nama lengkap wajib diisi.');
    if (!hp) {
      // Sudah diisi tetapi tidak menyisakan satu angka pun (mis. hanya huruf).
      var hpMentah = String(p.hp == null ? '' : p.hp).trim();
      return gagal(hpMentah ? 'Nomor HP/WhatsApp tidak valid.' : 'Nomor HP/WhatsApp wajib diisi.');
    }
    if (!POLA_HP.test(hp)) return gagal('Nomor HP/WhatsApp tidak valid.');
    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
      return gagal('Alamat email tidak valid.');
    }
    if (KECAMATAN.indexOf(kecamatan) === -1) return gagal('Kecamatan tidak dikenal.');
    if (!desa) return gagal('Desa/kelurahan wajib dipilih.');
    if (String(p.setuju || '') !== 'ya') return gagal('Persetujuan wajib dicentang.');

    // NIK: hanya diperiksa bila memang dikirim (kolomnya opsional di formulir).
    if (nik && !/^[0-9]{16}$/.test(nik)) return gagal('NIK harus 16 angka.');

    // --- Susun data berdasarkan NAMA KOLOM, bukan urutan.
    var data = {};
    data['Waktu'] = new Date();
    data['Nama'] = nama;
    data['No. HP'] = hp;
    data['Email'] = email;
    data['Kecamatan'] = kecamatan;
    data['Desa/Kelurahan'] = desa;

    var label = bacaLabel(p._label);
    var urut = urutkanDinamis(p, label);

    for (var i = 0; i < urut.length; i++) {
      var k = urut[i];
      data[judulKolom(k, label)] = rapikanTeks(p[k], 4000);
    }

    data['NIK'] = nik;
    data['Status'] = 'Baru';
    data['Catatan'] = '';

    // --- Isian wajib tambahan: daftar kuncinya dikirim formulir dari CMS.
    var wajib = bacaDaftar(p._wajib);
    if (!wajib.length) wajib = atur.wajibBawaan;
    for (var w = 0; w < wajib.length; w++) {
      var kw = wajib[w];
      if (KUNCI_INTI.indexOf(kw) !== -1 || KUNCI_KHUSUS.indexOf(kw) !== -1) continue;
      if (!data[judulKolom(kw, label)]) {
        return gagal('Isian "' + judulKolom(kw, label) + '" wajib diisi.');
      }
    }

    simpan(jenis, atur, data);

    return balas({ ok: true, pesan: 'Terima kasih, kiriman Anda sudah diterima.' });
  } catch (err) {
    console.error(err);
    return balas({ ok: false, pesan: 'Terjadi kesalahan di server: ' + err.message });
  }
}

/** Dibuka lewat peramban untuk memastikan endpoint hidup. */
function doGet() {
  return ContentService.createTextOutput(
    'Endpoint formulir PKS Boyolali aktif.\n' +
      'Kiriman harus dikirim lewat metode POST dari formulir di situs.'
  ).setMimeType(ContentService.MimeType.TEXT);
}

// ---------------------------------------------------------------------------
// 4. PENYIMPANAN
// ---------------------------------------------------------------------------

function simpan(jenis, atur, data) {
  var id = ID_SHEET[jenis];
  if (!id || id.indexOf('TEMPEL') === 0) {
    throw new Error('ID Sheets untuk "' + jenis + '" belum diisi di bagian KONFIGURASI.');
  }

  var kunci = LockService.getScriptLock();
  kunci.waitLock(20000); // cegah dua kiriman menulis baris yang sama
  try {
    var ss = SpreadsheetApp.openById(id);
    var sheet = siapkanTab(ss, atur);
    tulisBaris(sheet, atur, data);
  } finally {
    kunci.releaseLock();
  }
}

/** Membuat tab + judul kolom bila belum ada. */
function siapkanTab(ss, atur) {
  var sheet = ss.getSheetByName(atur.namaTab);
  if (!sheet) sheet = ss.insertSheet(atur.namaTab);

  if (sheet.getLastRow() === 0) {
    ss.setSpreadsheetTimeZone(ZONA_WAKTU);
    sheet.getRange(1, 1, 1, atur.kolom.length).setValues([atur.kolom]);
    rapikanKepala(sheet, atur.kolom);

    try {
      sheet.getRange(1, 1, 1, atur.kolom.length).createFilter();
    } catch (abaikan) {
      // Filter sudah ada — tidak masalah.
    }
  }

  return sheet;
}

/**
 * Menulis satu baris dengan mencocokkan NAMA kolom. Kolom yang belum ada
 * dibuat otomatis (disisipkan sebelum "Status" agar Status dan Catatan tetap
 * di ujung). Inilah yang membuat penambahan isian di CMS tidak perlu
 * menyentuh skrip ini.
 */
function tulisBaris(sheet, atur, data) {
  var lebar = sheet.getLastColumn();
  var kepala = lebar > 0 ? sheet.getRange(1, 1, 1, lebar).getValues()[0] : [];

  var urut = [];
  for (var i = 0; i < kepala.length; i++) {
    var h = String(kepala[i] == null ? '' : kepala[i]).trim();
    if (h) urut.push(h);
  }
  if (!urut.length) urut = atur.kolom.slice();

  // Kolom baru yang belum ada di kepala tabel.
  var baru = [];
  for (var k in data) {
    if (urut.indexOf(k) === -1 && baru.indexOf(k) === -1) baru.push(k);
  }

  if (baru.length) {
    var pos = urut.indexOf('Status');
    if (pos === -1) pos = urut.length;
    var disisipkan = false;
    try {
      sheet.insertColumnsBefore(pos + 1, baru.length);
      disisipkan = true;
    } catch (abaikan) {
      // Bila gagal (mis. ada filter), kolom baru ditaruh di ujung.
      pos = urut.length;
    }
    if (disisipkan || pos === urut.length) {
      urut = urut.slice(0, pos).concat(baru, urut.slice(pos));
      sheet.getRange(1, 1, 1, urut.length).setValues([urut]);
      rapikanKepala(sheet, urut);
    }
  }

  var baris = [];
  for (var j = 0; j < urut.length; j++) {
    var v = data[urut[j]];
    baris.push(v === undefined || v === null ? '' : v);
  }
  sheet.appendRow(baris);
}

/** Format judul kolom, lebar kolom, bungkus teks, dan pilihan Status. */
function rapikanKepala(sheet, urut) {
  var judul = sheet.getRange(1, 1, 1, urut.length);
  judul.setFontWeight('bold').setBackground('#e8eaed').setVerticalAlignment('middle');
  sheet.setFrozenRows(1);
  sheet.setRowHeight(1, 34);

  var lebar = {
    'Waktu': 140, 'Nama': 160, 'No. HP': 130, 'Email': 180, 'Kecamatan': 120,
    'Desa/Kelurahan': 150, 'Kategori': 110, 'Isi aspirasi': 320,
    'Alasan bergabung': 320, 'Pekerjaan': 130, 'NIK': 140, 'Status': 110,
    'Catatan': 200,
  };

  for (var i = 0; i < urut.length; i++) {
    var nama = urut[i];
    sheet.setColumnWidth(i + 1, lebar[nama] || 150);
    // Isian panjang: bungkus teksnya.
    if (/isi|alasan|catatan|keterangan/i.test(nama)) {
      sheet.getRange(2, i + 1, 2000, 1).setWrap(true);
    }
  }

  sheet.getRange('A:A').setNumberFormat('dd/MM/yyyy HH:mm');

  var posStatus = urut.indexOf('Status');
  if (posStatus !== -1) {
    var aturan = SpreadsheetApp.newDataValidation()
      .requireValueInList(['Baru', 'Diproses', 'Selesai', 'Diabaikan'], true)
      .setAllowInvalid(false)
      .build();
    sheet.getRange(2, posStatus + 1, 2000, 1).setDataValidation(aturan);
  }
}

// ---------------------------------------------------------------------------
// 5. PEMBANTU
// ---------------------------------------------------------------------------

function balas(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON
  );
}

function gagal(pesan) {
  return balas({ ok: false, pesan: pesan });
}

/** Potong spasi berlebih dan batasi panjang teks (untuk isian pendek). */
function bersih(nilai, maks) {
  var t = String(nilai == null ? '' : nilai)
    .replace(/\s+/g, ' ')
    .trim();
  if (maks && t.length > maks) t = t.substring(0, maks);
  return t;
}

/** Seperti bersih(), tetapi baris baru dipertahankan (untuk isi panjang). */
function rapikanTeks(nilai, maks) {
  var t = String(nilai == null ? '' : nilai)
    .replace(/\r\n/g, '\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
  if (maks && t.length > maks) t = t.substring(0, maks);
  return t;
}

/** Bentuk baku nomor HP: angka saja, tanpa 0 / 62 / +62 di depan. */
var POLA_HP = /^[1-9][0-9]{7,12}$/;

function rapikanHp(nilai) {
  var d = String(nilai == null ? '' : nilai).replace(/[^0-9]/g, '');
  if (d.length > 2 && d.substring(0, 2) === '62') d = d.substring(2);
  else if (d.charAt(0) === '0') d = d.substring(1);
  return d;
}

/** Kunci isian yang boleh menjadi kolom tambahan. */
function kunciSah(k) {
  if (!/^[a-z][a-z0-9_]{0,23}$/.test(k)) return false;
  if (KUNCI_INTI.indexOf(k) !== -1) return false;
  if (KUNCI_KHUSUS.indexOf(k) !== -1) return false;
  return true;
}

/** Urutan isian tambahan: ikut urutan CMS (_label), sisanya menyusul. */
function urutkanDinamis(p, label) {
  var hasil = [];
  for (var k in label) {
    if (kunciSah(k)) hasil.push(k);
  }
  for (var k2 in p) {
    if (kunciSah(k2) && hasil.indexOf(k2) === -1 && hasil.length < 15) hasil.push(k2);
  }
  return hasil;
}

/** Judul kolom untuk sebuah kunci isian. */
function judulKolom(kunci, label) {
  if (label && label[kunci]) return bersih(label[kunci], 40);
  if (LABEL[kunci]) return LABEL[kunci];
  var t = String(kunci || '').replace(/_/g, ' ');
  return t.charAt(0).toUpperCase() + t.substring(1);
}

/** Membaca _wajib (JSON array kunci). */
function bacaDaftar(teks) {
  if (!teks) return [];
  try {
    var d = JSON.parse(teks);
    if (!d || typeof d.length !== 'number') return [];
    var hasil = [];
    for (var i = 0; i < d.length && i < 20; i++) {
      var k = String(d[i] || '');
      if (/^[a-z][a-z0-9_]{0,23}$/.test(k)) hasil.push(k);
    }
    return hasil;
  } catch (e) {
    return [];
  }
}

/** Membaca _label (JSON objek kunci → label). */
function bacaLabel(teks) {
  if (!teks) return {};
  try {
    var d = JSON.parse(teks);
    if (!d || typeof d !== 'object') return {};
    var hasil = {};
    for (var k in d) {
      if (!/^[a-z][a-z0-9_]{0,23}$/.test(k)) continue;
      hasil[k] = bersih(d[k], 40);
    }
    return hasil;
  } catch (e) {
    return {};
  }
}
