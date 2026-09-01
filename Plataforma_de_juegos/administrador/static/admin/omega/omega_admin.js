(()=>{
  const BASE="/static/admin/omega/";
  const qsa=s=>[...document.querySelectorAll(s)];
  let actor,rain,hoverTimer,blinkTimer,smokeTimer,smileTimer,ambientTimer,rafId;

  const layer=id=>{const e=document.createElement('div');e.id=id;document.body.prepend(e);return e};

  function build(){
    layer('omega-stage');
    layer('omega-grid');
    rain=layer('omega-rain');
    layer('omega-particles');
    layer('omega-light');
    layer('omega-vignette');
    actor=layer('omega-actor');
    layer('omega-character-atmosphere');
    layer('omega-hud-fx');
  }

  async function character(){
    try{
      const r=await fetch(BASE+'omega_character.svg',{cache:'no-store'});
      if(!r.ok)throw Error('character');
      actor.innerHTML=await r.text();
      const svg=actor.querySelector('svg');
      if(svg){
        svg.setAttribute('aria-hidden','true');
        svg.style.pointerEvents='none';
        svg.classList.add('omega-character-svg');
      }
      const smoke=document.createElement('span');
      smoke.className='omega-smoke';
      smoke.setAttribute('aria-hidden','true');
      actor.appendChild(smoke);
      const ember=document.createElement('span');
      ember.className='omega-ember';
      ember.setAttribute('aria-hidden','true');
      actor.appendChild(ember);
      const rim=document.createElement('span');
      rim.className='omega-character-rim';
      rim.setAttribute('aria-hidden','true');
      actor.appendChild(rim);
    }catch(e){actor.innerHTML=''}
  }

  function drops(){
    const f=document.createDocumentFragment();
    for(let i=0;i<150;i++){
      const d=document.createElement('i');
      d.className='omega-drop';
      d.style.left=Math.random()*100+'%';
      d.style.height=34+Math.random()*130+'px';
      d.style.opacity=(.08+Math.random()*.40).toFixed(2);
      d.style.setProperty('--rs',(0.55+Math.random()*1.45).toFixed(2)+'s');
      d.style.animationDelay=Math.random()*3.8+'s';
      f.appendChild(d);
    }
    rain.appendChild(f);
  }

  function particles(){
    const host=document.getElementById('omega-particles');
    if(!host)return;
    const f=document.createDocumentFragment();
    for(let i=0;i<48;i++){
      const p=document.createElement('i');
      p.className='omega-particle';
      p.style.left=(8+Math.random()*84)+'%';
      p.style.top=(8+Math.random()*82)+'%';
      p.style.setProperty('--ps',(5+Math.random()*7).toFixed(2)+'s');
      p.style.setProperty('--pd',(-Math.random()*8).toFixed(2)+'s');
      p.style.setProperty('--px',(Math.random()*28-14).toFixed(1)+'px');
      p.style.setProperty('--py',(Math.random()*34-17).toFixed(1)+'px');
      p.style.setProperty('--po',(0.10+Math.random()*0.42).toFixed(2));
      f.appendChild(p);
    }
    host.appendChild(f);
  }

  function smokeParticles(){
    const host=actor;
    if(!host)return;
    const f=document.createDocumentFragment();
    for(let i=0;i<18;i++){
      const p=document.createElement('span');
      p.className='omega-smoke-particle';
      p.style.setProperty('--sx',(Math.random()*32-16).toFixed(1)+'px');
      p.style.setProperty('--sy',(Math.random()*16).toFixed(1)+'px');
      p.style.setProperty('--sw',(5+Math.random()*12).toFixed(1)+'px');
      p.style.setProperty('--sd',(0.1+i*.17).toFixed(2)+'s');
      p.style.setProperty('--ss',(2.5+Math.random()*2.8).toFixed(2)+'s');
      p.style.setProperty('--sr',(Math.random()*34-17).toFixed(1)+'deg');
      p.style.setProperty('--so',(0.12+Math.random()*.26).toFixed(2));
      f.appendChild(p);
    }
    host.appendChild(f);
  }

  function mouse(e){
    const x=e.clientX/innerWidth-.5;
    const y=e.clientY/innerHeight-.5;
    document.documentElement.style.setProperty('--ox',(x*24).toFixed(2)+'px');
    document.documentElement.style.setProperty('--oy',(y*14).toFixed(2)+'px');
    document.documentElement.style.setProperty('--ax',(x*14).toFixed(2)+'px');
    document.documentElement.style.setProperty('--ay',(y*8).toFixed(2)+'px');
    document.documentElement.style.setProperty('--at',(x*2.2).toFixed(2)+'deg');
    document.documentElement.style.setProperty('--lookx',x.toFixed(3));
    document.documentElement.style.setProperty('--looky',y.toFixed(3));
  }

  function organicMotion(now){
    const t=now/1000;
    const breathe=Math.sin(t*1.36)*0.5+0.5;
    const sway=Math.sin(t*.52)*0.58 + Math.sin(t*.81)*0.22;
    const micro=Math.sin(t*2.7)*.16 + Math.sin(t*4.1)*.08;
    document.documentElement.style.setProperty('--omega-breathe',breathe.toFixed(4));
    document.documentElement.style.setProperty('--omega-sway',sway.toFixed(4));
    document.documentElement.style.setProperty('--omega-micro',micro.toFixed(4));
    rafId=requestAnimationFrame(organicMotion);
  }

  function react(on){document.body.classList.toggle('omega-reacting',on)}

  function blink(){
    if(document.hidden)return;
    document.body.classList.add('omega-blink');
    setTimeout(()=>document.body.classList.remove('omega-blink'),115);
  }

  function scheduleBlink(){
    clearTimeout(blinkTimer);
    blinkTimer=setTimeout(()=>{
      blink();
      if(Math.random()<0.16)setTimeout(blink,180);
      scheduleBlink();
    },3200+Math.random()*5200);
  }

  function smokePulse(){
    if(document.hidden)return;
    document.body.classList.add('omega-smoke-pulse');
    setTimeout(()=>document.body.classList.remove('omega-smoke-pulse'),820);
  }

  function scheduleSmoke(){
    clearTimeout(smokeTimer);
    smokeTimer=setTimeout(()=>{
      smokePulse();
      scheduleSmoke();
    },3600+Math.random()*4800);
  }

  function ambientSmile(){
    clearTimeout(ambientTimer);
    ambientTimer=setTimeout(()=>{
      if(!document.hidden){
        document.body.classList.add('omega-smile');
        setTimeout(()=>document.body.classList.remove('omega-smile'),950);
      }
      ambientSmile();
    },10000+Math.random()*8500);
  }

  function playJuegos(done){
    if(document.body.classList.contains('omega-playing'))return;
    clearTimeout(hoverTimer);
    document.body.classList.add('omega-playing','omega-attentive','omega-juegos-focus');
    react(true);
    setTimeout(()=>document.body.classList.add('omega-smile'),420);
    setTimeout(()=>{
      document.body.classList.remove('omega-playing','omega-smile');
      document.body.classList.remove('omega-attentive','omega-juegos-focus');
      react(false);
      if(typeof done==='function')done();
    },1280);
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
        },140);
      });
    });

    qsa('a,button,input[type="submit"],input[type="button"]').forEach(el=>{
      const t=((el.textContent||'')+' '+(el.getAttribute('href')||'')+' '+(el.getAttribute('value')||'')+' '+(el.getAttribute('aria-label')||'')).toLowerCase();
      if(t.includes('juego')||t.includes('juegos')){
        el.addEventListener('click',e=>{
          const href=el.href;
          if(!href)return;
          e.preventDefault();
          playJuegos(()=>{window.location.href=href;});
        });
      }
    });

    document.addEventListener('visibilitychange',()=>{
      if(!document.hidden){scheduleBlink();scheduleSmoke();}
    });
  }

  function start(){
    build();
    character().then(()=>{
      drops();
      particles();
      smokeParticles();
      bind();
      scheduleBlink();
      scheduleSmoke();
      ambientSmile();
      rafId=requestAnimationFrame(organicMotion);
    });
  }

  window.addEventListener('pagehide',()=>cancelAnimationFrame(rafId),{once:true});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
