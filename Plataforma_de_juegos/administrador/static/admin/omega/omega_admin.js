(()=>{
  const BASE="/static/admin/omega/";
  const qsa=s=>[...document.querySelectorAll(s)];
  let actor,rain,hoverTimer;
  function layer(id){const e=document.createElement('div');e.id=id;document.body.prepend(e);return e}
  function build(){layer('omega-stage');layer('omega-grid');rain=layer('omega-rain');layer('omega-light');layer('omega-vignette');actor=layer('omega-actor')}
  async function character(){try{const r=await fetch(BASE+'omega_character.svg',{cache:'no-store'});if(!r.ok)throw Error();actor.innerHTML=await r.text();const svg=actor.querySelector('svg');if(svg){svg.setAttribute('aria-hidden','true');svg.style.pointerEvents='none'}const s=document.createElement('span');s.className='omega-smoke';actor.appendChild(s)}catch(e){actor.innerHTML=''}}
  function drops(){const f=document.createDocumentFragment();for(let i=0;i<190;i++){const d=document.createElement('i');d.className='omega-drop';d.style.left=Math.random()*100+'%';d.style.height=40+Math.random()*120+'px';d.style.opacity=(.10+Math.random()*.52).toFixed(2);d.style.setProperty('--rs',(0.42+Math.random()*1.15).toFixed(2)+'s');d.style.animationDelay=Math.random()*3+'s';f.appendChild(d)}rain.appendChild(f)}
  function mouse(e){const x=e.clientX/innerWidth-.5,y=e.clientY/innerHeight-.5;document.documentElement.style.setProperty('--ox',x*28+'px');document.documentElement.style.setProperty('--oy',y*18+'px');document.documentElement.style.setProperty('--ax',x*24+'px');document.documentElement.style.setProperty('--ay',y*12+'px');document.documentElement.style.setProperty('--at',x*4.5+'deg')}
  function react(on){document.body.classList.toggle('omega-reacting',on)}
  function playJuegos(){if(document.body.classList.contains('omega-playing'))return;document.body.classList.add('omega-playing');react(true);clearTimeout(hoverTimer);setTimeout(()=>{document.body.classList.remove('omega-playing');react(false)},1100)}
  function bind(){document.addEventListener('mousemove',mouse,{passive:true});const interactive=qsa('.module,.dashboard-module,.button,input[type="submit"],input[type="button"],#nav-sidebar a');interactive.forEach(el=>{el.addEventListener('mouseenter',()=>{clearTimeout(hoverTimer);react(true)});el.addEventListener('mouseleave',()=>{hoverTimer=setTimeout(()=>react(false),90)})});qsa('a,button,input[type="submit"],input[type="button"]').forEach(el=>{const t=((el.textContent||'')+' '+(el.getAttribute('href')||'')+' '+(el.getAttribute('value')||'')+' '+(el.getAttribute('aria-label')||'')).toLowerCase();if(t.includes('juego')||t.includes('juegos'))el.addEventListener('click',playJuegos)})}
  function loop(){let t=0;const tick=()=>{t+=.02;document.documentElement.style.setProperty('--pulse',(0.5+Math.sin(t)*.5).toFixed(3));requestAnimationFrame(tick)};tick()}
  async function start(){build();await character();drops();bind();loop()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();