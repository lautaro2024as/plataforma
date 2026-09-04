(() => {
  const stage = document.getElementById('omega-stage');
  if (!stage || stage.dataset.omegaLite === '1') return;
  stage.dataset.omegaLite = '1';

  const canvas = document.createElement('canvas');
  canvas.id = 'omega-lite-canvas';
  const ctx = canvas.getContext('2d', { alpha: false });
  stage.replaceChildren(canvas);

  const overlay = document.createElement('div');
  overlay.id = 'omega-lite-overlay';
  overlay.innerHTML = '<div class="omega-lite-vignette"></div><div class="omega-lite-scan"></div><div class="omega-lite-rain"></div><div class="omega-lite-clock"></div><div class="omega-lite-note">OMEGA LITE // WALLPAPER RENDER</div>';
  stage.appendChild(overlay);

  const rainHost = overlay.querySelector('.omega-lite-rain');
  const clock = overlay.querySelector('.omega-lite-clock');
  const state = { image: null, mouseX: 0, mouseY: 0, targetX: 0, targetY: 0 };

  for (let i = 0; i < 56; i += 1) {
    const d = document.createElement('i');
    d.className = 'omega-lite-drop';
    d.style.left = `${Math.random() * 100}%`;
    d.style.height = `${36 + Math.random() * 100}px`;
    d.style.opacity = `${0.08 + Math.random() * 0.25}`;
    d.style.animationDuration = `${0.8 + Math.random() * 1.6}s`;
    d.style.animationDelay = `${-Math.random() * 2.5}s`;
    rainHost.appendChild(d);
  }
  for (let i = 0; i < 24; i += 1) {
    const p = document.createElement('i');
    p.className = 'omega-lite-particle';
    p.style.left = `${5 + Math.random() * 90}%`;
    p.style.top = `${5 + Math.random() * 90}%`;
    p.style.setProperty('--px', `${Math.round(Math.random() * 26 - 13)}px`);
    p.style.setProperty('--py', `${Math.round(Math.random() * 22 - 11)}px`);
    p.style.animationDuration = `${4 + Math.random() * 6}s`;
    p.style.animationDelay = `${-Math.random() * 6}s`;
    rainHost.appendChild(p);
  }

  function resize() {
    const rect = stage.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    canvas.width = Math.max(1, Math.round(rect.width * dpr));
    canvas.height = Math.max(1, Math.round(rect.height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function drawFallback(w, h) {
    const g = ctx.createLinearGradient(0, 0, w, h);
    g.addColorStop(0, '#02040c');
    g.addColorStop(.45, '#12071f');
    g.addColorStop(1, '#050817');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = 'rgba(23,234,255,.09)';
    for (let x = 0; x < w; x += 80) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
    for (let y = 0; y < h; y += 54) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
    const rg = ctx.createRadialGradient(w * .55, h * .48, 0, w * .55, h * .48, Math.max(w, h) * .55);
    rg.addColorStop(0, 'rgba(255,50,230,.16)');
    rg.addColorStop(1, 'rgba(255,50,230,0)');
    ctx.fillStyle = rg;
    ctx.fillRect(0, 0, w, h);
  }

  function draw() {
    const rect = stage.getBoundingClientRect();
    const w = rect.width;
    const h = rect.height;
    if (!w || !h) return;
    ctx.clearRect(0, 0, w, h);
    if (!state.image) drawFallback(w, h);
    else {
      const img = state.image;
      const cover = Math.max(w / img.width, h / img.height);
      const dw = img.width * cover * 1.04;
      const dh = img.height * cover * 1.04;
      state.mouseX += (state.targetX - state.mouseX) * .045;
      state.mouseY += (state.targetY - state.mouseY) * .045;
      const t = performance.now() / 1000;
      const swayX = Math.sin(t * .18) * 3.0;
      const swayY = Math.sin(t * .22) * 2.0;
      const x = (w - dw) / 2 + state.mouseX * 12 + swayX;
      const y = (h - dh) / 2 + state.mouseY * 8 + swayY;
      ctx.drawImage(img, x, y, dw, dh);
    }
    requestAnimationFrame(draw);
  }

  async function loadWallpaper() {
    try {
      const response = await fetch('/admin/omega/wallpapers/list/', { credentials: 'same-origin', cache: 'no-store' });
      if (!response.ok) return;
      const data = await response.json();
      const item = (data.items || []).find(x => x.source === 'portable' && x.kind === 'scene' && /^portable-[^\\/]+$/.test(x.id));
      if (!item) return;
      const img = new Image();
      img.decoding = 'async';
      img.src = `/admin/omega/wallpapers/render/${encodeURIComponent(item.id)}/?t=${Date.now()}`;
      img.onload = () => { state.image = img; clock.textContent = 'OMEGA // 00:00:00'; };
    } catch (err) {
      console.warn('OMEGA Lite Engine:', err);
    }
  }

  stage.addEventListener('pointermove', (event) => {
    const rect = stage.getBoundingClientRect();
    state.targetX = ((event.clientX - rect.left) / rect.width - .5);
    state.targetY = ((event.clientY - rect.top) / rect.height - .5);
  }, { passive: true });

  function updateClock() {
    clock.textContent = `OMEGA // ${new Date().toLocaleTimeString('es-AR', { hour12: false })}`;
  }

  resize();
  window.addEventListener('resize', resize, { passive: true });
  updateClock();
  setInterval(updateClock, 1000);
  loadWallpaper();
  requestAnimationFrame(draw);
})();
