(() => {
  if (window.__omegaPersistentMusicLoaded) return;
  window.__omegaPersistentMusicLoaded = true;

  const STATE = 'omega_music_state_v3';
  const listUrl = '/admin/omega/music/list/';
  const streamBase = '/admin/omega/music/stream/';

  const make = (tag, cls, text) => {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (text !== undefined) el.textContent = text;
    return el;
  };

  const bar = make('div', 'omega-persistent-music');
  bar.setAttribute('aria-label', 'OMEGA Music Core');
  bar.innerHTML = `
    <div class="omega-pm-status"><span class="omega-pm-dot"></span><div><b id="omega-pm-title">MUSIC CORE</b><small id="omega-pm-meta">Sin música seleccionada</small></div></div>
    <div class="omega-pm-controls">
      <button id="omega-pm-prev" type="button" title="Anterior">◀◀</button>
      <button id="omega-pm-play" type="button" title="Reproducir">▶</button>
      <button id="omega-pm-next" type="button" title="Siguiente">▶▶</button>
    </div>
    <div class="omega-pm-progress"><span id="omega-pm-cur">0:00</span><input id="omega-pm-range" type="range" min="0" max="1000" value="0" step="1" aria-label="Posición de la música"><span id="omega-pm-dur">0:00</span></div>
    <label class="omega-pm-volume">VOL <input id="omega-pm-vol" type="range" min="0" max="1" step="0.01" value="0.75"></label>
    <audio id="omega-pm-audio" preload="auto"></audio>
  `;
  document.body.appendChild(bar);

  const audio = bar.querySelector('#omega-pm-audio');
  const title = bar.querySelector('#omega-pm-title');
  const meta = bar.querySelector('#omega-pm-meta');
  const playBtn = bar.querySelector('#omega-pm-play');
  const prevBtn = bar.querySelector('#omega-pm-prev');
  const nextBtn = bar.querySelector('#omega-pm-next');
  const range = bar.querySelector('#omega-pm-range');
  const cur = bar.querySelector('#omega-pm-cur');
  const dur = bar.querySelector('#omega-pm-dur');
  const vol = bar.querySelector('#omega-pm-vol');

  let items = [];
  let index = Number(localStorage.getItem(STATE + ':index') || 0);
  let restoring = true;

  const csrf = () => {
    const value = document.cookie.split('; ').find(x => x.startsWith('csrftoken='));
    return value ? decodeURIComponent(value.split('=').slice(1).join('=')) : '';
  };
  const fmt = s => {
    s = Number.isFinite(s) ? Math.max(0, s) : 0;
    return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  };
  const save = () => {
    localStorage.setItem(STATE + ':index', String(index));
    if (Number.isFinite(audio.currentTime)) localStorage.setItem(STATE + ':time', String(audio.currentTime));
    localStorage.setItem(STATE + ':volume', String(audio.volume));
    localStorage.setItem(STATE + ':playing', String(!audio.paused));
  };
  const ui = () => {
    const playing = !audio.paused;
    playBtn.textContent = playing ? 'Ⅱ' : '▶';
    bar.classList.toggle('playing', playing);
    localStorage.setItem(STATE + ':playing', String(playing));
  };

  const load = (i, autoplay = false, shouldRestore = false) => {
    if (!items.length) return;
    index = (i + items.length) % items.length;
    const item = items[index];
    const wanted = shouldRestore ? Number(localStorage.getItem(STATE + ':time') || 0) : 0;
    restoring = true;
    audio.src = `${streamBase}${encodeURIComponent(item.id)}/`;
    audio.load();
    title.textContent = item.name;
    meta.textContent = `${index + 1} / ${items.length} · OMEGA LOCAL AUDIO`;
    const apply = () => {
      if (shouldRestore && wanted > 0 && Number.isFinite(audio.duration) && wanted < audio.duration - 0.2) {
        try { audio.currentTime = wanted; } catch (_) {}
      }
      restoring = false;
      dur.textContent = fmt(audio.duration);
      if (autoplay) audio.play().catch(() => {});
      save();
      audio.removeEventListener('loadedmetadata', apply);
      audio.removeEventListener('canplay', apply);
    };
    audio.addEventListener('loadedmetadata', apply);
    audio.addEventListener('canplay', apply);
  };

  async function refresh() {
    try {
      const r = await fetch(listUrl, { cache: 'no-store', credentials: 'same-origin' });
      const data = await r.json();
      if (!r.ok) return;
      items = data.items || [];
      if (!items.length) {
        title.textContent = 'MUSIC CORE';
        meta.textContent = 'Sin música seleccionada';
        return;
      }
      index = Math.min(Math.max(index, 0), items.length - 1);
      const currentSrc = audio.getAttribute('src') || '';
      const currentId = items[index] && String(items[index].id);
      const expected = currentId ? `${streamBase}${encodeURIComponent(currentId)}/` : '';
      const shouldPlay = localStorage.getItem(STATE + ':playing') === 'true';
      if (!currentSrc || currentSrc !== expected) load(index, shouldPlay, true);
    } catch (_) {}
  }

  const savedVol = Number(localStorage.getItem(STATE + ':volume') || 0.75);
  audio.volume = Number.isFinite(savedVol) ? Math.min(1, Math.max(0, savedVol)) : 0.75;
  vol.value = String(audio.volume);

  playBtn.addEventListener('click', () => {
    if (!items.length) return;
    if (audio.paused) audio.play().catch(() => {}); else audio.pause();
  });
  prevBtn.addEventListener('click', () => load(index - 1, true, false));
  nextBtn.addEventListener('click', () => load(index + 1, true, false));
  vol.addEventListener('input', () => { audio.volume = Number(vol.value); save(); });

  const seek = () => {
    const duration = audio.duration;
    if (!Number.isFinite(duration) || duration <= 0) return;
    const position = (Number(range.value) / 1000) * duration;
    try { audio.currentTime = Math.max(0, Math.min(position, duration)); } catch (_) {}
    save();
  };
  range.addEventListener('input', seek);
  range.addEventListener('change', seek);

  audio.addEventListener('play', ui);
  audio.addEventListener('pause', () => { ui(); save(); });
  audio.addEventListener('timeupdate', () => {
    cur.textContent = fmt(audio.currentTime);
    if (Number.isFinite(audio.duration) && audio.duration > 0) {
      range.value = String(Math.round((audio.currentTime / audio.duration) * 1000));
    }
    if (!restoring) save();
  });
  audio.addEventListener('loadedmetadata', () => { dur.textContent = fmt(audio.duration); });
  audio.addEventListener('ended', () => load(index + 1, true, false));
  window.addEventListener('pagehide', save);
  document.addEventListener('visibilitychange', () => { if (document.hidden) save(); });

  // Navegación GET dentro del admin: cambia solo #content y conserva el audio vivo.
  document.addEventListener('click', async (event) => {
    const link = event.target.closest('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0) return;
    if (link.target && link.target !== '_self') return;
    if (link.hasAttribute('download')) return;
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const url = new URL(link.href, location.href);
    if (url.origin !== location.origin || !url.pathname.startsWith('/admin/')) return;
    if (url.pathname === '/admin/logout/' || url.pathname.includes('/password/')) return;
    if (link.closest('form')) return;

    event.preventDefault();
    try {
      const response = await fetch(url.href, {
        credentials: 'same-origin',
        cache: 'no-store',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const html = await response.text();
      const doc = new DOMParser().parseFromString(html, 'text/html');
      const incoming = doc.querySelector('#content');
      const current = document.querySelector('#content');
      if (!incoming || !current) { location.href = url.href; return; }
      current.replaceWith(incoming);
      document.title = doc.title || document.title;
      history.pushState({ omegaAjax: true }, '', url.href);
      window.scrollTo(0, 0);
    } catch (_) {
      location.href = url.href;
    }
  });

  window.addEventListener('popstate', () => location.reload());
  refresh();
})();
