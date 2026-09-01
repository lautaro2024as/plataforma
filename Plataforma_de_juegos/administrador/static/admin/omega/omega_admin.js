(()=>{
  const BASE="/static/admin/omega/";
  const qsa=s=>[...document.querySelectorAll(s)];
  let actor,rain,hoverTimer,blinkTimer,smokeTimer,smileTimer,ambientTimer;

  const layer=id=>{const e=document.createElement('div');e.id=id;document.body.prepend(e);return e};

  function build(){
    layer('omega-stage');
    layer('omega-grid');
    rain=layer('omega-rain');
    layer('omega-light');
    layer('omega-vignette');
    actor=layer('omega-actor');
  }

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
      f.appendChild(d);
    }
    rain.appendChild(f);
  }

  function mouse(e){
    const x=e.clientX/innerWidth-.5;
    const y=e.clientY/innerHeight-.5;
    document.documentElement.style.setProperty('--ox',x*28+'px');
    document.documentElement.style.setProperty('--oy',y*18+'px');
    document.documentElement.style.setProperty('--ax',x*24+'px');
    document.documentElement.style.setProperty('--ay',y*12+'px');
    document.documentElement.style.setProperty('--at',x*4.5+'deg');
    document.documentElement.style.setProperty('--lookx',x.toFixed(3));
    document.documentElement.style.setProperty('--looky',y.toFixed(3));
  }

  function react(on){document.body.classList.toggle('omega-reacting',on)}

  function blink(){
    if(document.hidden)return;
    document.body.classList.add('omega-blink');
    setTimeout(()=>document.body.classList.remove('omega-blink'),125);
  }

  function scheduleBlink(){
    clearTimeout(blinkTimer);
    blinkTimer=setTimeout(()=>{
      blink();
      /* Natural second blink sometimes follows the first. */
      if(Math.random()<0.22)setTimeout(blink,210);
      scheduleBlink();
    },2800+Math.random()*4800);
  }

  function smokePulse(){
    if(document.hidden)return;
    document.body.classList.add('omega-smoke-pulse');
    setTimeout(()=>document.body.classList.remove('omega-smoke-pulse'),700);
  }

  function scheduleSmoke(){
    clearTimeout(smokeTimer);
    smokeTimer=setTimeout(()=>{
      smokePulse();
      scheduleSmoke();
    },3200+Math.random()*4200);
  }

  function ambientSmile(){
    clearTimeout(smileTimer);
    ambientTimer=setTimeout(()=>{
      if(!document.hidden){
        document.body.classList.add('omega-smile');
        setTimeout(()=>document.body.classList.remove('omega-smile'),1000);
      }
      ambientSmile();
    },9000+Math.random()*7000);
  }

  function playJuegos(){
    if(document.body.classList.contains('omega-playing'))return;
    clearTimeout(hoverTimer);
    document.body.classList.add('omega-playing','omega-attentive','omega-juegos-focus');
    react(true);
    setTimeout(()=>document.body.classList.add('omega-smile'),430);
    setTimeout(()=>{
      document.body.classList.remove('omega-playing','omega-smile');
      if(!document.body.matches(':hover')){
        document.body.classList.remove('omega-attentive','omega-juegos-focus');
        react(false);
      }
    },1900);
  }

  function bind(){
    document.addEventListener('mousemove',mouse,{passive:true});

    const interactive=qsa('.omega-btn,.omega-card,.module,.dashboard-module,.button,input[type="submit"],input[type="button"],#nav-sidebar a');
    interactive.forEach(el=>{
      el.addEventListener('mouseenter',()=>{
        clearTimeout(hoverTimer);
        react(true);
        document.body.classList.add('omega-attentive');
        const text=((el.textContent||'')+' '+(el.getAttribute('href')||'')+' '+(el.getAttribute('aria-label')||'')).toLowerCase();
        if(text.includes('juego')||text.includes('juegos'))document.body.classList.add('omega-juegos-focus');
      });
      el.addEventListener('mouseleave',()=>{
        hoverTimer=setTimeout(()=>{
          if(!document.body.classList.contains('omega-playing')){
            document.body.classList.remove('omega-attentive','omega-juegos-focus');
            react(false);
          }
        },120);
      });
    });

    qsa('a,button,input[type="submit"],input[type="button"]').forEach(el=>{
      const t=((el.textContent||'')+' '+(el.getAttribute('href')||'')+' '+(el.getAttribute('value')||'')+' '+(el.getAttribute('aria-label')||'')).toLowerCase();
      if(t.includes('juego')||t.includes('juegos'))el.addEventListener('click',playJuegos,{capture:true});
    });

    document.addEventListener('visibilitychange',()=>{
      if(!document.hidden){scheduleBlink();scheduleSmoke();}
    });
  }

  async function start(){
    build();
    await character();
    drops();
    bind();
    /* The character is alive continuously: breathing + hair sway via CSS,
       while JS schedules natural blinks, smoke pulses and rare smiles. */
    scheduleBlink();
    scheduleSmoke();
    ambientSmile();
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
