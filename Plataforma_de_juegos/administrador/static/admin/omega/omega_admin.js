(()=>{
  const BASE="/static/admin/omega/";
  const qsa=s=>[...document.querySelectorAll(s)];
  let actor,rain,hoverTimer,modeTimer;

  function layer(id){const e=document.createElement('div');e.id=id;document.body.prepend(e);return e}
  function build(){layer('omega-stage');layer('omega-grid');rain=layer('omega-rain');layer('omega-light');layer('omega-vignette');actor=layer('omega-actor')}

  async function character(){
    try{
      const r=await fetch(BASE+'omega_character.svg',{cache:'no-store'});
      if(!r.ok)throw Error('character');
      actor.innerHTML=await r.text();
      const svg=actor.querySelector('svg');
      if(svg){svg.setAttribute('aria-hidden','true');svg.style.pointerEvents='none'}
      const smoke=document.createElement('span');
      smoke.className='omega-smoke';
      actor.appendChild(smoke);
    }catch(e){actor.innerHTML=''}
  }

  function drops(){
    const f=document.createDocumentFragment();
    for(let i=0;i<190;i++){
      const d=document.createElement('i');
      d.className='omega-drop';
      d.style.left=Math.random()*100+'%';
      d.style.height=40+Math.random()*120+'px';
      d.style.opacity=(.10+Math.random()*.52).toFixed(2);
      d.style.setProperty('--rs',(0.42+Math.random()*1.15).toFixed(2)+'s');
      d.style.animationDelay=Math.random()*3+'s';
      f.appendChild(d)
    }
    rain.appendChild(f)
  }

  function mouse(e){
    const x=e.clientX/innerWidth-.5;
    const y=e.clientY/innerHeight-.5;
    document.documentElement.style.setProperty('--ox',x*28+'px');
    document.documentElement.style.setProperty('--oy',y*18+'px');
    document.documentElement.style.setProperty('--ax',x*24+'px');
    document.documentElement.style.setProperty('--ay',y*12+'px');
    document.documentElement.style.setProperty('--at',x*4.5+'deg');
  }

  function react(on){document.body.classList.toggle('omega-reacting',on)}

  function clearMode(){
    document.body.classList.remove('omega-mode-look','omega-mode-smile','omega-mode-smoke');
    qsa('.omega-pose').forEach(x=>x.classList.remove('is-active'));
  }

  function setMode(mode){
    clearTimeout(modeTimer);
    clearMode();
    document.body.classList.add('omega-mode-'+mode);
    const pose=document.querySelector(`.omega-pose[data-mode="${mode}"]`);
    if(pose)pose.classList.add('is-active');
    react(true);
    if(mode==='smoke')modeTimer=setTimeout(()=>{clearMode();react(false)},3600);
    else if(mode==='smile')modeTimer=setTimeout(()=>{clearMode();react(false)},2200);
    else if(mode==='look')modeTimer=setTimeout(()=>{clearMode();react(false)},2600);
    else if(mode==='idle')react(false);
  }

  function playJuegos(){
    if(document.body.classList.contains('omega-playing'))return;
    clearTimeout(modeTimer);
    clearMode();
    document.body.classList.add('omega-playing');
    react(true);
    modeTimer=setTimeout(()=>{
      document.body.classList.remove('omega-playing');
      react(false);
    },1000)
  }

  function bind(){
    document.addEventListener('mousemove',mouse,{passive:true});

    const interactive=qsa('.omega-btn,.omega-card,.module,.dashboard-module,.button,input[type="submit"],input[type="button"],#nav-sidebar a');
    interactive.forEach(el=>{
      el.addEventListener('mouseenter',()=>{
        clearTimeout(hoverTimer);
        react(true);
        document.body.classList.add('omega-attentive');
      });
      el.addEventListener('mouseleave',()=>{
        hoverTimer=setTimeout(()=>{
          if(!document.body.classList.contains('omega-playing'))react(false);
          document.body.classList.remove('omega-attentive');
        },90)
      });
    });

    qsa('.omega-pose').forEach(pose=>{
      pose.addEventListener('click',()=>setMode(pose.dataset.mode||'idle'));
    });

    qsa('a,button,input[type="submit"],input[type="button"]').forEach(el=>{
      const t=((el.textContent||'')+' '+(el.getAttribute('href')||'')+' '+(el.getAttribute('value')||'')+' '+(el.getAttribute('aria-label')||'')).toLowerCase();
      if(t.includes('juego')||t.includes('juegos'))el.addEventListener('click',playJuegos,{capture:true});
    });

    /* No hay reproducción automática de poses ni loop del personaje. */
  }

  async function start(){build();await character();drops();bind()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
