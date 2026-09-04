(() => {
  const root = document.querySelector('.omega-music-page');
  if (!root || root.dataset.omegaMusicInitialized === '1') return;
  root.dataset.omegaMusicInitialized = '1';

  const listUrl = root.dataset.listUrl;
  const uploadUrl = root.dataset.uploadUrl;
  const deleteBase = root.dataset.deleteBase || '/admin/omega/music/delete/';
  const audio = document.getElementById('music-audio');
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
  const fileInput = document.getElementById('music-file');
  const statusEl = document.getElementById('music-upload-status');
  const stateKey = 'omega_music_state_v4';

  let items = [];
  let index = Number(localStorage.getItem(stateKey + ':index') || 0);
  let loop = localStorage.getItem(stateKey + ':loop') === '1';
  let uploadBusy = false;

  const csrf = () => {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta?.content) return meta.content;
    const input = document.querySelector('#music-upload-form input[name="csrfmiddlewaretoken"]');
    if (input?.value) return input.value;
    const cookie = document.cookie.split('; ').find(x => x.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=').slice(1).join('=')) : '';
  };
  const fmt = s => {
    s = Number.isFinite(s) ? Math.max(0, s) : 0;
    return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
  };
  const setStatus = (text, error = false) => {
    if (!statusEl) return;
    statusEl.textContent = text || '';
    statusEl.style.color = error ? '#ff7898' : '#85ffbd';
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
    eq?.classList.toggle('playing', playing);
  };
  const load = (i, autoplay = false, restoreTime = false) => {
    if (!items.length) return;
    index = (i + items.length) % items.length;
    const item = items[index];
    const wanted = restoreTime ? Number(localStorage.getItem(stateKey + ':time') || 0) : 0;
    audio.src = item.url;
    audio.load();
    titleEl.textContent = item.name;
    metaEl.textContent = `${index + 1} / ${items.length} · OMEGA LOCAL AUDIO`;
    localStorage.setItem(stateKey + ':index', String(index));

    const onMeta = () => {
      if (restoreTime && wanted > 0 && Number.isFinite(audio.duration) && wanted < audio.duration - 0.2) {
        try { audio.currentTime = wanted; } catch (_) {}
      }
      durationEl.textContent = fmt(audio.duration);
      saveState();
      audio.removeEventListener('loadedmetadata', onMeta);
    };
    audio.addEventListener('loadedmetadata', onMeta);
    if (autoplay) audio.play().catch(() => setPlayingUI());
    render();
  };
  const render = () => {
    countEl.textContent = `${items.length} TRACK${items.length === 1 ? '' : 'S'}`;
    listEl.innerHTML = '';
    if (!items.length) {
      listEl.innerHTML = '<div class="empty">Todavía no hay música cargada.</div>';
      titleEl.textContent = 'Nada reproduciendo';
      metaEl.textContent = 'Agregá música desde tu PC.';
      return;
    }
    items.forEach((item, i) => {
      const row = document.createElement('div');
      row.className = 'track' + (i === index ? ' active' : '');
      const main = document.createElement('button');
      main.className = 'track-main'; main.type = 'button';
      const strong = document.createElement('strong'); strong.textContent = item.name;
      const small = document.createElement('small'); small.textContent = `TRACK ${String(i + 1).padStart(2, '0')}`;
      main.append(strong, small);
      const play = document.createElement('button'); play.className = 'track-play'; play.type = 'button'; play.textContent = i === index && !audio.paused ? 'Ⅱ' : '▶';
      const del = document.createElement('button'); del.className = 'delete'; del.type = 'button'; del.title = 'Eliminar'; del.textContent = '✕';
      main.onclick = () => load(i, true, false);
      play.onclick = () => {
        if (i !== index) return load(i, true, false);
        audio.paused ? audio.play().catch(() => {}) : audio.pause();
      };
      del.onclick = async () => {
        if (!confirm(`Eliminar "${item.name}" de la biblioteca?`)) return;
        try {
          const response = await fetch(`${deleteBase}${encodeURIComponent(item.id)}/`, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}
          });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          items = items.filter(x => String(x.id) !== String(item.id));
          if (!items.length) {
            index = 0; audio.removeAttribute('src'); audio.load();
          } else if (index >= items.length) {
            index = items.length - 1; load(index, false, false);
          }
          render();
        } catch (e) { alert(`No se pudo eliminar: ${e.message}`); }
      };
      row.append(main, play, del);
      listEl.appendChild(row);
    });
  };

  const refresh = async () => {
    try {
      const r = await fetch(listUrl, {cache: 'no-store', credentials: 'same-origin', headers: {'Accept': 'application/json'}});
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
      items = Array.isArray(data.items) ? data.items : [];
      if (index >= items.length) index = Math.max(0, items.length - 1);
      render();
      if (items.length && !audio.src) load(index, false, true);
    } catch (e) {
      listEl.innerHTML = `<div class="empty">No se pudo cargar la biblioteca: ${e.message}</div>`;
    }
  };

  const uploadFiles = async files => {
    if (uploadBusy) return;
    const selected = [...files].filter(f => /\.(mp3|wav|ogg|m4a|aac|flac|webm)$/i.test(f.name));
    if (!selected.length) { setStatus('Elegí archivos de audio válidos.', true); return; }
    uploadBusy = true;
    setStatus(`SUBIENDO ${selected.length} PISTA(S)...`);
    try {
      let added = 0;
      for (const file of selected) {
        const fd = new FormData();
        fd.append('file', file, file.name);
        const r = await fetch(uploadUrl, {
          method: 'POST', body: fd, credentials: 'same-origin',
          headers: {'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json'}
        });
        const text = await r.text();
        let data = {};
        try { data = JSON.parse(text); } catch (_) {}
        if (!r.ok) throw new Error(data.detail || text.slice(0, 300) || `HTTP ${r.status}`);
        if (data.item) { items.push(data.item); added += 1; }
        setStatus(`SUBIDA: ${file.name}`);
      }
      render();
      if (items.length && !audio.src) load(items.length - added, false, false);
      setStatus(`✓ ${added} PISTA(S) AGREGADA(S) CORRECTAMENTE`);
    } catch (e) {
      setStatus(`ERROR AL AGREGAR MÚSICA: ${e.message}`, true);
    } finally {
      uploadBusy = false;
      fileInput.value = '';
    }
  };

  const savedVolume = Number(localStorage.getItem(stateKey + ':volume') || 0.75);
  audio.volume = Number.isFinite(savedVolume) ? Math.min(1, Math.max(0, savedVolume)) : 0.75;
  volume.value = String(audio.volume);
  audio.loop = loop;
  loopBtn.classList.toggle('on', loop);
  loopBtn.textContent = loop ? 'LOOP ON' : 'LOOP OFF';

  volume.oninput = () => { audio.volume = Number(volume.value); saveState(); };
  playBtn.onclick = () => {
    if (!items.length) return fileInput.click();
    if (audio.paused) audio.play().catch(() => {}); else audio.pause();
  };
  document.getElementById('music-prev').onclick = () => load(index - 1, true, false);
  document.getElementById('music-next').onclick = () => load(index + 1, true, false);
  loopBtn.onclick = () => { loop = !loop; audio.loop = loop; loopBtn.classList.toggle('on', loop); loopBtn.textContent = loop ? 'LOOP ON' : 'LOOP OFF'; saveState(); };
  progress.oninput = () => { if (Number.isFinite(audio.duration) && audio.duration > 0) audio.currentTime = (Number(progress.value) / 100) * audio.duration; };

  audio.addEventListener('play', setPlayingUI);
  audio.addEventListener('pause', () => { setPlayingUI(); saveState(); });
  audio.addEventListener('timeupdate', () => {
    currentEl.textContent = fmt(audio.currentTime);
    if (Number.isFinite(audio.duration) && audio.duration > 0) progress.value = String((audio.currentTime / audio.duration) * 100);
    saveState();
  });
  audio.addEventListener('loadedmetadata', () => { durationEl.textContent = fmt(audio.duration); });
  audio.addEventListener('ended', () => { if (!audio.loop) load(index + 1, true, false); });
  window.addEventListener('pagehide', saveState);

  if (fileInput) fileInput.addEventListener('change', () => uploadFiles(fileInput.files));
  document.getElementById('music-add')?.addEventListener('click', () => fileInput?.click());

  refresh();
})();
