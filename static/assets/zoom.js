/* Zoom gambar artikel.
   Meniru perilaku tema WordPress DPP PKS (pksejahtera):
   klik gambar -> gambar membesar mengapung di tengah layar dengan latar putih
   tembus pandang, keterangan gambar (figcaption) muncul di bawah, klik di mana
   saja atau tekan Esc untuk menutup. URL halaman tidak berubah.

   Pustaka medium-zoom dimuat lebih dulu (static/assets/vendor/medium-zoom.min.js). */
(function () {
  'use strict';

  function mulai() {
    var zoom = window.mediumZoom;
    if (typeof zoom !== 'function') return;          // pustaka gagal dimuat

    var wadah = document.getElementById('zoom-container');
    if (!wadah) return;

    // Gambar yang bisa di-zoom: isi artikel + gambar sampul
    var sasaran = '.pks-post-content img, .pks-post-featured-image img';
    if (!document.querySelector(sasaran)) return;    // tidak ada gambar, berhenti

    var ket = document.createElement('div');
    ket.className = 'zoom-caption';
    document.body.appendChild(ket);

    var z = zoom(sasaran, {
      container: wadah,
      margin: 24,
      background: '#FFFFFFDD',
      scrollOffset: 0
    });

    // Gambar hasil migrasi Blogger dibungkus tautan ke berkas gambarnya sendiri
    // (kebiasaan "lightbox" Blogger). Tanpa ini, klik gambar membuka berkas
    // gambar dan meninggalkan halaman artikel.
    var GAMBAR = /\.(jpe?g|png|gif|webp|avif|bmp)(\?|#|$)/i;
    document.querySelectorAll('.pks-post-content a, .pks-post-featured-image a').forEach(function (a) {
      if (!a.querySelector('img')) return;
      var href = a.getAttribute('href') || '';
      if (!GAMBAR.test(href)) return;                 // tautan biasa: biarkan
      a.addEventListener('click', function (e) { e.preventDefault(); });
    });

    // Klik di area gelap (wadah) menutup gambar
    wadah.addEventListener('click', function () {
      z.close();
      wadah.style.display = 'none';
    });

    z.on('open', function (e) {
      wadah.style.display = 'block';
      // Versi resolusi penuh (bila ada) dimuat diam-diam agar saat zoom tajam
      var src = e.target.getAttribute('data-zoom-src');
      if (src) { var pramuat = new Image(); pramuat.src = src; }
    });

    z.on('opened', function (e) {
      rapikanLapisan();
      var fig = e.target.closest('figure');
      var cap = fig ? fig.querySelector('figcaption') : null;
      if (cap && cap.textContent.trim()) {
        ket.textContent = cap.textContent.trim();
        ket.classList.add('zoom-caption--visible');
      }
    });

    z.on('close', function () {
      ket.classList.remove('zoom-caption--visible');
      wadah.style.display = 'none';
      rapikanLapisan();
    });

    // Pustaka kadang membuat lebih dari satu lapisan latar. Sisakan satu agar
    // latar tetap tembus pandang seperti tema WordPress, bukan putih pekat.
    function rapikanLapisan() {
      var lapisan = document.querySelectorAll('.medium-zoom-overlay');
      for (var i = 1; i < lapisan.length; i++) lapisan[i].remove();
    }

    // Esc ikut menutup (medium-zoom sudah menutup sendiri, ini menjaga wadah)
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') wadah.style.display = 'none';
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mulai);
  } else {
    mulai();
  }
})();
