import os
import time
from flask import Blueprint, jsonify, request, abort, Response
from CTFd.models import Solves, Users, Challenges
from CTFd.utils.scores import get_standings

KEY = os.getenv("BIGSCREEN_KEY", "")
bp = Blueprint("bigscreen", __name__)

# Tiny cache so several screens / fast polling never hammer the database.
_cache = {"t": 0.0, "v": None}
CACHE_SECONDS = 2


def _check():
    if not KEY or request.args.get("key") != KEY:
        abort(403)


def _no_store(resp):
    resp.headers["Cache-Control"] = "no-store"
    return resp


def _build():
    # --- first bloods: earliest solve of each challenge, hidden/banned excluded ---
    solves = (
        Solves.query.join(Users, Solves.user_id == Users.id)
        .join(Challenges, Solves.challenge_id == Challenges.id)
        .filter(Users.hidden == False, Users.banned == False)  # noqa: E712
        .order_by(Solves.date.asc())
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

    # --- full scoreboard: every account, sorted by score ---
    # (users in user mode, teams in team mode; hidden/banned already excluded)
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


PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Capture the Cup - Live</title>
<!-- Pull in the theme's own stylesheet so fonts/colors match the site -->
<link rel="stylesheet" href="/themes/mytheme/static/custom/css/capture-the-cup.css">
<style>
 /* Change these 5 values to match your theme exactly */
 :root{
   --bs-bg:#0b0f1a;
   --bs-panel:#151b2e;
   --bs-accent:#f5c542;
   --bs-text:#ffffff;
   --bs-blood:#7a0000;
 }
 *{box-sizing:border-box}
 html,body{height:100%}
 body{margin:0;background:var(--bs-bg);color:var(--bs-text);overflow:hidden;
      font-family:inherit,system-ui,-apple-system,"Segoe UI",sans-serif}
 .app{display:grid;grid-template-rows:auto 1fr;height:100vh;padding:1.2rem 1.6rem;gap:1rem}
 header{display:flex;align-items:center;gap:1rem}
 header img{height:clamp(36px,6vh,64px);width:auto}
 header h1{margin:0;font-size:clamp(1.2rem,3.2vh,2.2rem);letter-spacing:.12em;text-transform:uppercase}
 .live{margin-left:auto;display:flex;align-items:center;gap:.5rem;font-size:clamp(.8rem,1.8vh,1.1rem);opacity:.85}
 .dot{width:.8em;height:.8em;border-radius:50%;background:#2ecc71;animation:pulse 1.4s infinite}
 .dot.off{background:#e74c3c;animation:none}
 @keyframes pulse{50%{opacity:.25}}
 main{display:grid;grid-template-columns:minmax(260px,1fr) 3fr;gap:1.4rem;min-height:0}
 section{display:flex;flex-direction:column;min-height:0}
 h2{margin:0 0 .7rem;color:var(--bs-accent);letter-spacing:.14em;font-size:clamp(.9rem,2.2vh,1.3rem)}
 #board{display:grid;grid-auto-flow:column;gap:6px;flex:1;min-height:0;overflow:hidden}
 #bloods{display:flex;flex-direction:column;gap:6px;overflow:hidden}
 .row{display:flex;align-items:center;justify-content:space-between;gap:.8rem;
      background:var(--bs-panel);border-radius:8px;padding:0 1rem;min-width:0;
      border-left:4px solid transparent}
 .row .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
 .row .rk{display:inline-block;min-width:2.2em;opacity:.7}
 .row b{color:var(--bs-accent);font-variant-numeric:tabular-nums}
 .row.r1{border-left-color:#f5c542}
 .row.r2{border-left-color:#c0c7d1}
 .row.r3{border-left-color:#cd7f32}
 .row.up{animation:flash 1.6s}
 @keyframes flash{0%{background:#1f6f3c;transform:scale(1.02)}100%{background:var(--bs-panel);transform:none}}
 #bloods .row{padding:.55rem .9rem;font-size:clamp(.85rem,2vh,1.2rem)}
 .empty{opacity:.5;padding:1rem}
 #overlay{position:fixed;inset:0;display:none;flex-direction:column;align-items:center;justify-content:center;
   background:radial-gradient(circle,var(--bs-blood),#1a0000);text-align:center;z-index:10;padding:2rem}
 #overlay.show{display:flex;animation:pop .5s}
 #overlay .big{font-size:clamp(2.5rem,11vh,7rem);font-weight:800;letter-spacing:.05em}
 #overlay .team{font-size:clamp(2rem,9vh,6rem);color:var(--bs-accent);margin:1rem 0;word-break:break-word}
 #overlay .chal{font-size:clamp(1.2rem,5vh,3.2rem)}
 #overlay .by{font-size:clamp(1rem,3vh,2rem);opacity:.8;margin-top:.8rem}
 @keyframes pop{from{transform:scale(.6);opacity:0}to{transform:scale(1);opacity:1}}
 @media (max-width:900px){
   main{grid-template-columns:1fr;grid-template-rows:auto 1fr}
   #bloods .row:nth-child(n+4){display:none}
 }
</style></head><body>
<div class="app">
 <header>
  <img src="/themes/mytheme/static/img/logo1.png" alt="" onerror="this.style.display='none'">
  <h1>Capture the Cup</h1>
  <div class="live"><span class="dot" id="dot"></span><span id="status">LIVE</span></div>
 </header>
 <main>
  <section><h2>FIRST BLOODS</h2><div id="bloods"></div></section>
  <section><h2>SCOREBOARD <span id="count" style="opacity:.6"></span></h2><div id="board"></div></section>
 </main>
</div>
<div id="overlay">
 <div class="big">&#129656; FIRST BLOOD</div>
 <div class="team" id="ot"></div>
 <div class="chal" id="oc"></div>
 <div class="by" id="ob"></div>
</div>
<script>
const key = new URLSearchParams(location.search).get("key");
const $ = id => document.getElementById(id);
const boardEl = $("board"), bloodsEl = $("bloods"), overlay = $("overlay");
const ESC = {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"};
const esc = s => String(s).replace(/[&<>"]/g, c => ESC[c]);

let known = null, queue = [], showing = false, prev = {}, lastN = 0;

/* ---------- first blood announcements ---------- */
function next(){
  if(!queue.length){ showing = false; return; }
  showing = true;
  const b = queue.shift();
  $("ot").textContent = b.team;
  $("oc").textContent = b.challenge + " (" + b.category + ")";
  $("ob").textContent = b.user !== b.team ? "solved by " + b.user : "";
  overlay.className = "show";
  setTimeout(() => { overlay.className = ""; setTimeout(next, 500); }, 8000);
}

/* ---------- dynamic layout: fits any number of players on any screen ---------- */
function layout(n){
  const H = boardEl.clientHeight, W = boardEl.clientWidth, GAP = 6;
  const MIN = 40, MAX = 76;
  const cap = Math.max(1, Math.floor((H + GAP) / (MIN + GAP)));
  let cols = Math.min(3, Math.max(1, Math.ceil(n / cap)));
  if(W < 700) cols = 1;
  const rows = Math.max(1, Math.ceil(n / cols));
  const rowH = Math.max(MIN, Math.min(MAX, Math.floor((H - (rows - 1) * GAP) / rows)));
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
      return '<div class="' + cls + '"><span class="nm"><span class="rk">' + (i + 1) + '.</span>' +
             esc(t.name) + '</span><b>' + t.score + '</b></div>';
    }).join("");
  }
  prev = {};
  standings.forEach(t => prev[t.id] = t.score);
  boardEl.scrollTop = keep;
  $("count").textContent = "(" + standings.length + ")";
  lastN = standings.length;
}

/* ---------- polling ---------- */
async function tick(){
  try{
    const r = await fetch("/bigscreen/data?key=" + encodeURIComponent(key), {cache: "no-store"});
    if(!r.ok) throw new Error(r.status);
    const d = await r.json();

    if(known === null){
      known = new Set(d.bloods.map(b => b.challenge_id));   // first load: stay silent
    } else {
      d.bloods.forEach(b => {
        if(!known.has(b.challenge_id)){ known.add(b.challenge_id); queue.push(b); }
      });
    }
    if(!showing) next();

    bloodsEl.innerHTML = d.bloods.length
      ? d.bloods.slice().reverse().slice(0, 8).map(b =>
          '<div class="row"><span class="nm">&#129656; ' + esc(b.challenge) + '</span><b>' + esc(b.team) + '</b></div>').join("")
      : '<div class="empty">No first blood yet</div>';

    render(d.standings);
    $("dot").className = "dot"; $("status").textContent = "LIVE";
  }catch(e){
    $("dot").className = "dot off"; $("status").textContent = "RECONNECTING";
  }
}

/* slow auto-scroll, only when the list is taller than the screen */
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