(()=>{
  const BASE="/static/admin/omega/";
  let video=null,canvas=null,ctx=null,raf=0,lastW=0,lastH=0;
  const STYLE_ID="omega-video-polish-style";

  function installStyle(){
    if(document.getElementById(STYLE_ID))return;
    const style=document.createElement("style");
    style.id=STYLE_ID;
    style.textContent=`
      #omega-source-video,#omega-live-video{display:none!important}
      #omega-live-canvas{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;display:block!important;pointer-events:none!important;image-rendering:auto!important;filter:saturate(1.02) contrast(1.02) brightness(.90)!important;transform:scale(1.008);transform-origin:50% 52%;animation:omegaCanvasBreath 5.2s ease-in-out infinite;will-change:transform,filter}
      @keyframes omegaCanvasBreath{0%,100%{transform:scale(1.008) translate3d(0,0,0)}50%{transform:scale(1.014) translate3d(0,-2px,0)}}
      #omega-stage .omega-video-tint{position:absolute;inset:0;pointer-events:none;background:linear-gradient(90deg,rgba(1,2,9,.54),rgba(2,2,12,.20) 45%,rgba(2,2,12,.07) 68%,rgba(2,2,12,.30)),radial-gradient(circle at 42% 30%,rgba(255,35,220,.035),transparent 34%),radial-gradient(circle at 76% 68%,rgba(0,246,255,.035),transparent 30%)}
      #omega-stage .omega-video-vignette{position:absolute;inset:0;box-shadow:inset 0 0 180px rgba(0,0,12,.48);pointer-events:none}
      .omega-smoke-real{position:absolute;z-index:3;right:11%;top:18%;width:155px;height:245px;pointer-events:none;opacity:.16;filter:blur(16px);mix-blend-mode:screen;transform-origin:50% 100%;animation:omegaSmokeFloat 8s ease-in-out infinite}
      .omega-smoke-real span{position:absolute;display:block;border-radius:50%;background:radial-gradient(circle at 50% 62%,rgba(245,248,250,.24) 0%,rgba(190,205,214,.10) 27%,rgba(120,145,160,.045) 52%,transparent 74%);filter:blur(9px)}
      .omega-smoke-real span:nth-child(1){width:92px;height:112px;right:16px;bottom:0;animation:omegaSmokePuff1 6.2s ease-in-out infinite}
      .omega-smoke-real span:nth-child(2){width:75px;height:98px;right:51px;bottom:72px;animation:omegaSmokePuff2 7.1s ease-in-out infinite .7s}
      .omega-smoke-real span:nth-child(3){width:62px;height:84px;right:12px;bottom:137px;animation:omegaSmokePuff3 7.8s ease-in-out infinite 1.1s}
      @keyframes omegaSmokeFloat{0%,100%{transform:translate3d(0,8px,0) scale(.92)}50%{transform:translate3d(-14px,-20px,0) scale(1.05)}}
      @keyframes omegaSmokePuff1{0%,100%{opacity:.08;transform:translate(0,8px) scale(.86)}45%{opacity:.22;transform:translate(-9px,-7px) scale(1.04)}75%{opacity:.12;transform:translate(-18px,-21px) scale(1.13)}}
      @keyframes omegaSmokePuff2{0%,100%{opacity:.04;transform:translate(2px,7px) scale(.82)}50%{opacity:.18;transform:translate(-14px,-16px) scale(1.08)}}
      @keyframes omegaSmokePuff3{0%,100%{opacity:.025;transform:translate(5px,5px) scale(.78)}55%{opacity:.12;transform:translate(-13px,-20px) scale(1.06)}}
      body.omega-reacting #omega-live-canvas{filter:saturate(1.06) contrast(1.035) brightness(.96)!important}
      body.omega-playing #omega-live-canvas{animation:omegaCanvasTurn 1.1s cubic-bezier(.2,.85,.35,1);filter:saturate(1.10) contrast(1.05) brightness(.98)!important}
      @keyframes omegaCanvasTurn{0%{transform:scale(1.008) translate3d(0,0,0)}32%{transform:scale(1.024) translate3d(-8px,-3px,0) rotate(-.45deg)}63%{transform:scale(1.028) translate3d(9px,-2px,0) rotate(.55deg)}100%{transform:scale(1.008) translate3d(0,0,0) rotate(0)}}
      @media(max-width:700px){#omega-live-canvas{transform:scale(1.03)!important}.omega-smoke-real{right:4%;opacity:.10}}
      @media(prefers-reduced-motion:reduce){#omega-live-canvas,.omega-smoke-real,.omega-smoke-real span{animation:none!important}}
    `;
    document.head.appendChild(style);
  }

  function createCanvas(stage){
    canvas=document.createElement("canvas");
    canvas.id="omega-live-canvas";
    canvas.setAttribute("aria-hidden","true");
    canvas.width=640;
    canvas.height=360;
    ctx=canvas.getContext("2d",{alpha:true,willReadFrequently:true});
    stage.appendChild(canvas);
  }

  function resizeCanvas(){
    if(!canvas||!ctx)return;
    const w=640,h=360;
    if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h}
    lastW=w;lastH=h;
  }

  function removeMagenta(data){
    for(let i=0;i<data.length;i+=4){
      const r=data[i],g=data[i+1],b=data[i+2];
      const magenta=Math.min(r,b)-g;
      const vivid=r+b-g*1.65;
      const hot=r>180&&b>145&&g<125&&magenta>90&&vivid>255;
      const near=r>135&&b>120&&g<105&&magenta>65&&vivid>195;
      if(hot){data[i+3]=0}
      else if(near){
        const edge=Math.max(0,Math.min(1,(magenta-65)/60));
        data[i+3]=Math.round(255*(1-edge*.92));
      }
    }
  }

  function render(){
    if(!video||!canvas||!ctx)return;
    if(video.readyState>=2&&!video.paused&&!video.ended){
      resizeCanvas();
      const cw=canvas.width,ch=canvas.height;
      const vw=video.videoWidth||cw,vh=video.videoHeight||ch;
      const scale=Math.max(cw/vw,ch/vh);
      const dw=vw*scale,dh=vh*scale;
      const dx=(cw-dw)/2,dy=(ch-dh)/2;
      ctx.clearRect(0,0,cw,ch);
      ctx.drawImage(video,dx,dy,dw,dh);
      const frame=ctx.getImageData(0,0,cw,ch);
      removeMagenta(frame.data);
      ctx.putImageData(frame,0,0);
    }
    raf=requestAnimationFrame(render);
  }

  function ensureVideo(){
    const stage=document.getElementById("omega-stage");
    if(!stage)return false;
    if(document.getElementById("omega-live-canvas"))return true;
    stage.innerHTML="";
    video=document.createElement("video");
    video.id="omega-source-video";
    video.autoplay=true;video.loop=true;video.muted=true;video.playsInline=true;video.preload="auto";
    video.setAttribute("aria-hidden","true");
    const source=document.createElement("source");
    source.src=BASE+"omega_character_loop.mp4";
    source.type="video/mp4";
    video.appendChild(source);
    createCanvas(stage);
    const tint=document.createElement("div");tint.className="omega-video-tint";
    const vignette=document.createElement("div");vignette.className="omega-video-vignette";
    stage.appendChild(tint);stage.appendChild(vignette);stage.appendChild(video);
    video.addEventListener("loadedmetadata",resizeCanvas,{once:true});
    video.addEventListener("play",()=>{cancelAnimationFrame(raf);render()});
    video.addEventListener("error",()=>document.body.classList.add("omega-video-error"));
    video.play().catch(()=>{});
    requestAnimationFrame(render);
    return true;
  }

  function addRealisticSmoke(stage){
    if(stage.querySelector(".omega-smoke-real"))return;
    const smoke=document.createElement("div");
    smoke.className="omega-smoke-real";
    smoke.setAttribute("aria-hidden","true");
    smoke.innerHTML="<span></span><span></span><span></span>";
    stage.appendChild(smoke);
  }

  function bind(){
    const els=[...document.querySelectorAll(".omega-btn,.omega-card,.module,.dashboard-module,.button,input[type='submit'],input[type='button'],#nav-sidebar a")];
    els.forEach(el=>{
      el.addEventListener("mouseenter",()=>{
        document.body.classList.add("omega-reacting","omega-attentive");
        const text=((el.textContent||"")+" "+(el.getAttribute("href")||"")+" "+(el.getAttribute("aria-label")||"")).toLowerCase();
        if(text.includes("juego"))document.body.classList.add("omega-juegos-focus");
      });
      el.addEventListener("mouseleave",()=>setTimeout(()=>document.body.classList.remove("omega-reacting","omega-attentive","omega-juegos-focus"),120));
      el.addEventListener("click",()=>{
        const text=((el.textContent||"")+" "+(el.getAttribute("href")||"")).toLowerCase();
        if(text.includes("juego")){document.body.classList.add("omega-playing");setTimeout(()=>document.body.classList.remove("omega-playing"),1200)}
      },{capture:true});
    });
  }

  function start(){
    installStyle();
    const stage=document.getElementById("omega-stage");
    if(!stage)return;
    if(ensureVideo()){addRealisticSmoke(stage);bind();}
  }

  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start,{once:true});
  else start();
})();
