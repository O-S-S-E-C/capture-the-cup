import math
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


def _ball():
    """Football SVG symbol (navy patches on a white ball), generated once."""
    def poly(x, y, r, a0):
        return " ".join(
            "%.1f,%.1f" % (x + r * math.cos(math.radians(a0 + 72 * k)),
                           y + r * math.sin(math.radians(a0 + 72 * k)))
            for k in range(5)
        )

    patches = ['<polygon points="%s"/>' % poly(50, 50, 15, -90)]
    seams = []
    for k in range(5):
        th = -90 + 72 * k
        c, s = math.cos(math.radians(th)), math.sin(math.radians(th))
        patches.append('<polygon points="%s"/>' % poly(50 + 48 * c, 50 + 48 * s, 15, th + 180))
        seams.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (
            50 + 15 * c, 50 + 15 * s, 50 + 33 * c, 50 + 33 * s))
    return (
        '<symbol id="ball" viewBox="0 0 100 100"><defs>'
        '<radialGradient id="ballg" cx=".36" cy=".3" r=".85"><stop offset="0" stop-color="#fff"/>'
        '<stop offset=".65" stop-color="#e3ebf8"/><stop offset="1" stop-color="#7f95bd"/></radialGradient>'
        '<radialGradient id="balls" cx=".4" cy=".35" r=".75"><stop offset=".55" stop-color="#001040" stop-opacity="0"/>'
        '<stop offset="1" stop-color="#001040" stop-opacity=".5"/></radialGradient>'
        '<clipPath id="ballc"><circle cx="50" cy="50" r="48"/></clipPath></defs>'
        '<circle cx="50" cy="50" r="48" fill="url(#ballg)"/>'
        '<g clip-path="url(#ballc)" fill="#0a1b55" stroke="#0a1b55" stroke-width="1.4" stroke-linejoin="round">'
        + "".join(patches) +
        '</g><g stroke="#0a1b55" stroke-width="2.2" stroke-linecap="round">' + "".join(seams) + '</g>'
        '<circle cx="50" cy="50" r="48" fill="url(#balls)"/>'
        '<circle cx="50" cy="50" r="47.2" fill="none" stroke="#75d8ff" stroke-opacity=".7" stroke-width="1.6"/>'
        '</symbol>'
    )


PAGE = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Capture the Cup - Live</title>
<link rel="stylesheet" href="/themes/mytheme/static/custom/css/capture-the-cup.css">
<style>
:root{--night:#05070f;--panel:#0d1526;--raised:#131e35;--ink:#f5f8ff;--muted:#8d9db6;
 --blue:#2f8cff;--cyan:#38bdf8;--cyan2:#75d8ff;--red:#ff2d55;--red2:#ff7f93;--line:rgba(153,181,219,.18)}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;overflow:hidden;color:var(--ink);font-family:Lato,system-ui,sans-serif;background:var(--night)}
h1,h2,.title{font-family:Raleway,Lato,sans-serif}

/* ---------- pitch backdrop ---------- */
.pitch{position:fixed;inset:0;z-index:0;pointer-events:none;
 background:
  radial-gradient(circle at 10% 0,rgba(47,140,255,.2),transparent 34%),
  radial-gradient(circle at 92% 20%,rgba(255,45,85,.15),transparent 32%),
  repeating-linear-gradient(90deg,rgba(56,189,248,.03) 0 7vw,transparent 7vw 14vw),var(--night)}
.pitch svg{position:absolute;inset:0;width:100%;height:100%}

.app{position:relative;z-index:1;display:grid;grid-template-rows:auto 1fr;height:100vh;padding:1.2rem 1.6rem;gap:1rem}
header{position:relative;display:flex;flex-wrap:wrap;align-items:center;gap:1rem;padding-bottom:.9rem}
header::after{content:"";position:absolute;left:0;right:0;bottom:0;height:3px;
 background:linear-gradient(90deg,var(--blue),var(--red));box-shadow:0 0 14px rgba(47,140,255,.7),0 0 14px rgba(255,45,85,.5)}
header img{height:clamp(36px,6vh,64px)}
header h1{margin:0;font-size:clamp(1.2rem,3.2vh,2.2rem);letter-spacing:.14em;text-transform:uppercase;text-shadow:0 0 18px rgba(56,189,248,.45)}
.live{margin-left:1.2rem;display:flex;align-items:center;gap:.5rem;font-size:clamp(.8rem,1.8vh,1.1rem);color:var(--cyan2)}
.dot{width:.7em;height:.7em;border-radius:50%;background:var(--cyan);box-shadow:0 0 10px var(--cyan);animation:pulse 1.4s infinite}
.dot.off{background:var(--red);box-shadow:0 0 10px var(--red);animation:none}
@keyframes pulse{50%{opacity:.25}}
main{display:grid;min-height:0}
section{display:flex;flex-direction:column;min-height:0}
h2{margin:0 0 .7rem;color:var(--cyan2);letter-spacing:.18em;font-size:clamp(.9rem,2.2vh,1.3rem)}
#board{display:grid;gap:6px;flex:1;min-height:0;overflow:hidden}
.row{position:relative;display:flex;align-items:center;justify-content:space-between;gap:.8rem;background:linear-gradient(90deg,rgba(19,30,53,.92),rgba(13,21,38,.92));
 border:1px solid var(--line);border-left:4px solid var(--line);border-radius:8px;padding:0 1rem;min-width:0}
.nm{display:flex;align-items:center;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.rk{min-width:2.2em;opacity:.65;font-variant-numeric:tabular-nums}
.row b{color:var(--cyan2);font-variant-numeric:tabular-nums;background:rgba(5,7,15,.7);border:1px solid var(--line);border-radius:6px;padding:.05em .5em}
.ci{width:1.2em;height:1.2em;margin-right:.45em;flex:none;filter:drop-shadow(0 0 6px rgba(117,216,255,.8))}
.row.r1{border-left-color:var(--cyan2);border-color:rgba(117,216,255,.55);background:linear-gradient(90deg,rgba(56,189,248,.25),rgba(13,21,38,.92) 60%);box-shadow:0 0 22px rgba(56,189,248,.25)}
.row.r2{border-left-color:var(--blue);background:linear-gradient(90deg,rgba(47,140,255,.14),rgba(13,21,38,.92) 55%)}
.row.r3{border-left-color:var(--red);background:linear-gradient(90deg,rgba(255,45,85,.14),rgba(13,21,38,.92) 55%)}
.row.up{animation:rowflash 1.6s}
@keyframes rowflash{0%{background:#12466a;transform:scale(1.02)}100%{transform:none}}
.empty{color:var(--muted);padding:1rem}
.fb-card{position:relative;margin-left:auto;display:flex;align-items:center;gap:.8rem;min-width:0;max-width:min(58vw,52rem);
 padding:.4rem 1.1rem .4rem 1.2rem;background:linear-gradient(145deg,var(--raised),var(--panel));border:1px solid var(--line);border-radius:8px;
 box-shadow:0 0 24px rgba(47,140,255,.2)}
.fb-card::before{content:"";position:absolute;inset:0 auto 0 0;width:4px;border-radius:8px 0 0 8px;background:linear-gradient(var(--blue),var(--red));box-shadow:0 0 12px var(--blue)}
.fb-ball{width:clamp(30px,4.6vh,46px);height:clamp(30px,4.6vh,46px);flex:none;filter:drop-shadow(0 0 8px rgba(117,216,255,.7))}
.fb-body{min-width:0}
.fb-label{color:var(--red2);font-size:clamp(.6rem,1.2vh,.75rem);font-weight:800;letter-spacing:.18em}
.fb-line{display:flex;align-items:baseline;gap:.8rem;min-width:0;white-space:nowrap}
.fb-team{font-family:Raleway,Lato,sans-serif;font-size:clamp(1rem,2.6vh,1.6rem);font-weight:800;overflow:hidden;text-overflow:ellipsis;flex:0 1 auto}
.fb-chal{font-size:clamp(.8rem,1.8vh,1.05rem);color:var(--cyan2);overflow:hidden;text-overflow:ellipsis;flex:0 1 auto}
.fb-meta{color:var(--muted);font-size:clamp(.7rem,1.4vh,.85rem);overflow:hidden;text-overflow:ellipsis;flex:0 100 auto}
.fb-card.empty{opacity:.7}

/* =====================================================
   FIRST BLOOD CELEBRATION  (impact of the shot = 1.2s)
   ===================================================== */
#overlay{position:fixed;inset:0;display:none;align-items:center;justify-content:center;z-index:10;overflow:hidden;
 background:radial-gradient(circle at 20% 0,rgba(47,140,255,.35),transparent 48%),radial-gradient(circle at 80% 0,rgba(255,45,85,.3),transparent 48%),#03050b}
#overlay.show{display:flex;animation:fadein .2s}
@keyframes fadein{from{opacity:0}}

/* neon pitch floor */
.floor{position:absolute;left:-50%;right:-50%;bottom:-6vh;height:60vh;z-index:0;pointer-events:none;
 background:repeating-linear-gradient(90deg,rgba(56,189,248,.55) 0 2px,transparent 2px 90px),repeating-linear-gradient(0deg,rgba(255,45,85,.5) 0 2px,transparent 2px 64px);
 transform:perspective(520px) rotateX(64deg);transform-origin:50% 100%;
 -webkit-mask-image:linear-gradient(to top,#000 15%,transparent 92%);mask-image:linear-gradient(to top,#000 15%,transparent 92%);
 animation:grid 1.6s linear infinite}
@keyframes grid{from{background-position:0 0,0 0}to{background-position:0 0,0 64px}}

/* stadium floodlights */
.beam{position:absolute;top:-12vh;width:28vw;height:125vh;z-index:0;transform-origin:50% 0;pointer-events:none;mix-blend-mode:screen;opacity:0;
 clip-path:polygon(46% 0,54% 0,100% 100%,0 100%);
 animation:beamon .9s linear .25s forwards,sweep 6s ease-in-out 1.2s infinite alternate}
.beam.b1{left:2vw;background:linear-gradient(rgba(47,140,255,.85),transparent 85%);--a1:-6deg;--a2:-26deg}
.beam.b2{left:18vw;background:linear-gradient(rgba(117,216,255,.7),transparent 85%);--a1:8deg;--a2:-14deg}
.beam.b3{right:18vw;background:linear-gradient(rgba(255,127,147,.7),transparent 85%);--a1:-8deg;--a2:14deg}
.beam.b4{right:2vw;background:linear-gradient(rgba(255,45,85,.85),transparent 85%);--a1:6deg;--a2:26deg}
@keyframes beamon{0%{opacity:0}15%{opacity:.95}25%{opacity:.1}40%{opacity:1}55%{opacity:.25}75%{opacity:.9}100%{opacity:.7}}
@keyframes sweep{from{transform:rotate(var(--a1))}to{transform:rotate(var(--a2))}}

/* crowd camera flashes */
#cams{position:absolute;inset:0;z-index:1;pointer-events:none}
#cams b{position:absolute;width:5px;height:5px;border-radius:50%;background:#fff;opacity:0;
 box-shadow:0 0 22px 10px rgba(255,255,255,.6),0 0 60px 24px rgba(117,216,255,.25);
 animation:cam var(--d) linear var(--w) infinite}
@keyframes cam{0%,100%{opacity:0;transform:scale(.3)}3%{opacity:1;transform:scale(1.6)}9%{opacity:0;transform:scale(.6)}}

/* rays + confetti burst on impact */
.rays{position:absolute;width:170vmax;height:170vmax;left:50%;top:34%;margin:-85vmax 0 0 -85vmax;pointer-events:none;z-index:1;opacity:0;
 background:repeating-conic-gradient(rgba(47,140,255,.28) 0 6deg,transparent 6deg 12deg,rgba(255,45,85,.24) 12deg 18deg,transparent 18deg 24deg);
 -webkit-mask:radial-gradient(circle,#000,transparent 55%);mask:radial-gradient(circle,#000,transparent 55%);
 animation:raysin .8s ease-out 1.2s forwards,spin 36s linear 1.2s infinite}
@keyframes raysin{to{opacity:1}}
@keyframes spin{to{transform:rotate(360deg)}}
#confetti{position:absolute;inset:0;pointer-events:none;z-index:2}
#confetti i{position:absolute;top:-4vh;left:var(--x);width:var(--s);height:calc(var(--s)*1.7);background:var(--c);opacity:.95;
 box-shadow:0 0 8px var(--c);animation:fall var(--d) linear var(--w) forwards}
@keyframes fall{to{transform:translate3d(var(--dx),108vh,0) rotate(var(--r))}}

/* main content (shakes on impact) */
.shake{position:relative;z-index:3;display:flex;flex-direction:column;align-items:center;text-align:center;padding:0 2vw;
 animation:shake .7s linear 1.2s}
@keyframes shake{0%,100%{transform:none}10%{transform:translate(-14px,8px) rotate(-.6deg)}20%{transform:translate(12px,-10px) rotate(.5deg)}
 30%{transform:translate(-9px,-6px)}45%{transform:translate(7px,6px)}60%{transform:translate(-4px,3px)}80%{transform:translate(2px,-2px)}}

/* goal + ball */
.stage{position:relative;width:min(84vw,66vh);aspect-ratio:2/1}
.goal{width:100%;height:100%;display:block;overflow:visible;animation:goalflash 1.2s ease-out 1.2s}
.goal .pl{filter:drop-shadow(0 0 7px #2f8cff) drop-shadow(0 0 18px #2f8cff)}
.goal .pr{filter:drop-shadow(0 0 7px #ff2d55) drop-shadow(0 0 18px #ff2d55)}
.goal .pb{filter:drop-shadow(0 0 10px #a46bff)}
.goal .net{transform-box:fill-box;transform-origin:50% 40%;animation:ripple 1.3s ease-out 1.2s}
@keyframes goalflash{0%{filter:drop-shadow(0 0 70px #fff) brightness(2)}100%{filter:none}}
@keyframes ripple{0%{transform:none;filter:brightness(1)}16%{transform:scale(1.08,1.12);filter:brightness(3)}
 36%{transform:scale(.96,.94)}56%{transform:scale(1.03,1.04)}78%{transform:scale(.99)}100%{transform:none;filter:brightness(1)}}
.ball{position:absolute;left:50%;top:50%;width:13%;aspect-ratio:1;z-index:2;
 filter:blur(0) drop-shadow(0 0 14px rgba(117,216,255,.9));
 animation:shot .7s cubic-bezier(.35,0,.7,1) .5s both,settle 1.7s ease-out 1.2s forwards}
@keyframes shot{
 0%{transform:translate(-170%,calc(-50% + 72vh)) scale(3.4) rotate(0deg);filter:blur(10px) drop-shadow(0 0 14px rgba(117,216,255,.9))}
 100%{transform:translate(-50%,-50%) scale(1) rotate(900deg);filter:blur(0) drop-shadow(0 0 14px rgba(117,216,255,.9))}}
@keyframes settle{
 0%{transform:translate(-50%,-50%) scale(1) rotate(900deg)}
 28%{transform:translate(-50%,calc(-50% + 11vh)) scale(1) rotate(1010deg);animation-timing-function:ease-out}
 48%{transform:translate(-50%,calc(-50% + 6vh)) scale(1) rotate(1060deg);animation-timing-function:ease-in}
 66%{transform:translate(-50%,calc(-50% + 11vh)) scale(1) rotate(1110deg);animation-timing-function:ease-out}
 80%{transform:translate(-50%,calc(-50% + 9vh)) scale(1) rotate(1135deg);animation-timing-function:ease-in}
 100%{transform:translate(-50%,calc(-50% + 11vh)) scale(1) rotate(1160deg)}}
.ring{position:absolute;left:50%;top:50%;width:30%;aspect-ratio:1;border-radius:50%;border:4px solid var(--cyan2);
 box-shadow:0 0 24px var(--blue),inset 0 0 24px var(--blue);opacity:0;transform:translate(-50%,-50%) scale(0);animation:shock 1.5s ease-out 1.2s both}
.ring.r2{border-color:var(--red);box-shadow:0 0 24px var(--red),inset 0 0 24px var(--red);animation-delay:1.35s}
@keyframes shock{0%{transform:translate(-50%,-50%) scale(.1);opacity:1}100%{transform:translate(-50%,-50%) scale(8);opacity:0}}

/* text */
.eyebrow{margin-top:2vh;color:var(--red);font-weight:900;font-style:italic;letter-spacing:.45em;font-size:clamp(1rem,3vh,2rem);
 text-shadow:0 0 12px var(--red),0 0 34px var(--red);animation:up .6s cubic-bezier(.2,.9,.3,1) 1.35s both,neon 2.4s ease-in-out 2s infinite}
@keyframes neon{0%,100%{opacity:1}46%{opacity:1}48%{opacity:.35}50%{opacity:1}54%{opacity:.5}56%{opacity:1}}
.title{position:relative;display:inline-block;white-space:nowrap;margin:.2vh 0;font-size:min(13vh,12vw);font-weight:900;line-height:1;letter-spacing:.03em;color:#fff;
 transform:skewX(-8deg);text-shadow:0 0 28px rgba(117,216,255,.75),0 0 80px rgba(47,140,255,.5);animation:slam .7s cubic-bezier(.2,.9,.2,1.1) 1.3s both}
.title::before,.title::after{content:attr(data-text);position:absolute;left:0;top:0;width:100%;mix-blend-mode:screen;pointer-events:none}
.title::before{color:#2f8cff;transform:translate(-.045em,0);animation:split1 2.6s ease-in-out 2s infinite}
.title::after{color:#ff2d55;transform:translate(.045em,0);animation:split2 2.6s ease-in-out 2s infinite}
@keyframes split1{0%,100%{transform:translate(-.045em,0)}50%{transform:translate(-.1em,.01em)}}
@keyframes split2{0%,100%{transform:translate(.045em,0)}50%{transform:translate(.1em,-.01em)}}
@keyframes slam{0%{transform:scale(3.4) skewX(-8deg);opacity:0;filter:blur(20px)}
 60%{transform:scale(.95) skewX(-8deg);opacity:1;filter:blur(0)}100%{transform:scale(1) skewX(-8deg)}}
.team{position:relative;margin:1.4vh 0 .6vh;padding-bottom:1.5vh;max-width:92vw;font-family:Raleway,Lato,sans-serif;font-size:min(9vh,9vw);font-weight:800;word-break:break-word;
 text-shadow:0 0 40px rgba(56,189,248,.6);animation:up .7s cubic-bezier(.2,.9,.3,1) 1.65s both}
.team::after{content:"";position:absolute;left:50%;bottom:0;height:.6vh;min-height:4px;width:0;transform:translateX(-50%);
 background:linear-gradient(90deg,var(--blue),var(--red));box-shadow:0 0 14px var(--blue),0 0 14px var(--red);animation:bar 1s cubic-bezier(.2,.9,.3,1) 1.9s forwards}
@keyframes bar{to{width:80%}}
.plate{display:inline-flex;align-items:stretch;margin-top:1.4vh;font-weight:800;font-style:italic;font-size:clamp(1rem,3.6vh,2.4rem);
 transform:skewX(-10deg);box-shadow:0 0 30px rgba(47,140,255,.4);animation:plate .6s cubic-bezier(.2,.9,.3,1) 1.9s both}
.plate .cat{background:var(--red);padding:.15em .7em;letter-spacing:.14em;text-transform:uppercase}
.plate .chal{background:rgba(47,140,255,.2);border:2px solid var(--blue);border-left:0;padding:.15em .8em;color:var(--cyan2)}
@keyframes plate{from{transform:skewX(-10deg) translateX(-70px);opacity:0}}
.by{font-size:clamp(1rem,2.8vh,1.8rem);color:var(--muted);margin-top:1.2vh;animation:up .6s cubic-bezier(.2,.9,.3,1) 2.1s both}
@keyframes up{from{transform:translateY(30px);opacity:0}}

/* ticker */
.ticker{position:absolute;left:0;right:0;bottom:0;z-index:4;height:clamp(28px,5.2vh,56px);display:flex;align-items:center;overflow:hidden;
 background:linear-gradient(90deg,#1456d6,#ff2d55);box-shadow:0 -6px 30px rgba(47,140,255,.5);transform:translateY(105%);animation:tkup .5s ease-out 1.8s forwards}
#tk{white-space:nowrap;font-weight:900;font-style:italic;letter-spacing:.2em;font-size:clamp(.8rem,2.4vh,1.4rem);animation:marq 26s linear infinite}
@keyframes tkup{to{transform:none}}
@keyframes marq{to{transform:translateX(-50%)}}

/* opening wipe + impact flash */
.wipe{position:absolute;top:-10%;bottom:-10%;width:150%;left:-170%;z-index:9;pointer-events:none;transform:skewX(-20deg);animation:wipe .9s cubic-bezier(.7,0,.3,1) forwards}
.wipe.a{background:var(--blue)}
.wipe.b{background:var(--red);animation-delay:.12s}
@keyframes wipe{from{left:-170%}to{left:130%}}
.whiteout{position:absolute;inset:0;z-index:8;background:#fff;opacity:0;pointer-events:none;animation:whiteout 1.1s ease-out 1.2s forwards}
@keyframes whiteout{0%{opacity:0}3%{opacity:1}100%{opacity:0}}

/* ---- sound gate ---- */
#gate{position:fixed;inset:0;z-index:20;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1.2rem;
 background:radial-gradient(circle at 25% 10%,rgba(47,140,255,.3),transparent 45%),radial-gradient(circle at 75% 90%,rgba(255,45,85,.26),transparent 45%),var(--night);
 cursor:pointer;text-align:center}
#gate svg{width:clamp(90px,20vh,200px);filter:drop-shadow(0 0 24px rgba(117,216,255,.7));animation:bounce 1.2s cubic-bezier(.3,0,.6,1) infinite}
@keyframes bounce{0%,100%{transform:translateY(0) rotate(0)}50%{transform:translateY(-6vh) rotate(180deg)}}
#gate b{font-family:Raleway,Lato,sans-serif;letter-spacing:.3em;font-size:clamp(1.2rem,4vh,2.4rem);text-shadow:0 0 22px var(--blue)}
#gate span{color:var(--muted)}
@media(max-width:900px){.fb-meta{display:none}}
@media(max-width:620px){.app{padding:.9rem 1rem}.fb-card{order:3;flex-basis:100%;max-width:none;margin-left:0}}
@media(prefers-reduced-motion:reduce){.rays,#gate svg,.floor,.beam{animation:none}}
</style></head><body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs></defs>__BALL__</svg>

<div class="pitch"><svg viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" fill="none" stroke="rgba(117,216,255,.09)" stroke-width="3">
 <rect x="40" y="40" width="1520" height="820"/><line x1="800" y1="40" x2="800" y2="860"/><circle cx="800" cy="450" r="130"/><circle cx="800" cy="450" r="6" fill="rgba(117,216,255,.12)"/>
 <rect x="40" y="250" width="200" height="400"/><rect x="40" y="350" width="80" height="200"/>
 <rect x="1360" y="250" width="200" height="400"/><rect x="1480" y="350" width="80" height="200"/>
</svg></div>

<div id="gate"><svg viewBox="0 0 100 100"><use href="#ball"/></svg><b>CAPTURE THE CUP</b><span>Click once to kick off the big screen with sound</span></div>

<div class="app">
 <header>
  <img src="/themes/mytheme/static/img/logo1.png" alt="" onerror="this.style.display='none'">
  <h1>Capture the Cup</h1>
  <aside class="fb-card empty" id="fb" aria-live="polite">
   <svg class="fb-ball" viewBox="0 0 100 100"><use href="#ball"/></svg>
   <div class="fb-body">
    <div class="fb-label">LATEST CAPTURE</div>
    <div class="fb-line"><span class="fb-team" id="fb-team">Waiting for the first solve</span><span class="fb-chal" id="fb-chal">The next capture will appear here</span><span class="fb-meta" id="fb-meta"></span></div>
   </div>
  </aside>
  <div class="live"><span class="dot" id="dot"></span><span id="status">LIVE</span></div>
 </header>
 <main><section><h2>SCOREBOARD <span id="count" style="opacity:.6"></span></h2><div id="board"></div></section></main>
</div>

<div id="overlay">
 <div class="floor"></div>
 <div class="beam b1"></div><div class="beam b2"></div><div class="beam b3"></div><div class="beam b4"></div>
 <div id="cams"></div>
 <div class="rays"></div><div id="confetti"></div>

 <div class="shake">
  <div class="stage">
   <svg class="goal" viewBox="0 0 600 300">
    <defs>
     <pattern id="netp" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0H14M0 0V14" stroke="rgba(255,255,255,.42)" stroke-width="1" fill="none"/></pattern>
     <linearGradient id="barg" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="#2f8cff"/><stop offset="1" stop-color="#ff2d55"/></linearGradient>
    </defs>
    <g class="net">
     <rect x="40" y="40" width="520" height="250" fill="url(#netp)"/>
     <rect x="105" y="85" width="390" height="175" fill="rgba(5,7,15,.55)" stroke="rgba(255,255,255,.3)"/>
     <rect x="105" y="85" width="390" height="175" fill="url(#netp)"/>
     <g stroke="rgba(255,255,255,.35)" stroke-width="1.2"><line x1="40" y1="40" x2="105" y2="85"/><line x1="560" y1="40" x2="495" y2="85"/><line x1="40" y1="290" x2="105" y2="260"/><line x1="560" y1="290" x2="495" y2="260"/></g>
    </g>
    <rect class="pl" x="34" y="34" width="12" height="262" rx="6" fill="#2f8cff"/>
    <rect class="pr" x="554" y="34" width="12" height="262" rx="6" fill="#ff2d55"/>
    <rect class="pb" x="34" y="34" width="532" height="12" rx="6" fill="url(#barg)"/>
    <line x1="-40" x2="640" y1="297" y2="297" stroke="rgba(255,255,255,.55)" stroke-width="2"/>
   </svg>
   <svg class="ball" viewBox="0 0 100 100"><use href="#ball"/></svg>
   <i class="ring"></i><i class="ring r2"></i>
  </div>
  <div class="eyebrow">GOOOAL!</div>
  <div class="title" data-text="FIRST BLOOD">FIRST BLOOD</div>
  <div class="team" id="ot"></div>
  <div class="plate"><span class="cat" id="ocat"></span><span class="chal" id="oc"></span></div>
  <div class="by" id="ob"></div>
 </div>

 <div class="ticker"><div id="tk"></div></div>
 <div class="wipe a"></div><div class="wipe b"></div>
 <div class="whiteout"></div>
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

/* crowd camera flashes (built once, they start popping at the moment of impact) */
(function(){
  const box = $("cams");
  for(let i = 0; i < 46; i++){
    const e = document.createElement("b");
    e.style.cssText = "left:" + (Math.random()*100) + "%;top:" + (6 + Math.random()*90) + "%;--d:" + (1.6 + Math.random()*3) + "s;--w:" + (1.2 + Math.random()*4) + "s";
    box.appendChild(e);
  }
})();

function confetti(){
  const box = $("confetti"), cols = ["#2f8cff","#75d8ff","#ff2d55","#ff7f93","#ffffff"];
  box.innerHTML = "";
  for(let i = 0; i < 110; i++){
    const e = document.createElement("i");
    e.style.cssText = "--x:" + (Math.random()*100) + "%;--s:" + (6 + Math.random()*9) + "px;--c:" + cols[i % cols.length] +
      ";--d:" + (3 + Math.random()*3) + "s;--w:" + (1.2 + Math.random()*2) + "s;--dx:" + ((Math.random()-.5)*200) + "px;--r:" + (360 + Math.random()*720) + "deg";
    box.appendChild(e);
  }
}

function next(){
  if(!queue.length){ showing = false; return; }
  showing = true;
  const b = queue.shift();
  $("ot").textContent = b.team;
  $("ocat").textContent = b.category;
  $("oc").textContent = b.challenge;
  $("ob").textContent = b.user !== b.team ? "captured by " + b.user : "";
  $("tk").textContent = ("FIRST BLOOD  \u2605  " + b.team + "  \u2605  " + b.challenge + "  \u2605  ").repeat(14);
  overlay.className = ""; void overlay.offsetWidth;   // restart the animations
  confetti();
  overlay.className = "show";
  if(soundOn){ snd.currentTime = 0; snd.play().catch(() => {}); }
  setTimeout(() => { overlay.className = ""; setTimeout(next, 500); }, 10000);
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
      const icon = i === 0 ? '<svg class="ci" viewBox="0 0 100 100"><use href="#ball"/></svg>' : "";
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
</script></body></html>""".replace("__BALL__", _ball())


@bp.route("/bigscreen")
def page():
    _check()
    return _no_store(Response(PAGE, mimetype="text/html"))


def load(app):
    app.register_blueprint(bp)