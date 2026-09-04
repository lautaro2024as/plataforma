(() => {
  const root=document.getElementById('omega-deck');
  if(!root)return;
  const endpoint=root.dataset.statsUrl;
  const historyCpu=[],historyRam=[];
  const $=id=>document.getElementById(id);
  const setText=(id,v)=>{const e=$(id);if(e)e.textContent=v;};
  const setBar=(id,v)=>{const e=$(id);if(e)e.style.width=`${Math.max(0,Math.min(100,Number(v)||0))}%`;};
  function linePoints(values){const n=Math.max(values.length,2);return values.map((v,i)=>`${Math.round(i*900/(n-1))},${Math.round(202-(Math.max(0,Math.min(100,v))*1.62))}`).join(' ');}
  function push(arr,v){arr.push(Number(v)||0);if(arr.length>32)arr.shift();}
  function chart(){const c=$('cpu-line'),r=$('ram-line');if(c&&historyCpu.length>1)c.setAttribute('points',linePoints(historyCpu));if(r&&historyRam.length>1)r.setAttribute('points',linePoints(historyRam));}
  function feed(label,text,ok=true){const f=$('omega-feed');if(!f)return;const row=document.createElement('div');row.innerHTML=`<b>${label}</b><span>${text}</span><i>${ok?'✓':'!'}</i>`;f.prepend(row);while(f.children.length>5)f.removeChild(f.lastElementChild);}
  async function refresh(){try{const r=await fetch(endpoint,{credentials:'same-origin',cache:'no-store'});if(!r.ok)throw new Error(`HTTP ${r.status}`);const d=await r.json();
    setText('db-state',d.db);setText('db-state-2',d.db);setText('server-state','ONLINE');setText('os-state',d.os);setText('uptime-state',d.uptime);setText('pc-host',`HOST: ${d.hostname}`);setText('net-traffic',`NET: ↑${d.net_sent_mb} MB ↓${d.net_recv_mb} MB`);
    setText('stat-games',d.games);setText('stat-published',d.published);setText('stat-malware',d.malware);setText('stat-licenses',d.licenses);setText('side-games',d.games);setText('side-malware',d.malware);setText('side-licenses',d.licenses);setText('side-users',d.users);
    setText('cpu-value',`${d.cpu}%`);setText('ram-value',`${d.ram}%`);setText('disk-value',`${d.disk}%`);setText('legend-cpu',`${d.cpu}%`);setText('legend-ram',`${d.ram}%`);setText('legend-db',d.db_ms==null?'OFF':`${d.db_ms} ms`);setBar('cpu-bar',d.cpu);setBar('ram-bar',d.ram);setBar('disk-bar',d.disk);
    push(historyCpu,d.cpu);push(historyRam,d.ram);chart();setText('footer-status',d.cpu>92||d.ram>94||d.disk>96?'WARNING':'HEALTHY');feed('PC',`CPU ${d.cpu}% // RAM ${d.ram}% // DISK ${d.disk}%`);
  }catch(err){setText('server-state','DEGRADED');setText('footer-status','DEGRADED');feed('ERR',`Telemetría no disponible: ${err.message}`,false);}}
  function visual(){const stage=$('omega-stage');if(!stage)return;let mx=0,my=0;stage.addEventListener('pointermove',e=>{const r=stage.getBoundingClientRect();mx=(e.clientX-r.left)/r.width-.5;my=(e.clientY-r.top)/r.height-.5;stage.style.setProperty('--mx',mx.toFixed(3));stage.style.setProperty('--my',my.toFixed(3));});stage.addEventListener('pointerleave',()=>{stage.style.setProperty('--mx','0');stage.style.setProperty('--my','0');});stage.addEventListener('mouseenter',()=>stage.classList.add('operator-hover'));stage.addEventListener('mouseleave',()=>stage.classList.remove('operator-hover'));}
  refresh();setInterval(refresh,2000);visual();
})();
