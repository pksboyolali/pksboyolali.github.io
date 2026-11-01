// Pencarian memakai Pagefind (indeks dibuat otomatis saat publikasi)
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const box = document.getElementById('search-results');
const empty = document.getElementById('search-empty');
const title = document.getElementById('search-title');
const input = document.getElementById('search-box-input');
const base = new URL('../', import.meta.url);
const q = (new URLSearchParams(location.search).get('q') || '').trim();
if (input) input.value = q;
const fmt = (iso) => { const d = new Date(iso); return isNaN(d) ? '' : new Intl.DateTimeFormat('id-ID', {day:'numeric', month:'long', year:'numeric', timeZone:'Asia/Jakarta'}).format(d); };

if (!q) {
  box.innerHTML = '<p>Ketik kata kunci pada kotak pencarian (ikon kaca pembesar di menu).</p>';
} else {
  title.innerHTML = '<span class="text-pks-orange">Hasil pencarian kata kunci </span><span class="text-pks-black! font-semibold">' + esc(q) + '</span>';
  try {
    const pf = await import(new URL('pagefind/pagefind.js', base).href);
    const res = await pf.search(q);
    if (!res.results.length) {
      box.innerHTML = '';
      empty.hidden = false;
    } else {
      const items = await Promise.all(res.results.slice(0, 30).map((r) => r.data()));
      const thumb = new URL('images/thumbnail-default.png', base).href;
      box.innerHTML = items.map((d) => `
        <article class="mb-2 flex flex-col md:flex-row items-start group bg-pks-white border border-pks-black-50 rounded-2xl shadow-lg">
          <a href="${esc(d.url)}" class="block w-full md:w-auto md:inline-block shrink-0">
            <img src="${esc(d.meta.image || thumb)}" alt="" loading="lazy" class="w-full md:w-60 h-60 md:h-40 object-cover rounded-2xl shrink-0">
          </a>
          <div class="entry-content p-4">
            <a href="${esc(d.url)}" class="no-underline! mb-2 block"><h2 class="entry-title font-semibold text-xl text-pks-black group-hover:text-pks-orange transition-colors duration-300">${esc(d.meta.title)}</h2></a>
            <div class="entry-meta text-xs text-pks-black-300">${esc(fmt(d.meta.date))}</div>
          </div>
        </article>`).join('');
    }
  } catch (e) {
    box.innerHTML = '<p>Pencarian akan aktif setelah situs dipublikasikan (indeks pencarian dibuat saat publikasi).</p>';
  }
}
