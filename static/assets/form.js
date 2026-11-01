/* Formulir Aspirasi & Gabung PKS.
   Mengirim data ke alamat /exec Apps Script (lihat scripts/formulir-apps-script.gs).
   - Dropdown desa/kelurahan diisi mengikuti kecamatan yang dipilih.
   - Nomor HP hanya menerima angka, "+" di awal, spasi, dan tanda hubung.
   - Daftar isian tambahan dibaca dari skema di front matter (diatur lewat CMS). */
(function () {
  var form = document.querySelector('form[data-formulir]');
  if (!form) return;

  var status = form.querySelector('[data-status]');
  var tombol = form.querySelector('.formulir-tombol');
  var kecSel = form.querySelector('[data-kecamatan]');
  var desaSel = form.querySelector('[data-desa]');
  var waktu = form.querySelector('input[name="_waktu"]');
  var inputWajib = form.querySelector('input[name="_wajib"]');
  var inputLabel = form.querySelector('input[name="_label"]');

  function bacaJson(sel) {
    var el = form.querySelector('script[' + sel + ']');
    if (!el) return [];
    try { return JSON.parse(el.textContent); } catch (e) { return []; }
  }

  var wilayah = bacaJson('data-wilayah');
  var skema = bacaJson('data-skema');

  // --- Pop-up konfirmasi ---------------------------------------------------
  var modal = document.querySelector('[data-modal]');
  var modalKartu = modal && modal.querySelector('.formulir-modal-kartu');
  var modalTombol = modal && modal.querySelector('[data-modal-tombol]');

  // Dipindah ke <body> supaya "position:fixed" tidak terpengaruh wadah
  // ber-transform di dalam artikel, dan z-index-nya lepas dari tumpukan tema.
  if (modal && modal.parentNode !== document.body) {
    document.body.appendChild(modal);
  }

  function bukaModal() {
    if (!modal) return;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    // Fokus ke kartu, bukan ke tombol: pembaca layar langsung membacakan isi
    // pop-up tanpa memunculkan cincin fokus di tombol.
    if (modalKartu) modalKartu.focus();
  }

  // Tahan fokus di dalam pop-up: Tab memindahkan fokus ke satu-satunya tombol.
  if (modal) {
    modal.addEventListener('keydown', function (e) {
      if (e.key !== 'Tab') return;
      e.preventDefault();
      if (modalTombol) modalTombol.focus();
    });
  }

  function setStatus(teks, jenis) {
    if (!status) return;
    status.textContent = teks || '';
    status.className = 'formulir-status' + (jenis ? ' formulir-status--' + jenis : '');
  }

  // --- Nomor HP ------------------------------------------------------------
  // Bentuk baku yang disimpan: angka saja, tanpa 0 / 62 / +62 di depan.
  // Contoh: 081234567890, +62 812-3456-7890, 6281234567890 → 81234567890.
  var POLA_HP = /^[1-9][0-9]{7,12}$/;

  function intiHp(nilai) {
    var d = String(nilai || '').replace(/[^0-9]/g, '');
    if (d.length > 2 && d.substring(0, 2) === '62') d = d.substring(2);
    else if (d.charAt(0) === '0') d = d.substring(1);
    return d;
  }

  // Buang karakter terlarang seketika, lalu kembalikan posisi kursor.
  function saringHp(el) {
    var asli = el.value;
    var pos = el.selectionStart;
    if (pos === null || pos === undefined) pos = asli.length;

    var hasil = asli.replace(/[^0-9+\- ]/g, '');
    // "+" hanya boleh di awal sebagai kode negara.
    var plus = hasil.charAt(0) === '+';
    hasil = (plus ? '+' : '') + hasil.replace(/\+/g, '');
    if (hasil === asli) return;

    var h = 0;
    var a = 0;
    while (a < pos && h < hasil.length) {
      if (asli.charAt(a) === hasil.charAt(h)) { a++; h++; } else { a++; }
    }

    el.value = hasil;
    try { el.setSelectionRange(h, h); } catch (e) { /* abaikan */ }
  }

  function pesanGalat(el, teks) {
    var kotak = form.querySelector('[data-galat-for="' + (el.getAttribute('name') || '') + '"]');
    var wadah = el.closest ? el.closest('.formulir-isian') : null;
    if (teks) {
      el.setAttribute('aria-invalid', 'true');
      if (wadah) wadah.classList.add('formulir-isian--salah');
      if (kotak) { kotak.textContent = teks; kotak.hidden = false; }
    } else {
      el.removeAttribute('aria-invalid');
      if (wadah) wadah.classList.remove('formulir-isian--salah');
      if (kotak) { kotak.textContent = ''; kotak.hidden = true; }
    }
  }

  function periksaHp(el) {
    var nilai = String(el.value || '').trim();
    if (!nilai) {
      pesanGalat(el, el.required ? 'Nomor HP/WhatsApp wajib diisi.' : '');
      return !el.required;
    }
    if (!POLA_HP.test(intiHp(nilai))) {
      pesanGalat(el, 'Nomor HP belum benar. Tulis angka saja, 9–14 digit. Contoh: 081234567890.');
      return false;
    }
    pesanGalat(el, '');
    return true;
  }

  function bersihkanGalat() {
    var kotak = form.querySelectorAll('[data-galat-for]');
    for (var i = 0; i < kotak.length; i++) { kotak[i].textContent = ''; kotak[i].hidden = true; }
    var salah = form.querySelectorAll('[aria-invalid]');
    for (var j = 0; j < salah.length; j++) salah[j].removeAttribute('aria-invalid');
    var wadah = form.querySelectorAll('.formulir-isian--salah');
    for (var k = 0; k < wadah.length; k++) wadah[k].classList.remove('formulir-isian--salah');
  }

  // Karena balon bawaan ditahan, fokus harus dipindah sendiri ke kolom
  // pertama yang salah — sama seperti perilaku peramban.
  function fokusPertamaSalah() {
    var semua = form.querySelectorAll('input:not([type=hidden]), select, textarea');
    for (var i = 0; i < semua.length; i++) {
      if (!semua[i].checkValidity()) { semua[i].focus(); return; }
    }
  }

  var hpEls = form.querySelectorAll('[data-hp]');
  for (var i = 0; i < hpEls.length; i++) {
    (function (el) {
      // Peramban memeriksa "wajib diisi" sebelum event submit. Balon bawaannya
      // diganti pesan sendiri agar bahasanya sama dengan pesan lain.
      el.addEventListener('invalid', function (e) {
        e.preventDefault();
        pesanGalat(el, el.required ? 'Nomor HP/WhatsApp wajib diisi.' : '');
        setTimeout(fokusPertamaSalah, 0);
      });
      el.addEventListener('input', function () {
        saringHp(el);
        if (el.getAttribute('aria-invalid')) periksaHp(el);
      });
      el.addEventListener('blur', function () {
        if (el.value.trim()) periksaHp(el);
      });
    })(hpEls[i]);
  }

  // --- Kecamatan → desa/kelurahan ------------------------------------------
  function isiDesa() {
    if (!kecSel || !desaSel) return;
    var kec = kecSel.value;
    var daftar = [];
    for (var i = 0; i < wilayah.length; i++) {
      if (wilayah[i].nama === kec) { daftar = wilayah[i].desa || []; break; }
    }
    desaSel.innerHTML = '';
    var awal = document.createElement('option');
    awal.value = '';
    awal.textContent = daftar.length ? '— pilih desa / kelurahan —' : '— pilih kecamatan dulu —';
    desaSel.appendChild(awal);
    for (var j = 0; j < daftar.length; j++) {
      var o = document.createElement('option');
      o.value = daftar[j];
      o.textContent = daftar[j];
      desaSel.appendChild(o);
    }
    desaSel.disabled = daftar.length === 0;
  }

  // --- Skema isian tambahan ------------------------------------------------
  // _wajib dan _label dipakai skrip Apps Script untuk memeriksa isian wajib
  // dan memberi judul kolom baru di Sheets.
  function siapkanSkema() {
    var wajib = [];
    var label = {};
    for (var i = 0; i < skema.length; i++) {
      var f = skema[i] || {};
      if (!f.kunci) continue;
      label[f.kunci] = f.label || f.kunci;
      if (f.wajib) wajib.push(f.kunci);
    }
    if (inputWajib) inputWajib.value = JSON.stringify(wajib);
    if (inputLabel) inputLabel.value = JSON.stringify(label);
  }

  if (kecSel) kecSel.addEventListener('change', isiDesa);
  if (waktu) waktu.value = Date.now();
  siapkanSkema();

  // --- Pengiriman ----------------------------------------------------------
  form.addEventListener('submit', function (e) {
    e.preventDefault();

    // Nomor HP diperiksa lebih dulu agar pesannya berbahasa Indonesia.
    var daftarHp = form.querySelectorAll('[data-hp]');
    for (var i = 0; i < daftarHp.length; i++) {
      if (!periksaHp(daftarHp[i])) { daftarHp[i].focus(); return; }
    }

    if (!form.checkValidity()) { form.reportValidity(); return; }

    var aksi = form.getAttribute('action');
    if (!aksi) { setStatus('Formulir belum aktif.', 'error'); return; }

    siapkanSkema();

    var data = new URLSearchParams(new FormData(form));
    if (tombol) { tombol.disabled = true; tombol.textContent = 'Mengirim…'; }
    setStatus('Sedang mengirim…', '');

    // mode "no-cors" dipakai karena Apps Script tidak mengirim header CORS;
    // jawabannya tidak bisa dibaca, jadi keberhasilan dianggap saat permintaan selesai.
    fetch(aksi, { method: 'POST', mode: 'no-cors', body: data })
      .then(function () {
        form.reset();
        isiDesa();
        bersihkanGalat();
        if (waktu) waktu.value = Date.now();
        siapkanSkema();
        // Teks di bawah tombol tetap diisi sebagai cadangan bila pop-up gagal tampil.
        setStatus('Terima kasih, kiriman Anda sudah diterima.', 'ok');
        bukaModal();
      })
      .catch(function () {
        setStatus('Gagal mengirim. Periksa koneksi internet lalu coba lagi.', 'error');
      })
      .then(function () {
        if (tombol) { tombol.disabled = false; tombol.textContent = 'Kirim'; }
      });
  });
})();
