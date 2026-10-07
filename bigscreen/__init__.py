import os
import time
from flask import Blueprint, jsonify, request, abort, Response, send_from_directory
from CTFd.models import Solves, Users, Challenges
from CTFd.utils.scores import get_standings

KEY = os.getenv("BIGSCREEN_KEY", "")
HERE = os.path.dirname(os.path.abspath(__file__))
bp = Blueprint("bigscreen", __name__)

_cache = {"t": 0.0, "v": None}
CACHE_SECONDS = 2


def _check():
    if not KEY or request.args.get("key") != KEY:
        abort(403)


def _no_store(resp):
    resp.headers["Cache-Control"] = "no-store"
    return resp


def _build():
    # First capture of each challenge = earliest solve in the DB (id breaks date ties).
    solves = (
        Solves.query.join(Users, Solves.user_id == Users.id)
        .join(Challenges, Solves.challenge_id == Challenges.id)
        .filter(Users.hidden == False, Users.banned == False)  # noqa: E712
        .order_by(Solves.date.asc(), Solves.id.asc())
        .all()
    )
    seen, bloods = set(), []
    for s in solves:
        if s.challenge_id in seen:
            continue
        if s.team and (s.team.hidden or s.team.banned):
            continue
        seen.add(s.challenge_id)
        bloods.append({
            "challenge_id": s.challenge_id,
            "challenge": s.challenge.name,
            "category": s.challenge.category,
            "team": s.team.name if s.team else s.user.name,
            "user": s.user.name,
            "date": s.date.isoformat(),
        })

    standings = []
    for i, r in enumerate(get_standings()):
        standings.append({
            "id": getattr(r, "account_id", i),
            "name": getattr(r, "name", "?"),
            "score": int(getattr(r, "score", 0) or 0),
        })
    return {"bloods": bloods, "standings": standings}


@bp.route("/bigscreen/data")
def data():
    _check()
    now = time.time()
    if _cache["v"] is None or now - _cache["t"] > CACHE_SECONDS:
        _cache["v"] = _build()
        _cache["t"] = now
    return _no_store(jsonify(_cache["v"]))


@bp.route("/bigscreen/blood.mp3")
def sound():
    _check()
    return send_from_directory(HERE, "blood.mp3", max_age=3600)


PAGE = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Capture the Cup - Live</title>
<link rel="stylesheet" href="/themes/mytheme/static/custom/css/capture-the-cup.css">
<style>
:root{--night:#070b14;--panel:#101827;--raised:#151f31;--ink:#f5f8ff;--muted:#91a0b6;
 --cyan:#38bdf8;--cyan2:#75d8ff;--red:#f23856;--line:rgba(153,181,219,.18)}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;overflow:hidden;color:var(--ink);font-family:Lato,system-ui,sans-serif;
 background-color:var(--night);
 background-image:linear-gradient(rgba(117,216,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(117,216,255,.035) 1px,transparent 1px),
 radial-gradient(circle at 12% 0,rgba(56,189,248,.14),transparent 30%),radial-gradient(circle at 90% 25%,rgba(242,56,86,.1),transparent 28%);
 background-size:64px 64px,64px 64px,auto,auto}
h1,h2,.title{font-family:Raleway,Lato,sans-serif}
.app{display:grid;grid-template-rows:auto 1fr;height:100vh;padding:1.2rem 1.6rem;gap:1rem}
header{position:relative;display:flex;align-items:center;gap:1rem;padding-bottom:.9rem}
header::after{content:"";position:absolute;left:0;right:0;bottom:0;height:2px;background:linear-gradient(90deg,var(--cyan),var(--red) 60%,transparent)}
header img{height:clamp(36px,6vh,64px)}
header h1{margin:0;font-size:clamp(1.2rem,3.2vh,2.2rem);letter-spacing:.14em;text-transform:uppercase}
.live{margin-left:auto;display:flex;align-items:center;gap:.5rem;font-size:clamp(.8rem,1.8vh,1.1rem);color:var(--cyan2)}
.dot{width:.7em;height:.7em;border-radius:50%;background:var(--cyan);box-shadow:0 0 10px var(--cyan);animation:pulse 1.4s infinite}
.dot.off{background:var(--red);box-shadow:0 0 10px var(--red);animation:none}
@keyframes pulse{50%{opacity:.25}}
main{display:grid;min-height:0}
section{display:flex;flex-direction:column;min-height:0}
h2{margin:0 0 .7rem;color:var(--cyan2);letter-spacing:.18em;font-size:clamp(.9rem,2.2vh,1.3rem)}
#board{display:grid;gap:6px;flex:1;min-height:0;overflow:hidden}
.row{display:flex;align-items:center;justify-content:space-between;gap:.8rem;background:var(--panel);
 border:1px solid var(--line);border-left:4px solid transparent;border-radius:8px;padding:0 1rem;min-width:0}
.nm{display:flex;align-items:center;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.rk{min-width:2.2em;opacity:.65;font-variant-numeric:tabular-nums}
.row b{color:var(--cyan2);font-variant-numeric:tabular-nums}
.ci{width:1.15em;height:1.15em;margin-right:.45em;flex:none}
.row.r1{border-left-color:#f7b733;background:linear-gradient(90deg,rgba(247,183,51,.14),var(--panel) 55%)}
.row.r2{border-left-color:#c0c7d1}
.row.r3{border-left-color:var(--red)}
.row.up{animation:rowflash 1.6s}
@keyframes rowflash{0%{background:#12466a;transform:scale(1.02)}100%{transform:none}}
.empty{color:var(--muted);padding:1rem}
.fb-card{position:fixed;top:5.8rem;right:1.6rem;width:min(23rem,38vw);padding:1rem 1.1rem;z-index:4;
 background:linear-gradient(145deg,var(--raised),var(--panel));border:1px solid var(--line);border-radius:8px;
 box-shadow:0 18px 45px rgba(0,0,0,.4)}
.fb-card::before{content:"";position:absolute;inset:0 auto 0 0;width:4px;background:linear-gradient(var(--cyan),var(--red))}
.fb-label{display:flex;align-items:center;gap:.5rem;color:#f7b733;font-size:.72rem;font-weight:800;letter-spacing:.18em}
.fb-label svg{width:1.6rem;height:1.6rem}
.fb-team{margin:.5rem 0 .2rem;font-family:Raleway,Lato,sans-serif;font-size:clamp(1.15rem,2.2vw,1.7rem);font-weight:800;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fb-chal{font-size:clamp(.85rem,1.3vw,1rem);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.fb-meta{margin-top:.35rem;color:var(--muted);font-size:.75rem}
.fb-card.empty{opacity:.7}

/* ---- cup celebration ---- */
#overlay{position:fixed;inset:0;display:none;flex-direction:column;align-items:center;justify-content:center;z-index:10;
 text-align:center;padding:2rem;overflow:hidden;
 background:radial-gradient(circle at 50% 36%,rgba(56,189,248,.3),transparent 55%),radial-gradient(circle at 50% 100%,rgba(242,56,86,.22),transparent 50%),var(--night)}
#overlay.show{display:flex;animation:fadein .4s}
@keyframes fadein{from{opacity:0}}
.rays{position:absolute;width:170vmax;height:170vmax;left:50%;top:36%;margin:-85vmax 0 0 -85vmax;pointer-events:none;
 background:repeating-conic-gradient(rgba(56,189,248,.2) 0 6deg,transparent 6deg 12deg,rgba(242,56,86,.16) 12deg 18deg,transparent 18deg 24deg);
 -webkit-mask:radial-gradient(circle,#000,transparent 55%);mask:radial-gradient(circle,#000,transparent 55%);animation:spin 40s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.whiteout{position:absolute;inset:0;background:#fff;pointer-events:none;animation:whiteout 1s both}
@keyframes whiteout{from{opacity:.85}to{opacity:0}}
.cupwrap{position:relative;z-index:2}
.cupwrap svg{width:clamp(150px,32vh,320px);height:auto;filter:drop-shadow(0 0 34px rgba(247,183,51,.6));
 animation:rise 1.1s cubic-bezier(.2,1.5,.3,1) both,float 3.2s ease-in-out 1.1s infinite}
.cupwrap::after{content:"";position:absolute;left:50%;top:45%;width:20vh;height:20vh;margin:-10vh 0 0 -10vh;border-radius:50%;
 border:3px solid var(--cyan2);animation:ring 2.2s ease-out .5s infinite;opacity:0}
@keyframes rise{from{transform:translateY(80px) scale(.2) rotate(-20deg);opacity:0}}
@keyframes float{50%{transform:translateY(-12px)}}
@keyframes ring{0%{transform:scale(.5);opacity:.8}100%{transform:scale(4);opacity:0}}
#overlay .eyebrow,#overlay .title,#overlay .team,#overlay .chal,#overlay .by{position:relative;z-index:2;animation:up .7s cubic-bezier(.2,.9,.3,1) both}
.eyebrow{margin-top:1.4vh;color:#f7b733;font-weight:800;letter-spacing:.5em;font-size:clamp(.9rem,2.6vh,1.6rem);animation-delay:.6s!important}
.title{font-size:clamp(2.4rem,11vh,7rem);font-weight:800;letter-spacing:.08em;line-height:1;animation-delay:.75s!important;
 background:linear-gradient(90deg,var(--cyan2),#fff 50%,#ff7f93);-webkit-background-clip:text;background-clip:text;color:transparent}
.team{margin:1.6vh 0 .6vh;font-family:Raleway,Lato,sans-serif;font-size:clamp(2rem,9vh,6rem);font-weight:800;word-break:break-word;
 text-shadow:0 0 40px rgba(56,189,248,.6);animation-delay:1s!important}
.chal{font-size:clamp(1.2rem,4.6vh,3rem);color:var(--cyan2);animation-delay:1.2s!important}
.by{font-size:clamp(1rem,2.8vh,1.8rem);color:var(--muted);margin-top:.8vh;animation-delay:1.35s!important}
@keyframes up{from{transform:translateY(30px);opacity:0}}
#confetti{position:absolute;inset:0;pointer-events:none;z-index:1}
#confetti i{position:absolute;top:-4vh;left:var(--x);width:var(--s);height:calc(var(--s)*1.7);background:var(--c);opacity:.95;
 animation:fall var(--d) linear var(--w) forwards}
@keyframes fall{to{transform:translate3d(var(--dx),108vh,0) rotate(var(--r))}}

/* ---- sound gate ---- */
#gate{position:fixed;inset:0;z-index:20;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1.2rem;
 background:var(--night);cursor:pointer;text-align:center}
#gate svg{width:clamp(90px,20vh,200px);filter:drop-shadow(0 0 24px rgba(247,183,51,.5));animation:float 3s ease-in-out infinite}
#gate b{font-family:Raleway,Lato,sans-serif;letter-spacing:.3em;font-size:clamp(1.2rem,4vh,2.4rem)}
#gate span{color:var(--muted)}
@media(max-width:900px){.fb-card{top:5.4rem;right:1rem;width:min(19rem,calc(100vw - 2rem))}}
@media(max-width:620px){.app{padding:.9rem 1rem}.fb-card{top:auto;bottom:1rem;right:1rem;width:calc(100vw - 2rem)}}
@media(prefers-reduced-motion:reduce){.rays,.cupwrap svg,#gate svg{animation:none}}
</style></head><body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
 <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff3bf"/><stop offset=".45" stop-color="#f7b733"/><stop offset="1" stop-color="#a8651a"/></linearGradient>
 <symbol id="cup" viewBox="0 0 200 220">
  <path d="M58 52H34c-5 0-7 4-6 9 4 26 20 42 42 47" fill="none" stroke="url(#gold)" stroke-width="9" stroke-linecap="round"/>
  <path d="M142 52h24c5 0 7 4 6 9-4 26-20 42-42 47" fill="none" stroke="url(#gold)" stroke-width="9" stroke-linecap="round"/>
  <path d="M54 26h92v62c0 34-22 54-46 58-24-4-46-24-46-58z" fill="url(#gold)"/>
  <path d="M66 34h14v54c0 20 8 34 20 42-22-6-34-26-34-50z" fill="#fff" opacity=".28"/>
  <path d="M100 56l7.5 15.200 16.800 2.400-12.200 11.800 2.900 16.700-15-7.900-15 7.900 2.900-16.700-12.200-11.800 16.800-2.400z" fill="#7a4a10" opacity=".55"/>
  <path d="M90 146h20v26H90z" fill="url(#gold)"/>
  <rect x="66" y="170" width="68" height="14" rx="5" fill="url(#gold)"/>
  <rect x="52" y="184" width="96" height="18" rx="6" fill="#38bdf8"/>
  <rect x="52" y="184" width="96" height="6" rx="3" fill="#75d8ff"/>
  <rect x="52" y="198" width="96" height="4" rx="2" fill="#f23856"/>
 </symbol></defs></svg>

<div id="gate"><svg viewBox="0 0 200 220"><use href="#cup"/></svg><b>CAPTURE THE CUP</b><span>Click once to start the big screen with sound</span></div>

<div class="app">
 <header>
  <img src="/themes/mytheme/static/img/logo1.png" alt="" onerror="this.style.display='none'">
  <h1>Capture the Cup</h1>
  <div class="live"><span class="dot" id="dot"></span><span id="status">LIVE</span></div>
 </header>
 <main><section><h2>SCOREBOARD <span id="count" style="opacity:.6"></span></h2><div id="board"></div></section></main>
 <aside class="fb-card empty" id="fb" aria-live="polite">
  <div class="fb-label"><svg viewBox="0 0 200 220"><use href="#cup"/></svg> LATEST CAPTURE</div>
  <div class="fb-team" id="fb-team">Waiting for the first solve</div>
  <div class="fb-chal" id="fb-chal">The next capture will appear here</div>
  <div class="fb-meta" id="fb-meta"></div>
 </aside>
</div>

<div id="overlay">
 <div class="rays"></div><div id="confetti"></div><div class="whiteout"></div>
 <div class="cupwrap"><svg viewBox="0 0 200 220"><use href="#cup"/></svg></div>
 <div class="eyebrow">FIRST BLOOD</div>
 <div class="title">CUP CAPTURED</div>
 <div class="team" id="ot"></div>
 <div class="chal" id="oc"></div>
 <div class="by" id="ob"></div>
</div>

<script>
const key = new URLSearchParams(location.search).get("key");
const $ = id => document.getElementById(id);
const boardEl = $("board"), overlay = $("overlay");
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
let known = null, queue = [], showing = false, prev = {}, lastN = 0, soundOn = false;

/* ---- sound: browsers need one click before audio may play ---- */
const snd = new Audio("/bigscreen/blood.mp3?key=" + encodeURIComponent(key));
snd.preload = "auto";
$("gate").onclick = () => {
  snd.volume = 0;
  snd.play().then(() => { snd.pause(); snd.currentTime = 0; snd.volume = 1; soundOn = true; }).catch(() => {});
  $("gate").remove();
  if(document.documentElement.requestFullscreen) document.documentElement.requestFullscreen().catch(() => {});
};

function confetti(){
  const box = $("confetti"), cols = ["#38bdf8","#75d8ff","#f23856","#f7b733","#ffffff"];
  box.innerHTML = "";
  for(let i = 0; i < 70; i++){
    const e = document.createElement("i");
    e.style.cssText = "--x:" + (Math.random()*100) + "%;--s:" + (6 + Math.random()*8) + "px;--c:" + cols[i % cols.length] +
      ";--d:" + (3 + Math.random()*3) + "s;--w:" + (Math.random()*1.8) + "s;--dx:" + ((Math.random()-.5)*160) + "px;--r:" + (360 + Math.random()*720) + "deg";
    box.appendChild(e);
  }
}

function next(){
  if(!queue.length){ showing = false; return; }
  showing = true;
  const b = queue.shift();
  $("ot").textContent = b.team;
  $("oc").textContent = b.challenge + " (" + b.category + ")";
  $("ob").textContent = b.user !== b.team ? "captured by " + b.user : "";
  overlay.className = ""; void overlay.offsetWidth;   // restart the animations
  confetti();
  overlay.className = "show";
  if(soundOn){ snd.currentTime = 0; snd.play().catch(() => {}); }
  setTimeout(() => { overlay.className = ""; setTimeout(next, 500); }, 9000);
}

function renderLatest(bloods){
  const b = bloods[bloods.length - 1];
  if(!b) return;
  $("fb").classList.remove("empty");
  $("fb-team").textContent = b.team;
  $("fb-chal").textContent = b.challenge + " / " + b.category;
  $("fb-meta").textContent = b.user !== b.team ? "captured by " + b.user : "first solve recorded";
}

function layout(n){
  const H = boardEl.clientHeight, W = boardEl.clientWidth, GAP = 6, MIN = 40, MAX = 76;
  const cap = Math.max(1, Math.floor((H + GAP) / (MIN + GAP)));
  let cols = Math.min(3, Math.max(1, Math.ceil(n / cap)));
  if(W < 700) cols = 1;
  const rows = Math.max(1, Math.ceil(n / cols));
  const rowH = Math.max(MIN, Math.min(MAX, Math.floor((H - (rows - 1) * GAP) / rows)));
  boardEl.style.gridAutoFlow = "column";
  boardEl.style.gridTemplateColumns = "repeat(" + cols + ",1fr)";
  boardEl.style.gridTemplateRows = "repeat(" + rows + "," + rowH + "px)";
  boardEl.style.fontSize = Math.max(14, rowH * 0.42) + "px";
}

function render(standings){
  const keep = boardEl.scrollTop;
  layout(standings.length);
  if(!standings.length){
    boardEl.innerHTML = '<div class="empty">No scores yet</div>';
  } else {
    boardEl.innerHTML = standings.map((t, i) => {
      const old = prev[t.id];
      let cls = "row";
      if(i < 3) cls += " r" + (i + 1);
      if(old !== undefined && t.score > old) cls += " up";
      const icon = i === 0 ? '<svg class="ci" viewBox="0 0 200 220"><use href="#cup"/></svg>' : "";
      return '<div class="' + cls + '"><span class="nm"><span class="rk">' + (i + 1) + '.</span>' + icon + esc(t.name) + '</span><b>' + t.score + '</b></div>';
    }).join("");
  }
  prev = {};
  standings.forEach(t => prev[t.id] = t.score);
  boardEl.scrollTop = keep;
  $("count").textContent = "(" + standings.length + ")";
  lastN = standings.length;
}

async function tick(){
  try{
    const r = await fetch("/bigscreen/data?key=" + encodeURIComponent(key), {cache: "no-store"});
    if(!r.ok) throw new Error(r.status);
    const d = await r.json();
    if(known === null){
      known = new Set(d.bloods.map(b => b.challenge_id));   // first load stays silent
    } else {
      d.bloods.forEach(b => { if(!known.has(b.challenge_id)){ known.add(b.challenge_id); queue.push(b); } });
    }
    if(!showing) next();
    renderLatest(d.bloods);
    render(d.standings);
    $("dot").className = "dot";
    $("status").textContent = "LIVE · SOUND " + (soundOn ? "ON" : "OFF");
  }catch(e){
    $("dot").className = "dot off"; $("status").textContent = "RECONNECTING";
  }
}

/* press T to rehearse the celebration */
document.addEventListener("keydown", e => {
  if(e.key.toLowerCase() === "t"){
    queue.push({team: "Demo Team", challenge: "Test Challenge", category: "web", user: "demo player"});
    if(!showing) next();
  }
});

let dir = 1;
setInterval(() => {
  if(boardEl.scrollHeight <= boardEl.clientHeight + 2) return;
  boardEl.scrollTop += dir;
  if(boardEl.scrollTop + boardEl.clientHeight >= boardEl.scrollHeight - 1) dir = -1;
  else if(boardEl.scrollTop <= 0) dir = 1;
}, 40);

window.addEventListener("resize", () => layout(lastN));
tick(); setInterval(tick, 3000);
</script></body></html>"""


@bp.route("/bigscreen")
def page():
    _check()
    return _no_store(Response(PAGE, mimetype="text/html"))


def load(app):
    app.register_blueprint(bp)