(()=>{
  const BASE="/static/admin/omega/";
  const qsa=s=>[...document.querySelectorAll(s)];
  let actor,rain,hoverTimer,modeTimer,hovering=false,manualMode=false;

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

  function clearCharacterModes(){
    document.body.classList.remove('omega-mode-look','omega-mode-smile','omega-mode-smoke');
  }

  function manualMode(mode){
    clearTimeout(modeTimer);
    manualMode=true;
    clearCharacterModes();
    document.body.classList.add('omega-mode-'+mode);
    qsa('.omega-pose').forEach(x=>x.classList.toggle('is-active',x.dataset.mode===mode));
    react(mode!=='idle');
    if(mode==='smoke')document.body.classList.add('omega-attentive');
    else document.body.classList.remove('omega-attentive');
    if(mode==='idle')manualMode=false;
  }

  function hoverCharacter(isJuegos){
    if(manualMode||document.body.classList.contains('omega-playing'))return;
    clearTimeout(modeTimer);
    document.body.classList.add('omega-attentive','omega-mode-look','omega-mode-smile','omega-mode-smoke');
    react(true);
    /* Juegos provoca una reacción más fuerte, pero sigue siendo 100% por interacción. */
    if(isJuegos)document.body.classList.add('omega-juegos-focus');
  }

  function leaveCharacter(){
    clearTimeout(hoverTimer);
    hoverTimer=setTimeout(()=>{
      if(!manualMode&&!document.body.classList.contains('omega-playing')){
        clearCharacterModes();
        document.body.classList.remove('omega-attentive','omega-juegos-focus');
        react(false);
      }
    },120);
  }

  function playJuegos(){
    if(document.body.classList.contains('omega-playing'))return;
    clearTimeout(modeTimer);
    manualMode=false;
    clearCharacterModes();
    qsa('.omega-pose').forEach(x=>x.classList.remove('is-active'));
    document.body.classList.add('omega-playing','omega-mode-smile','omega-attentive','omega-juegos-focus');
    react(true);
    modeTimer=setTimeout(()=>{
      document.body.classList.remove('omega-playing');
      if(!hovering){
        clearCharacterModes();
        document.body.classList.remove('omega-attentive','omega-juegos-focus');
        react(false);
      }else{
        hoverCharacter(true);
      }
    },1000)
  }

  function bind(){
    document.addEventListener('mousemove',mouse,{passive:true});

    const interactive=qsa('.omega-btn,.omega-card,.module,.dashboard-module,.button,input[type="submit"],input[type="button"],#nav-sidebar a');
    interactive.forEach(el=>{
      el.addEventListener('mouseenter',()=>{
        hovering=true;
        clearTimeout(hoverTimer);
        const text=((el.textContent||'')+' '+(el.getAttribute('href')||'')+' '+(el.getAttribute('aria-label')||'')).toLowerCase();
        hoverCharacter(text.includes('juego')||text.includes('juegos'));
      });
      el.addEventListener('mouseleave',()=>{
        hovering=false;
        leaveCharacter();
      });
    });

    qsa('.omega-pose').forEach(pose=>{
      pose.addEventListener('click',()=>manualMode(pose.dataset.mode||'idle'));
    });

    qsa('a,button,input[type="submit"],input[type="button"]').forEach(el=>{
      const t=((el.textContent||'')+' '+(el.getAttribute('href')||'')+' '+(el.getAttribute('value')||'')+' '+(el.getAttribute('aria-label')||'')).toLowerCase();
      if(t.includes('juego')||t.includes('juegos'))el.addEventListener('click',playJuegos,{capture:true});
    });

    /* El personaje NO se reproduce solo. Toda pose se activa por hover o click. */
  }

  async function start(){build();await character();drops();bind()}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
