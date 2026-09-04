(() => {
  const root = document.getElementById('omega-deck');
  if (!root) return;
  const endpoint = root.dataset.statsUrl;
  const historyCpu = [];
  const historyRam = [];

  const $ = (id) => document.getElementById(id);
  const setText = (id, value) => { const el = $(id); if (el) el.textContent = value; };
  const setBar = (id, value) => { const el = $(id); if (el) el.style.width = `${Math.max(0, Math.min(100, value))}%`; };

  function linePoints(values) {
    const n = Math.max(values.length, 2);
    return values.map((v, i) => `${Math.round(i * 900 / (n - 1))},${Math.round(210 - (Math.max(0, Math.min(100, v)) * 1.65) - 8)}`).join(' ');
  }

  function pushHistory(arr, value) {
    arr.push(Number(value) || 0);
    if (arr.length > 28) arr.shift();
  }

  function updateChart() {
    const cpu = $('cpu-line');
    const ram = $('ram-line');
    if (cpu && historyCpu.length > 1) cpu.setAttribute('points', linePoints(historyCpu));
    if (ram && historyRam.length > 1) ram.setAttribute('points', linePoints(historyRam));
  }

  function addFeed(label, text, ok = true) {
    const feed = $('omega-feed');
    if (!feed) return;
    const row = document.createElement('div');
    row.innerHTML = `<b>${label}</b><span>${text}</span><i>${ok ? '✓' : '!'}</i>`;
    feed.prepend(row);
    while (feed.children.length > 5) feed.removeChild(feed.lastElementChild);
  }

  async function refresh() {
    try {
      const response = await fetch(endpoint, { credentials: 'same-origin', cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const d = await response.json();

      setText('db-state', d.db);
      setText('db-state-2', d.db);
      setText('os-state', d.os);
      setText('uptime-state', d.uptime);
      setText('pc-host', `HOST: ${d.hostname}`);
      setText('net-traffic', `NET: ↑${d.net_sent_mb} MB ↓${d.net_recv_mb} MB`);
      setText('stat-games', d.games);
      setText('stat-published', d.published);
      setText('stat-malware', d.malware);
      setText('stat-licenses', d.licenses);
      setText('side-games', d.games);
      setText('side-malware', d.malware);
      setText('side-licenses', d.licenses);
      setText('side-users', d.users);
      setText('cpu-value', `${d.cpu}%`);
      setText('ram-value', `${d.ram}%`);
      setText('disk-value', `${d.disk}%`);
      setText('legend-cpu', `${d.cpu}%`);
      setText('legend-ram', `${d.ram}%`);
      setText('legend-db', d.db_ms == null ? 'OFF' : `${d.db_ms} ms`);
      setBar('cpu-bar', d.cpu);
      setBar('ram-bar', d.ram);
      setBar('disk-bar', d.disk);

      pushHistory(historyCpu, d.cpu);
      pushHistory(historyRam, d.ram);
      updateChart();
      setText('footer-status', d.cpu > 92 || d.ram > 94 || d.disk > 96 ? 'WARNING' : 'HEALTHY');
      addFeed('PC', `CPU ${d.cpu}% // RAM ${d.ram}% // DISK ${d.disk}%`);
    } catch (err) {
      setText('server-state', 'DEGRADED');
      setText('footer-status', 'DEGRADED');
      addFeed('ERR', `Telemetría no disponible: ${err.message}`, false);
    }
  }

  function bindWallpaper() {
    const button = $('omega-wallpaper-open');
    if (!button) return;
    button.addEventListener('click', () => {
      alert('CONTROL DE WALLPAPER ENGINE: preparado para el controlador local de Windows. La selección se habilitará solo para el superusuario.');
    });
  }

  refresh();
  setInterval(refresh, 2000);
  bindWallpaper();
})();
