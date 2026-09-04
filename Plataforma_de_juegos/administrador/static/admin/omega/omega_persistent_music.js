(() => {
  if (window.__omegaPersistentMusicLoaded) return;
  window.__omegaPersistentMusicLoaded = true;

  const STATE = 'omega_music_state_v2';
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
    <div class="omega-pm-progress"><span id="omega-pm-cur">0:00</span><input id="omega-pm-range" type="range" min="0" max="100" value="0"><span id="omega-pm-dur">0:00</span></div>
    <label class="omega-pm-volume">VOL <input id="omega-pm-vol" type="range" min="0" max="1" step="0.01" value="0.75"></label>
    <audio id="omega-pm-audio" preload="metadata"></audio>
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
    localStorage.setItem(STATE + ':time', String(audio.currentTime || 0));
    localStorage.setItem(STATE + ':volume', String(audio.volume));
    localStorage.setItem(STATE + ':playing', String(!audio.paused));
  };
  const ui = () => {
    const playing = !audio.paused;
    playBtn.textContent = playing ? 'Ⅱ' : '▶';
    bar.classList.toggle('playing', playing);
    localStorage.setItem(STATE + ':playing', String(playing));
  };
  const load = (i, autoplay = false, restoreTime = false) => {
    if (!items.length) return;
    index = (i + items.length) % items.length;
    const item = items[index];
    audio.src = `${streamBase}${encodeURIComponent(item.id)}/`;
    audio.load();
    title.textContent = item.name;
    meta.textContent = `${index + 1} / ${items.length} · OMEGA LOCAL AUDIO`;
    localStorage.setItem(STATE + ':index', String(index));
    const wanted = restoreTime ? Number(localStorage.getItem(STATE + ':time') || 0) : 0;
    const onMeta = () => {
      if (wanted > 0 && wanted < audio.duration) audio.currentTime = wanted;
      audio.removeEventListener('loadedmetadata', onMeta);
      if (autoplay) audio.play().catch(() => {});
      save();
    };
    audio.addEventListener('loadedmetadata', onMeta);
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
      load(index, false, true);
      const shouldPlay = localStorage.getItem(STATE + ':playing') === 'true';
      if (shouldPlay) {
        audio.play().catch(() => {
          const once = () => { audio.play().catch(() => {}); document.removeEventListener('click', once); };
          document.addEventListener('click', once, { once: true });
        });
      }
      restoring = false;
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
  range.addEventListener('input', () => { if (audio.duration) audio.currentTime = (Number(range.value) / 100) * audio.duration; });
  audio.addEventListener('play', ui);
  audio.addEventListener('pause', ui);
  audio.addEventListener('timeupdate', () => {
    cur.textContent = fmt(audio.currentTime);
    if (audio.duration) range.value = String((audio.currentTime / audio.duration) * 100);
    if (!restoring) save();
  });
  audio.addEventListener('loadedmetadata', () => { dur.textContent = fmt(audio.duration); });
  audio.addEventListener('ended', () => load(index + 1, true, false));
  window.addEventListener('pagehide', save);
  document.addEventListener('visibilitychange', () => { if (document.hidden) save(); });

  refresh();
})();
