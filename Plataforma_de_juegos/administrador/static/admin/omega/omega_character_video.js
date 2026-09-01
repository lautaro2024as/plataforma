(()=>{
  const BASE="/static/admin/omega/";
  let video;

  function ensureVideo(){
    const stage=document.getElementById("omega-stage");
    if(!stage) return false;
    if(document.getElementById("omega-live-video")) return true;

    stage.innerHTML="";
    video=document.createElement("video");
    video.id="omega-live-video";
    video.autoplay=true;
    video.loop=true;
    video.muted=true;
    video.playsInline=true;
    video.preload="auto";
    video.setAttribute("aria-hidden","true");

    const source=document.createElement("source");
    source.src=BASE+"omega_character_loop.mp4";
    source.type="video/mp4";
    video.appendChild(source);

    const tint=document.createElement("div");
    tint.className="omega-video-tint";
    const vignette=document.createElement("div");
    vignette.className="omega-video-vignette";

    stage.appendChild(video);
    stage.appendChild(tint);
    stage.appendChild(vignette);
    video.play().catch(()=>{});
    return true;
  }

  function bind(){
    const els=[...document.querySelectorAll(".omega-btn,.omega-card,.module,.dashboard-module,.button,input[type='submit'],input[type='button'],#nav-sidebar a")];
    els.forEach(el=>{
      el.addEventListener("mouseenter",()=>{
        document.body.classList.add("omega-reacting","omega-attentive");
        const text=((el.textContent||"")+" "+(el.getAttribute("href")||"")+" "+(el.getAttribute("aria-label")||"")).toLowerCase();
        if(text.includes("juego")) document.body.classList.add("omega-juegos-focus");
      });
      el.addEventListener("mouseleave",()=>setTimeout(()=>document.body.classList.remove("omega-reacting","omega-attentive","omega-juegos-focus"),120));
      el.addEventListener("click",()=>{
        const text=((el.textContent||"")+" "+(el.getAttribute("href")||"")).toLowerCase();
        if(text.includes("juego")){
          document.body.classList.add("omega-playing");
          setTimeout(()=>document.body.classList.remove("omega-playing"),1200);
        }
      },{capture:true});
    });
  }

  function start(){if(ensureVideo()) bind()}
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",start,{once:true});
  else start();
})();
