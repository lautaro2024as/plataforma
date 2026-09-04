(() => {
  const root = document.querySelector('.omega-music-page');
  if (!root) return;

  const listUrl = root.dataset.listUrl;
  const uploadUrl = root.dataset.uploadUrl;
  const audio = document.getElementById('omega-pm-audio') || document.getElementById('music-audio');
  const listEl = document.getElementById('music-list');
  const titleEl = document.getElementById('music-title');
  const metaEl = document.getElementById('music-meta');
  const playBtn = document.getElementById('music-play');
  const progress = document.getElementById('music-progress');
  const currentEl = document.getElementById('music-current');
  const durationEl = document.getElementById('music-duration');
  const volume = document.getElementById('music-volume');
  const loopBtn = document.getElementById('music-loop');
  const eq = document.querySelector('.eq');
  const countEl = document.getElementById('music-count');
  const stateKey = 'omega_music_state_v2';
  let items = [];
  let index = Number(localStorage.getItem(stateKey + ':index') || 0);
  let loop = localStorage.getItem(stateKey + ':loop') === '1';

  const csrf = () => {
    const value = document.cookie.split('; ').find(x => x.startsWith('csrftoken='));
    return value ? decodeURIComponent(value.split('=').slice(1).join('=')) : '';
  };
  const fmt = s => {
    s = Number.isFinite(s) ? Math.max(0, s) : 0;
    return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  };
  const saveState = () => {
    localStorage.setItem(stateKey + ':index', String(index));
    localStorage.setItem(stateKey + ':loop', loop ? '1' : '0');
    localStorage.setItem(stateKey + ':volume', String(audio.volume));
    localStorage.setItem(stateKey + ':time', String(audio.currentTime || 0));
    localStorage.setItem(stateKey + ':playing', String(!audio.paused));
  };
  const setPlayingUI = () => {
    const playing = !audio.paused;
    playBtn.textContent = playing ? 'Ⅱ' : '▶';
    eq.classList.toggle('playing', playing);
  };
  const load = (i, autoplay = false) => {
    if (!items.length) return;
    index = (i + items.length) % items.length;
    const item = items[index];
    audio.src = item.url;
    audio.load();
    titleEl.textContent = item.name;
    metaEl.textContent = `${index + 1} / ${items.length} · OMEGA LOCAL AUDIO`;
    localStorage.setItem(stateKey + ':index', String(index));
    render();
    if (autoplay) audio.play().catch(() => setPlayingUI());
  };
  const render = () => {
    countEl.textContent = `${items.length} TRACK${items.length === 1 ? '' : 'S'}`;
    listEl.innerHTML = '';
    if (!items.length) {
      listEl.innerHTML = '<div class="empty">Todavía no hay música cargada.</div>';
      titleEl.textContent = 'Nada reproduciendo';
      return;
    }
    items.forEach((item, i) => {
      const row = document.createElement('div');
      row.className = 'track' + (i === index ? ' active' : '');
      row.innerHTML = `<button class="track-main" type="button"><strong></strong><small>TRACK ${String(i + 1).padStart(2, '0')}</small></button><button class="track-play" type="button">${i === index && !audio.paused ? 'Ⅱ' : '▶'}</button><button class="delete" type="button" title="Eliminar">✕</button>`;
      row.querySelector('.track-main strong').textContent = item.name;
      row.querySelector('.track-main').onclick = () => load(i, true);
      row.querySelector('.track-play').onclick = () => {
        if (i !== index) return load(i, true);
        audio.paused ? audio.play() : audio.pause();
      };
      row.querySelector('.delete').onclick = async () => {
        if (!confirm(`Eliminar "${item.name}" de la biblioteca?`)) return;
        const r = await fetch(`/admin/omega/music/delete/${encodeURIComponent(item.id)}/`, {method: 'POST', headers: {'X-CSRFToken': csrf()}});
        if (r.ok) {
          items = items.filter(x => x.id !== item.id);
          if (index >= items.length) index = Math.max(0, items.length - 1);
          if (items.length) load(index);
          else { audio.removeAttribute('src'); audio.load(); localStorage.removeItem(stateKey + ':playing'); }
          render();
        }
      };
      listEl.appendChild(row);
    });
  };
  const refresh = async () => {
    try {
      const r = await fetch(listUrl, {cache: 'no-store'});
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || 'No autorizado');
      items = data.items || [];
      render();
      if (items.length && !audio.src) load(Math.min(index, items.length - 1));
    } catch (e) { listEl.innerHTML = `<div class="empty">${e.message}</div>`; }
  };

  volume.value = localStorage.getItem(stateKey + ':volume') || '0.75';
  audio.volume = Number(volume.value);
  audio.loop = loop;
  loopBtn.classList.toggle('on', loop);
  loopBtn.textContent = loop ? 'LOOP ON' : 'LOOP OFF';
  volume.oninput = () => { audio.volume = Number(volume.value); saveState(); };
  playBtn.onclick = () => items.length ? (audio.paused ? audio.play() : audio.pause()) : document.getElementById('music-file').click();
  document.getElementById('music-prev').onclick = () => load(index - 1, true);
  document.getElementById('music-next').onclick = () => load(index + 1, true);
  loopBtn.onclick = () => { loop = !loop; audio.loop = loop; loopBtn.classList.toggle('on', loop); loopBtn.textContent = loop ? 'LOOP ON' : 'LOOP OFF'; saveState(); };
  audio.addEventListener('play', setPlayingUI);
  audio.addEventListener('pause', setPlayingUI);
  audio.addEventListener('timeupdate', () => { currentEl.textContent = fmt(audio.currentTime); if (audio.duration) progress.value = String((audio.currentTime / audio.duration) * 100); saveState(); });
  audio.addEventListener('loadedmetadata', () => { durationEl.textContent = fmt(audio.duration); });
  audio.addEventListener('ended', () => { if (!audio.loop) load(index + 1, true); });
  progress.oninput = () => { if (audio.duration) audio.currentTime = (Number(progress.value) / 100) * audio.duration; };

  const fileInput = document.getElementById('music-file');
  document.getElementById('music-add').onclick = () => fileInput.click();
  fileInput.onchange = async () => {
    const files = [...fileInput.files];
    for (const file of files) {
      const fd = new FormData(); fd.append('file', file);
      const r = await fetch(uploadUrl, {method: 'POST', body: fd, headers: {'X-CSRFToken': csrf()}});
      if (!r.ok) { let msg = 'No se pudo subir el archivo.'; try { msg = (await r.json()).detail || msg; } catch (_) {} alert(msg); continue; }
      const data = await r.json(); items.push(data.item);
    }
    render();
    if (items.length && !audio.src) load(0);
    fileInput.value = '';
  };

  refresh();
})();
