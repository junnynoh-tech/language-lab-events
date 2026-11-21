"""Shared Language Lab page builder (SPAN 1001, SPAN 1002, ...).

Each course keeps its content in its own source folder (<course>-labs.json, vocab.json,
guidelines-quiz.json, quizzes.json). Point the builder at that folder:

    python3 labs/lab-builder/build_all.py labs/span1002/labs-2026/source

or run one step with LABS_COURSE=<source folder> python3 labs/lab-builder/build.py

Section types ("variants": in person, online, Stone, summer...) are defined in the course
config. Each variant can reorder the labs, change a lab's title or chapter label, use a
different due-date key from the lab hub, offer WCONLINE tutoring ("tutoring": "in person" or "online"),
and offer the lab session service for recording Bongo in the Lab ("inlab", regular in-person sections only).
Stone sections don't use lab sessions; like online sections, they book tutoring if they need help.

Writes into the course folder (V = variant key):
  d2l/<code>-announcement-V.html        announcement with buttons + getting-started steps
  d2l/<code>-lab-folder-V.html          LAB folder description
  d2l/<code>-guidelines-quiz.html       Guidelines Quiz description
  d2l/<code>-lab-N-quiz[-V].html        mini-quiz descriptions (start page); suffixed only for
                                        variants whose order or dates differ from the first
  d2l/<code>-spanish-keyboard.html      keyboard tutorial
  github/<code>-lab-N-bongo-V.html      Bongo instructions (GitHub Pages)
Due dates come from the lab hub's lab-due-dates.json at build time.
"""
from urllib.parse import quote
import json, re, html, os
from datetime import date
from pathlib import Path
import keyboard as K

ENGINE = Path(__file__).resolve().parent
HERE = Path(os.environ.get("LABS_COURSE", ENGINE.parent / "span1001" / "labs-regular-2026" / "source")).resolve()
OUT = HERE.parent
C = json.loads(next(HERE.glob("*-labs.json")).read_text(encoding="utf8"))
POLICY = json.loads((ENGINE / "policy.json").read_text(encoding="utf8"))   # lab policy shared by every course
POLICY.update(C.get("policy_overrides", {}))
MINI_QUIZZES = C.get("mini_quizzes", True)
AUDIO = C.get("vocab_audio", False)            # chapter word lists get Forvo links and ▶ buttons
SLUG = C.get("page_slug", "bongo")              # file name part for lab pages
if C.get("locale") == "fr":
    import keyboard_fr as K, fr_locale
VOC = json.loads((HERE / "vocab.json").read_text(encoding="utf8"))
V = VOC["chapters"]
CODE = C["course_code"]                      # e.g. span1002
NUM = C["course"].split()[-1]                # e.g. 1002
_DD = json.loads((HERE / C["due_dates_json"]).resolve().read_text(encoding="utf8"))
SEMESTER = _DD["semester_label"]
QUIZZES = json.loads((HERE / "quizzes.json").read_text(encoding="utf8")) if (HERE / "quizzes.json").exists() else {}
LAB_BY_ID = {L["id"]: L for L in C["labs"]}
# One copy of the pages per campus: students see (and email) only their own Language Lab.
CAMPUSES = json.loads((HERE / C["campuses_json"]).resolve().read_text(encoding="utf8"))["campuses"]
if C.get("campus_codes"): CAMPUSES = [c for c in CAMPUSES if c["code"] in C["campus_codes"]]
CAMPUS = CAMPUSES[0]          # the campus being built; set_campus() switches it
def set_campus(code):
    global CAMPUS
    CAMPUS = next(c for c in CAMPUSES if c["code"] == code)

def e(s): return html.escape(s, quote=True)
def es(s):
    """*Spanish* -> <i lang="es">Spanish</i>; everything else escaped except <b> and <kbd>."""
    parts = re.split(r"\*([^*]+)\*", s)
    out = "".join(e(p) if i % 2 == 0 else f'<i lang="es">{e(p)}</i>' for i, p in enumerate(parts))
    return re.sub(r"&lt;(/?)(b|kbd)&gt;", r"<\1\2>", out)

# ---------------- variants ----------------

class Variant(dict):
    """A section type. .labs are the course labs in this variant's order, each with
    its number n, its due date, and the variant's overrides applied."""
    def __init__(self, key, cfg):
        super().__init__(cfg); self.key = key
        cls = next((c for c in _DD["classes"] if c["key"] == cfg.get("due_key")), None)
        self.due_day = cls["due_day"] if cls else None
        self.due_time = POLICY["due_time"] if cls else None   # the policy's due time; dates still come from the hub
        dates = {int(l["label"].split()[-1]): date.fromisoformat(l["date"]) for l in (cls or {}).get("labs", []) if l["label"].startswith("Lab ")}
        wk = {int(l["label"].split()[-1]): date.fromisoformat(l["date"]) for l in (cls or {}).get("labs", []) if l["label"].startswith("Workshop ")} if C.get("last_lab_workshop") else {}
        order = cfg.get("order") or [L["id"] for L in C["labs"]]
        self.labs = []
        for n, lid in enumerate(order, 1):
            L = dict(LAB_BY_ID[lid]); L.update(cfg.get("overrides", {}).get(lid, {}))
            L["n"] = n; L["date"] = dates.get(n) or (wk.get(n) if L.get("review") else None)
            if wk: L["workshop_date"] = wk.get(n)
            self.labs.append(L)
        self.signature = (tuple(order), cfg.get("due_key"), json.dumps(cfg.get("overrides", {}), sort_keys=True))
    @property
    def has_dates(self): return bool(self.due_time) and all(L["date"] for L in self.labs)
    def lab(self, lid): return next(L for L in self.labs if L["id"] == lid)

VARIANTS = [Variant(k, v) for k, v in C["variants"].items()]
VMAP = {v.key: v for v in VARIANTS}

def quiz_suffix(v):
    """Mini-quiz descriptions are shared by variants with the same order, dates and overrides."""
    first = next(x for x in VARIANTS if x.signature == v.signature)
    return "" if first.signature == VARIANTS[0].signature else f"-{first.key}"

def due(L, v):
    d = L["date"]
    return f"{d.strftime('%a, %b')} {d.day}, {v.due_time}" if d else "Due date in D2L"
def due_long(L, v):
    d = L["date"]
    return f"{d.strftime('%A, %B')} {d.day}, {v.due_time}" if d else "see D2L"
def due_chip(L, v):
    return f'<li class="due"><b>Due</b> {due(L, v)}</li>' if L["date"] else '<li class="due"><b>Due</b> date in D2L</li>'
def due_iso(L, v):
    """Due date and time for the browser (local time), e.g. 2026-09-04T15:00."""
    h, m = re.match(r"(\d+):(\d+)", v.due_time).groups(); h = int(h) % 12 + (12 if "PM" in v.due_time.upper() else 0)
    return f"{L['date'].isoformat()}T{h:02d}:{m}"

def when_text(v):
    if v.has_dates: return f"{v.due_day}s, {v.due_time}"
    # 2026-11-21: the due day is set (course registry) but the term's dates aren't published yet
    return f"{v.due_day}s, {v.due_time} (dates in D2L)" if v.due_day and v.due_time and C.get("due_day_known") else "dates in D2L"

AUDIO_CSS = """.au{display:inline-flex;gap:6px;margin-left:6px;vertical-align:middle;}.au .say{margin-left:0;}
.fv{display:inline-flex;align-items:center;min-height:36px;padding:0 8px;border:1px solid var(--line-2);border-radius:6px;background:var(--white);color:var(--navy);font-size:.8rem;}
@media print{.au{display:none!important;}}"""

CSS = """
:root{--navy:#002147;--navy-2:#0b2f5c;--blue:#005fa3;--sky:#9cc9ee;--red:#c8102e;--gold:#b8952a;--gold-dk:#7a5d14;--gold-lt:#fdf6e3;
--ink:#0d1525;--muted:#4a5f75;--cream:#f7f9fc;--white:#fff;--line:#d5e0ee;--line-2:#9fb3cc;--green:#1a5c1a;--green-lt:#eef8ee;--red-lt:#fff0f2;}
*,*::before,*::after{box-sizing:border-box;}
html,body{margin:0;padding:0;}
body{font-family:'DM Sans',Arial,sans-serif;font-size:17px;line-height:1.6;color:var(--ink);background:var(--cream);}
a{color:var(--blue);} a:hover{color:var(--navy);}
a:focus-visible,button:focus-visible,[tabindex]:focus-visible{outline:3px solid var(--gold);outline-offset:2px;}
.skip{position:absolute;left:-9999px;top:0;background:var(--gold-dk);color:#fff;padding:10px 16px;font-weight:700;z-index:100;}
.skip:focus{left:0;}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;}
header.top{background:var(--navy);color:#fff;padding:20px 28px;display:flex;align-items:center;gap:18px;}
.flag{display:flex;flex-direction:column;gap:3px;flex-shrink:0;position:relative;}.flag i{display:block;width:34px;height:5px;border-radius:2px;background:#c8102e;transition:background .9s ease;}.flag i:nth-child(2){background:#b8952a;}
.flag .flagtip{position:absolute;left:44px;top:-4px;background:rgba(0,0,0,.8);color:#fff;font:700 13px 'DM Sans',Arial,sans-serif;padding:3px 8px;border-radius:4px;white-space:nowrap;opacity:0;transition:opacity .2s;pointer-events:none;z-index:10;}
.flag:hover .flagtip{opacity:1;}
.top h1 .c{transition:color .9s ease;}
.top h1{font-family:'Fraunces',Georgia,serif;font-weight:900;font-size:1.65rem;line-height:1.15;margin:0;}
.top h1 .c{color:var(--sky);}
.top p{margin:2px 0 0;font-size:.95rem;color:#d6e2f0;}
.top .num{margin-left:auto;font-family:'Fraunces',Georgia,serif;font-weight:900;font-size:3rem;line-height:1;color:var(--sky);}
/* Console (2026-11-10, like the events console admin/console.html): the flag banner on top, then a white
   rail flush left with compact items, and the content using the full width. No vh units: in a D2L iframe
   the frame grows to fit the page, and a vh height would make it grow forever. */
.layout{display:grid;grid-template-columns:248px minmax(0,1fr);align-items:stretch;}
.side{background:var(--white);border-right:1px solid var(--line);padding:18px 12px 24px;}
.tabs{display:flex;flex-direction:column;gap:2px;position:sticky;top:12px;}
.grp{font-size:.74rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:14px 10px 4px;}
.grp:first-child{margin-top:0;}
.tab{display:block;width:100%;text-align:left;font:inherit;font-size:.97rem;font-weight:600;line-height:1.3;color:var(--ink);background:none;border:0;border-radius:8px;padding:7px 10px;cursor:pointer;min-height:40px;}
.tab small{display:block;font-size:.72rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);margin-bottom:1px;}
.tab:hover{background:#eef2f7;}
.tab[aria-selected="true"]{background:var(--navy);color:#fff;}
.tab[aria-selected="true"] small{color:#e8d080;}
.tab.lab{background:var(--gold-lt);box-shadow:inset 3px 0 0 var(--gold);}
.tab.lab:hover{background:#f8ecc8;}
.tab.lab[aria-selected="true"]{background:var(--gold-dk);color:#fff;box-shadow:none;}
.tab.lab[aria-selected="true"] small{color:#fff3cf;}
.layout>main{padding:22px clamp(16px,3vw,44px) 56px;}
.layout>main>.panel{max-width:1100px;}
.panel[hidden]{display:none;}
.panel:focus{outline:none;}
main{min-width:0;}
h2{font-family:'Fraunces',Georgia,serif;font-size:1.5rem;color:var(--navy);margin:0 0 10px;line-height:1.25;}
h3{font-size:1.05rem;color:var(--navy);margin:22px 0 6px;}
p{margin:0 0 10px;}
ul,ol{margin:0 0 10px;padding-left:22px;} li{margin:3px 0;}
.facts{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px;padding:0;list-style:none;}
.facts li{margin:0;background:var(--white);border:1.5px solid var(--line-2);border-radius:999px;padding:5px 14px;font-size:.95rem;}
.facts li b{color:var(--navy);}
.facts li.due{border-color:var(--red);background:var(--red-lt);}
.box{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:0 0 14px;}
.box h3:first-child{margin-top:0;}
.box h3:first-child+h3{margin-top:6px;}
.note{border-left:4px solid var(--gold);background:var(--white);border-radius:0 8px 8px 0;padding:10px 14px;margin:0 0 14px;}
.qlist{list-style:none;padding:0;margin:0;counter-reset:q;}
.qlist li{counter-increment:q;position:relative;padding:9px 0 9px 42px;border-bottom:1px solid var(--line);margin:0;}
.qlist li:last-child{border-bottom:none;}
.qlist li::before{content:counter(q);position:absolute;left:0;top:10px;width:28px;height:28px;border-radius:50%;background:var(--navy);color:#fff;font-weight:700;font-size:.9rem;display:flex;align-items:center;justify-content:center;}
.qlist .q{display:block;font-size:1.1rem;font-weight:600;color:var(--navy);}
.qlist .q i{font-style:normal;}
.qlist .g{display:block;color:var(--muted);font-size:.95rem;}
.qlist .t{display:block;font-family:'Fraunces',Georgia,serif;font-weight:700;font-size:1.15rem;color:var(--navy);margin:0 0 4px;}
.qsub{list-style:none;padding:0;margin:0;}
.qsub li{counter-increment:none;padding:5px 0 5px 0;border:none;}
.qsub li::before{content:none;}
.qlist .qsub .q{font-size:1.05rem;}
.steps{counter-reset:s;list-style:none;padding:0;}
.steps li{counter-increment:s;padding-left:34px;position:relative;margin:6px 0;}
.steps li::before{content:counter(s);position:absolute;left:0;top:1px;width:24px;height:24px;border-radius:50%;border:2px solid var(--navy);color:var(--navy);font-weight:700;font-size:.85rem;display:flex;align-items:center;justify-content:center;}
.slide-ex{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:8px 0 0;}
.slide-ex div{border-radius:8px;padding:10px 12px;font-size:.95rem;}
.slide-ex .ok{background:var(--green-lt);border:1.5px solid var(--green);}
.slide-ex .no{background:var(--red-lt);border:1.5px solid var(--red);}
.slide-ex b{display:block;font-size:.85rem;text-transform:uppercase;letter-spacing:.05em;}
.slide-ex .ok b{color:var(--green);} .slide-ex .no b{color:#9b0c23;}
.slide-ex .t{font-family:'Fraunces',Georgia,serif;font-weight:700;font-size:1.1rem;color:var(--navy);display:block;}
.check{list-style:none;padding:0;} .check li{display:flex;gap:10px;align-items:flex-start;}
.check input{width:24px;height:24px;margin-top:4px;accent-color:var(--navy);flex-shrink:0;}
.subtabs{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 14px;}
.subtab{font:inherit;font-size:.95rem;font-weight:600;padding:6px 14px;min-height:44px;border-radius:999px;border:1.5px solid var(--line-2);background:var(--white);color:var(--navy);cursor:pointer;}
.subtab[aria-selected="true"]{background:var(--navy);border-color:var(--navy);color:#fff;}
table{border-collapse:collapse;width:100%;margin:0 0 8px;background:var(--white);font-size:.98rem;}
th,td{text-align:left;padding:6px 10px;border-bottom:1px solid var(--line);vertical-align:top;}
th{font-size:.85rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);background:var(--cream);}
td:first-child{font-weight:600;color:var(--navy);width:48%;}
.say{border:1px solid var(--line-2);background:var(--white);color:var(--navy);border-radius:6px;min-width:36px;min-height:36px;cursor:pointer;margin-left:6px;font-size:.95rem;}
.imgs{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin:0 0 6px;}
.imgs figure{margin:0;background:var(--white);border:1px solid var(--line);border-radius:8px;overflow:hidden;}
.imgs img{width:100%;height:110px;object-fit:cover;display:block;}
.imgs figcaption{padding:6px 9px;font-size:.92rem;} .imgs figcaption b{display:block;color:var(--navy);}
.credit{font-size:.85rem;color:var(--muted);}
.grid2{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;}
.camp{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:12px 14px;font-size:.95rem;}
.camp h3{margin:0 0 4px;}
.camp a{display:inline-block;padding:3px 0;min-height:24px;}
.labrow{display:grid;grid-template-columns:52px 1fr;gap:12px;background:var(--white);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:0 0 10px;}
.labrow .n{font-family:'Fraunces',Georgia,serif;font-weight:900;font-size:2rem;color:var(--blue);line-height:1;}
.labrow h3{margin:0 0 2px;}
.labstate{margin:0;font-size:.875rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;}
.labstate:empty{display:none;}
.labrow.past{background:var(--cream);border-style:dashed;}
.labrow.past .n,.labrow.past h3,.labrow.past p,.labrow.past .meta b{color:var(--muted);}
.labrow.current{border:2px solid var(--gold);box-shadow:0 6px 20px rgba(122,93,20,.18);transform:scale(1.015);background:var(--gold-lt);}
.labrow.current .labstate{display:inline-block;background:var(--gold-dk);color:#fff;border-radius:999px;padding:1px 10px;margin-bottom:4px;}
.box.honesty{border-left:5px solid var(--red);}
.labrow .meta{font-size:.92rem;color:var(--muted);margin:0 0 4px;}
.labrow .meta b{color:var(--red);}
.btn{display:inline-block;background:var(--navy);color:#fff;text-decoration:none;font-weight:700;padding:10px 18px;border-radius:8px;min-height:44px;}
.btn:hover{background:var(--navy-2);color:#fff;}
.btn.gold{background:var(--gold-dk);} .btn.gold:hover{background:#5f480f;}
.labpanel{background:var(--gold-lt);border:1.5px solid var(--gold);border-radius:12px;padding:18px 20px;}
.cards{display:flex;flex-wrap:wrap;gap:10px;list-style:none;padding:0;margin:0 0 6px;}
.cards li{margin:0;}
.wcard{font:inherit;min-width:150px;min-height:64px;padding:8px 14px;border-radius:10px;border:1.5px solid var(--navy);background:var(--white);cursor:pointer;text-align:center;}
.wcard .w{display:block;font-weight:700;font-size:1.1rem;color:var(--navy);}
.wcard .m{display:block;font-size:.95rem;color:var(--muted);}
.wcard .m[hidden]{display:none;}
.wcard[aria-expanded="true"]{background:var(--sky);border-color:var(--sky);}
.wcard[aria-expanded="true"] .m{color:var(--ink);}
.linkbtn{font:inherit;font-weight:700;color:var(--navy);background:var(--white);border:1.5px solid var(--navy);border-radius:999px;padding:6px 16px;min-height:44px;cursor:pointer;}
.hero{margin:0 0 14px;}
.hero img{display:block;width:100%;height:180px;object-fit:cover;border-radius:12px;}
.hero figcaption{font-size:.85rem;color:var(--muted);margin-top:4px;}
.hero figcaption a{color:var(--muted);display:inline-block;min-height:24px;padding:2px 0;}
.video{position:relative;width:100%;max-width:720px;aspect-ratio:16/9;background:#0b1a2e;border-radius:12px;overflow:hidden;margin:0 0 14px;}
.video iframe{position:absolute;inset:0;width:100%;height:100%;border:0;}
details.box summary{cursor:pointer;min-height:32px;color:var(--navy);}
details.box[open] summary{margin-bottom:6px;}
.btnrow{display:flex;flex-wrap:wrap;gap:10px;margin:6px 0 16px;}
.btn.ghost{background:var(--white);color:var(--navy);border:1.5px solid var(--navy);}
.btn.ghost:hover{background:var(--cream);color:var(--navy);}
footer.foot{margin:0 0 0 248px;padding:0 clamp(16px,3vw,44px) 30px;font-size:.88rem;color:var(--muted);}
.single{max-width:760px;margin:0 auto;padding:22px 24px 60px;}
@media (max-width:820px){
 .layout{grid-template-columns:minmax(0,1fr);}
 .side{border-right:0;border-bottom:1px solid var(--line);padding:10px 12px;} .tabs{flex-direction:row;flex-wrap:wrap;gap:4px;position:static;}
 .tab{width:auto;flex:1 1 40%;} .grp{display:none;} .layout>main{padding:16px 16px 48px;} footer.foot{margin:0;padding:0 16px 24px;}
 header.top{padding:16px;} .top .num{font-size:2.3rem;} .slide-ex{grid-template-columns:1fr;}
 .single{padding:14px 16px 50px;}
}
@page{size:letter;margin:.65in;}
@media print{
 .side,.skip,.no-print,.accent-tab,.say{display:none!important;}
 body{background:#fff;} header.top{background:#fff;color:#000;border-bottom:2px solid #000;}
 .top h1 .c,.top .num,.top p{color:#000;}
 .layout{grid-template-columns:1fr;} .layout>main{padding:0;} footer.foot{margin:0;} .panel[hidden]{display:block!important;}
 .box,.labrow,.camp{break-inside:avoid;}
}
"""

TABS_JS = """
(function(){
  function setup(listSel, tabSel){
    document.querySelectorAll(listSel).forEach(function(list){
      var tabs=[].slice.call(list.querySelectorAll(tabSel));
      function show(t, focus){
        tabs.forEach(function(x){var on=x===t;x.setAttribute('aria-selected',on);x.tabIndex=on?0:-1;
          document.getElementById(x.getAttribute('aria-controls')).hidden=!on;});
        if(focus) t.focus();
      }
      tabs.forEach(function(t,i){
        t.addEventListener('click',function(){show(t);
          if(list.classList.contains('tabs')){try{history.replaceState(null,'','#'+t.id.replace('tab-',''));}catch(e){}}});
        t.addEventListener('keydown',function(ev){
          var k=ev.key,j=null;
          if(k==='ArrowDown'||k==='ArrowRight') j=(i+1)%tabs.length;
          else if(k==='ArrowUp'||k==='ArrowLeft') j=(i-1+tabs.length)%tabs.length;
          else if(k==='Home') j=0; else if(k==='End') j=tabs.length-1;
          if(j!==null){ev.preventDefault();show(tabs[j],true);}
        });
      });
      if(list.classList.contains('tabs')){
        var h=(location.hash||'').slice(1), t=h&&document.getElementById('tab-'+h);
        if(t&&tabs.indexOf(t)>=0) show(t);
      }
    });
  }
  setup('.tabs','.tab'); setup('.subtabs','.subtab');
  document.querySelectorAll('[data-goto]').forEach(function(a){a.addEventListener('click',function(ev){
    var t=document.getElementById('tab-'+a.getAttribute('data-goto')); if(t){ev.preventDefault();t.click();t.focus();window.scrollTo(0,0);}});});
})();
(function(){
  // In a D2L iframe (same site, with a height="" attribute from the setup snippets), grow the frame to fit
  // this page so there's no inner scrollbar. Pages on GitHub can't do this (different site), and preview
  // frames in the proposal and guides have no height attribute, so they keep their own size.
  function fit(){ try{ var f=window.frameElement; if(f&&f.hasAttribute('height')) f.style.height=(document.documentElement.scrollHeight+6)+'px'; }catch(e){} }
  window.addEventListener('load',fit); document.addEventListener('click',function(){ setTimeout(fit,60); });
  if(window.ResizeObserver) new ResizeObserver(fit).observe(document.body);
})();
function say(t){try{var u=new SpeechSynthesisUtterance(t);u.lang='es-MX';u.rate=.9;speechSynthesis.cancel();speechSynthesis.speak(u);}catch(e){}}
"""

FLAG_JS = r"""
(function(){
  // The banner flag cycles through Spanish-speaking countries (as on the original lab pages).
  // Paused while you point at it; no cycling for people who ask for reduced motion.
  var flags=[["España",["#c8102e","#b8952a","#c8102e"],"#9cc9ee"],["México",["#006847","#ffffff","#ce1126"],"#9cc9ee"],["Argentina",["#74acdf","#ffffff","#74acdf"],"#9cc9ee"],
   ["Colombia",["#fcd116","#003087","#ce1126"],"#fcd116"],["Chile",["#d52b1e","#ffffff","#002d62"],"#9cc9ee"],["Perú",["#d91023","#ffffff","#d91023"],"#9cc9ee"],
   ["Venezuela",["#cf142b","#00247d","#cf9a00"],"#e0b030"],["Cuba",["#002a8f","#ffffff","#002a8f"],"#9cc9ee"],["Ecuador",["#ffd100","#003893","#ef3340"],"#ffd100"],
   ["Bolivia",["#d52b1e","#f4e400","#007a3d"],"#f4e400"],["Guatemala",["#4997d0","#ffffff","#4997d0"],"#9cc9ee"],["Costa Rica",["#002b7f","#cf142b","#ffffff"],"#9cc9ee"],
   ["Uruguay",["#ffffff","#5b9bd5","#ffffff"],"#9cc9ee"],["Honduras",["#009bde","#ffffff","#009bde"],"#9cc9ee"],["Nicaragua",["#003f87","#ffffff","#003f87"],"#9cc9ee"],
   ["El Salvador",["#0f47af","#ffffff","#0f47af"],"#9cc9ee"],["Rep. Dominicana",["#002d62","#cf142b","#002d62"],"#9cc9ee"],["Puerto Rico",["#002d62","#ffffff","#cf142b"],"#9cc9ee"],
   ["Panamá",["#da121a","#ffffff","#005eb8"],"#9cc9ee"],["Paraguay",["#d52b1e","#ffffff","#0032a0"],"#9cc9ee"]];
  var w=document.querySelector('.top .flag'); if(!w) return;
  var bars=w.querySelectorAll('i'), tip=w.querySelector('.flagtip'), acc=document.querySelector('.top h1 .c'), i=0, paused=false;
  for(var k=flags.length-1;k>1;k--){var j=1+Math.floor(Math.random()*k),t=flags[k];flags[k]=flags[j];flags[j]=t;}  // España first, then a random order
  function show(f){ for(var b=0;b<3;b++) bars[b].style.background=f[1][b]; w.setAttribute('aria-label','Flag of '+f[0]); if(tip) tip.textContent=f[0]; if(acc) acc.style.color=f[2]; }
  show(flags[0]);
  if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  w.addEventListener('mouseenter',function(){paused=true;}); w.addEventListener('mouseleave',function(){paused=false;});
  setInterval(function(){ if(paused) return; i=(i+1)%flags.length; show(flags[i]); },6000);
})();
"""

ACCENT = """
<div class="accent-tab no-print" id="accentTab">
  <button type="button" class="accent-tab-toggle" id="accentToggle" aria-expanded="false" aria-controls="accentPanel">&#9000; Accents</button>
  <div class="accent-panel" id="accentPanel" hidden>
    <p class="accent-instructions">Click a letter to copy it, then press <strong>Ctrl+V</strong> (<strong>&#8984;+V</strong> on Mac) to paste it into your answer. On a Mac, you can also press and hold a letter key.</p>
    <div class="accent-grid">""" + "".join(f'<button type="button" class="accent-btn" data-char="{c}">{c}</button>' for c in "áéíóúñ¿¡") + """</div>
    <p class="accent-status" id="accentStatus" aria-live="polite"></p>
  </div>
</div>
<style>
.accent-tab{position:fixed;right:0;top:50%;transform:translateY(-50%);z-index:500;}
.accent-tab-toggle{writing-mode:vertical-rl;background:var(--navy);color:#fff;border:none;border-radius:10px 0 0 10px;padding:14px 8px;font:600 14px 'DM Sans',Arial,sans-serif;cursor:pointer;min-height:44px;}
.accent-panel{position:fixed;right:58px;top:50%;transform:translateY(-50%);z-index:501;background:#fff;border:1.5px solid var(--line-2);border-radius:10px;padding:14px;width:230px;box-shadow:0 8px 24px rgba(0,0,0,.22);}
.accent-panel[hidden]{display:none;}
.accent-instructions{font-size:14px;color:var(--muted);margin:0 0 10px;line-height:1.4;}
.accent-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;}
.accent-btn{font:700 20px 'Fraunces',Georgia,serif;color:var(--navy);background:var(--cream);border:1.5px solid var(--line-2);border-radius:8px;padding:8px 0;cursor:pointer;min-height:44px;}
.accent-btn:hover{border-color:var(--navy);}
.accent-status{font-size:14px;color:var(--navy);font-weight:600;margin:8px 0 0;min-height:36px;}
</style>
<script>
(function(){
  var toggle=document.getElementById('accentToggle'),panel=document.getElementById('accentPanel'),status=document.getElementById('accentStatus');
  toggle.addEventListener('click',function(){var h=panel.hasAttribute('hidden');
    if(h){panel.removeAttribute('hidden');toggle.setAttribute('aria-expanded','true');}else{panel.setAttribute('hidden','');toggle.setAttribute('aria-expanded','false');}});
  function fallback(t,cb){var ta=document.createElement('textarea');ta.value=t;ta.style.position='fixed';ta.style.opacity='0';document.body.appendChild(ta);ta.select();try{document.execCommand('copy');}catch(e){}document.body.removeChild(ta);cb();}
  document.querySelectorAll('.accent-btn').forEach(function(b){b.addEventListener('click',function(){var ch=b.getAttribute('data-char');
    var done=function(){status.textContent='Copied "'+ch+'". Press Ctrl+V (⌘+V on Mac) to paste.';};
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(ch).then(done).catch(function(){fallback(ch,done);});}else{fallback(ch,done);}});});
})();
</script>
"""

FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@700;900&family=DM+Sans:wght@400;600;700&display=swap" rel="stylesheet">'

def page(title, head_title, head_sub, body, num="", accent=False, kb=False):
    doc = _page(title, head_title, head_sub, body, num, accent, kb)
    return loc(doc)

def loc(doc):
    return fr_locale.loc(doc, C.get("locale_pairs")) if C.get("locale") == "fr" else doc

def _page(title, head_title, head_sub, body, num="", accent=False, kb=False):
    num_html = f'<span class="num" aria-hidden="true">{num}</span>' if num else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
{FONTS}
<style>{CSS}{K.CSS}{AUDIO_CSS if AUDIO else ""}{WK_CSS if WKG else ""}{C.get("theme_css", "")}</style>
</head>
<body>
<a class="skip" href="#main">Skip to main content</a>
<header class="top">
  <span class="flag" role="img" aria-label="Flag of España"><i></i><i></i><i></i><span class="flagtip" aria-hidden="true">España</span></span>
  <div><h1>{head_title}</h1><p>{head_sub}</p></div>
  {num_html}
</header>
{body}
{ACCENT if accent else ""}
<script>{TABS_JS}{FLAG_JS}</script>
{"<script>" + K.js() + "</script>" if kb else ""}
</body>
</html>
"""


def console(tabs, label, groups=None):
    """tabs: list of (id, kicker, label, html, cls). groups: optional {tab id: rail heading}. Returns the left-console layout."""
    last = [None]
    def grp(t):
        g = (groups or {}).get(t[0])
        if not g or g == last[0]: return ""
        last[0] = g; return f'<div class="grp" aria-hidden="true">{e(g)}</div>'
    nav = "\n".join(grp(t) +
        f'<button type="button" role="tab" class="tab{(" " + t[4]) if t[4] else ""}" id="tab-{t[0]}" aria-controls="p-{t[0]}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}"><small>{t[1]}</small>{t[2]}</button>'
        for i, t in enumerate(tabs))
    panels = "\n".join(
        f'<section class="panel" role="tabpanel" id="p-{t[0]}" aria-labelledby="tab-{t[0]}" tabindex="0"{"" if i == 0 else " hidden"}>\n{t[3]}\n</section>'
        for i, t in enumerate(tabs))
    return f"""<div class="layout">
<nav class="side" aria-label="{e(label)}"><div class="tabs" role="tablist" aria-orientation="vertical" aria-label="{e(label)}">
{nav}
</div></nav>
<main id="main">
{panels}
</main>
</div>"""

def ul(items, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f"<ul{c}>" + "".join(f"<li>{es(x)}</li>" for x in items) + "</ul>"

def steps(items):
    return '<ol class="steps">' + "".join(f"<li>{x}</li>" for x in items) + "</ol>"

def spoken(a):
    """The vocabulary entry as words to read aloud: Fatigué(e) -> Fatigué, Ne… jamais -> Ne jamais."""
    s = re.sub(r"\((e|se)\)", "", a.split(" + ")[0]).replace(", etc.", "").replace("…", " ").replace(" / ", ", ").replace("(", "").replace(")", "")
    return re.sub(r"\s+", " ", s).strip()

def forvo_link(a):
    """Forvo search for the entry's first form, without its article. Search, not a word page, as in the feedback generators."""
    s = spoken(re.sub(r"\([^)]*\)", "", re.sub(r"\((e|se)\)", "", a))).split(",")[0].lower().rstrip(" ?!.…¡¿")
    s = re.sub(r"^(un |une |des |le |la |les |l'|de la )", "", s)
    return f'<a class="fv" lang="en" href="https://forvo.com/search/{quote(s)}/{C.get("locale", "es")}/" target="_blank" rel="noopener" aria-label="Hear {e(a)} on Forvo (opens in a new tab)">Forvo</a>'

def vtable(rows, speak=False, caption="", forvo=False):
    cap = f'<caption class="sr">{es(caption)}</caption>' if caption else ""
    trs = "".join(
        f'<tr><td lang="es">{e(a)}' + ('<span class="au">' + forvo_link(a) if forvo else "") + (f'<button type="button" class="say" onclick="say(this.dataset.t)" data-t="{e(spoken(a) if forvo else a)}" aria-label="Listen: {e(a)}">▶</button>' if speak else "") + ("</span>" if forvo else "") + f'</td><td>{es(b)}</td></tr>'
        for a, b in rows)
    return f'<table>{cap}<thead><tr><th scope="col">Spanish</th><th scope="col">English</th></tr></thead><tbody>{trs}</tbody></table>'

def head(sub_title, n=""):
    return f'SPAN <span class="c">{NUM}</span>' + (f" · Lab {n}" if n else " · Language Lab")

# ---------------- Bongo page ----------------

def video_rules_html(L=None):
    return ul((L or {}).get("video_rules", C["video_rules"])) + f'<p>{es(POLICY["incomplete_rule"])} The rubric is in the Bongo assignment.</p>'

def length(L): return L.get("length", C.get("default_length", ""))

def record_steps(L):
    mode, p = L["mode"], L.get("prompts")
    if mode == "Upload":
        s = ["Record your video on your phone in a quiet, well-lit spot.",
             "Move the file to your computer (AirDrop, Google Drive, or email it to yourself).",
             "Open the Bongo assignment and choose <b>Upload</b> (not Record). Select your file.",
             "Watch it back: check that your face and voice come through. Then <b>Submit</b>."]
    elif p:
        s = [f"Open the Bongo assignment. It has <b>{p} separate prompts</b>. Allow the camera and microphone.",
             "Watch the first prompt video, then record your answer in <b>Camera</b> mode.",
             "Watch your answer back: check that your face and voice come through.",
             "Submit it, then open the next prompt. To redo one before the due date, open the <b>⋮</b> menu next to it and choose <b>Retake</b>."]
    else:
        s = [f"Open the Bongo assignment and choose <b>{mode}</b>. Allow the camera and microphone."]
        if mode == "Camera + Screen":
            s.append("Open your slides full screen, then share that screen when Bongo asks.")
        s += ["Record. Then watch it: check that your face and voice come through.",
              "Submit. To redo it before the due date, open the <b>⋮</b> menu and choose <b>Reset Submission</b>."]
    if L.get("peer"):
        s.append("After you submit, classmates' videos appear. Leave a <b>video</b> comment (not text) on one of them.")
    return steps(s)

def hero(L):
    img, credit, url = L["hero"]
    cred = f'<a href="{e(url)}" target="_blank" rel="noopener">{e(credit)}</a>' if url else e(credit)
    return f'<figure class="hero"><img src="{C["github_images"]}{img}" alt=""><figcaption>{cred}</figcaption></figure>'

def talk_tab(L, v):
    """TalkAbroad labs: short by design. The workshop has its own tab; reflection lives in the generator."""
    facts = [due_chip(L, v), f'<li>{e(L["ch_label"])}</li>', f'<li><b>Mode</b> {e(L["mode"])}</li>', f'<li><b>Length</b> {e(length(L))}</li>']
    h = [hero(L), f'<h2>Lab {L["n"]}: <span lang="es">{e(L["title"])}</span></h2>', '<ul class="facts">' + "".join(facts) + "</ul>"]
    book = f'<p><a class="btn gold" href="{e(C["wconline"])}" target="_blank" rel="noopener">Sign up on WCONLINE</a></p>'
    if L.get("review"):
        h.append(f'<p>{e(L["context"])} You attend {e(v.get("workshop_where", "in person"))}.</p><div class="note"><b>Graded on attendance and participation only.</b> No TalkAbroad and no submission.</div>')
        h.append('<div class="box"><h3>Bring</h3>' + ul(L["bring"]) + book + "</div>")
        if WKG and L["id"] in WKG["labs"]: h.append('<h3>What you\'ll do</h3><ul class="wk-meta"><li>About 30 min</li><li>Groups of 4–6</li><li>French only</li></ul>' + wk_stages(L))
        return "\n".join(h)
    wk = not v.get("no_workshop")
    how = ([(f'<b>Workshop:</b> sign up and attend {e(v.get("workshop_where", "in person"))}' + (f" by {L['workshop_date'].strftime('%b')} {L['workshop_date'].day}" if L.get("workshop_date") else "") + '. See the <a href="#workshop" data-goto="workshop">Workshop</a> tab.')] if wk else []) + [
        "<b>Talk:</b> book at least 36 hours ahead, then have your 15-minute conversation in French. Ask your partner at least 2 questions.",
        (f"<b>Submit:</b> upload your preparation notes and your conversation video to the <b>Lab {L['n']} TalkAbroad</b> dropbox." if C.get("talk_dropbox") else "<b>Submit:</b> upload your preparation notes and the mp3 to the lab's dropbox.")]
    h.append('<div class="box"><h3>What to do</h3>' + steps(how) + "</div>")
    h.append('<div class="box"><h3>Talk about</h3>' + "".join(f"<h3>{e(t)}</h3>" + ul(x) for t, x in L["prompt_groups"]) + f'<h3>Use</h3><p>{e("; ".join(L["grammar"]))}</p>' + "</div>")
    h.append(f'<div class="box"><h3>Your preparation notes</h3><p>Key words, a few ideas and 2–3 questions for your partner. Cover every part of the topic and add your own ideas: preparation is graded. Notes, not a script.</p>'
             + (f'<p><a href="../reflection.html?lab={L["n"]}" target="_blank" rel="noopener">Optional: download the PDF form</a> for your notes and reflection, fill it in, and upload it with your video.</p></div>' if C.get("talk_dropbox") else
             f'<p><a href="../reflection.html?lab={L["n"]}" target="_blank" rel="noopener">Optional: use the reflection generator</a> to write them and save a PDF.</p></div>'))
    return "\n".join(h)

# Workshop stages (FREN 1002, 2026-11-16): the students' Workshop tab shows the same five stages the lab assistants run
# (proposal.la_workshops in the course source, from fren1002/labs-2026/workshop_guides.py). Other courses: unchanged.
WKG = (C.get("proposal") or {}).get("la_workshops")
WK_CSS = """.wk-meta{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px;padding:0;list-style:none;} .wk-meta li{margin:0;background:var(--cream);border:1px solid var(--line);border-radius:999px;padding:3px 12px;font-size:.9rem;font-weight:600;}
.wk-st{list-style:none;padding:0;margin:0 0 12px;display:grid;gap:10px;}
.wk-st>li{display:grid;grid-template-columns:34px minmax(0,1fr);gap:12px;background:var(--white);border:1.5px solid var(--line);border-radius:10px;padding:12px 14px;margin:0;}
.wk-n{display:grid;place-items:center;width:32px;height:32px;border-radius:50%;background:var(--navy);color:#fff;font-weight:700;}
.wk-st h3{margin:2px 0 4px;font-size:1.05rem;} .wk-st h3 small{font-weight:400;color:var(--muted);font-size:.88rem;} .wk-st p{margin:0 0 6px;}
.wk-say{margin:6px 0 0;padding:6px 10px;background:var(--cream);border-left:4px solid var(--blue);border-radius:6px;font-size:.95rem;} .wk-say span{display:block;}
.wk-board{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));border:2px solid var(--navy);border-radius:8px;overflow:hidden;margin:6px 0 0;}
.wk-board div{padding:6px 10px;border-right:1px solid var(--line);font-size:.93rem;} .wk-board div:last-child{border-right:0;} .wk-board b{display:block;color:var(--navy);}
@media(max-width:620px){.wk-board{grid-template-columns:1fr;} .wk-board div{border-right:0;border-bottom:1px solid var(--line);}}"""

def wk_stages(L):
    g = WKG["labs"][L["id"]]
    def one(i, x):
        extra = ('<div class="wk-board">' + "".join(f'<div><b lang="fr">{e(h)}</b><span lang="fr">{e(w)}</span></div>' for h, w in x["board"]) + "</div>") if x.get("board") else (
                 '<p class="wk-say" lang="fr">' + "".join(f"<span>{e(t)}</span>" for t in x["say"]) + "</p>" if x["say"] else "")
        return (f'<li><span class="wk-n" aria-hidden="true">{i}</span><div><h3><span lang="fr">{e(x["fr"])}</span> <small>{e(x["en"])} · {x["min"]} min · {e(x["fmt"]).lower()}</small></h3>'
                f'<p>{x["you"]}</p>{extra}</div></li>')
    return '<ol class="wk-st">' + "".join(one(i, x) for i, x in enumerate(g["stages"], 1)) + "</ol>"

def workshop_tab(L, v):
    w = L["workshop"]
    if WKG and L["id"] in WKG["labs"]:
        nb = f'<a href="../reflection.html?lab={L["n"]}" target="_blank" rel="noopener">notes form</a>'
        return (f'<h2>Workshop</h2><p>Practice with your lab assistant and 3–5 classmates {e(v.get("workshop_where", "in person"))} before your conversation. It\'s informal and all in French. Graded on attendance and participation. Nothing to submit.</p>'
                f'<p><a class="btn gold" href="{e(C["wconline"])}" target="_blank" rel="noopener">Sign up on WCONLINE</a></p>'
                + '<div class="note"><b>Can\'t make any time at your campus?</b> Book any online workshop that week on WCONLINE. Lab assistants from Dahlonega and Gainesville run them, and any of them counts.</div>'
                + '<ul class="wk-meta"><li>About 30 min</li><li>Groups of 4–6</li><li>French only</li></ul>' + wk_stages(L)
                + f'<div class="note"><b>You leave with</b> 5 key words and 2 questions for your TalkAbroad partner: your preparation notes. Want them on paper? Use the optional {nb}.</div>')
    return (f'<h2>Workshop</h2><p>Practice with your Lab Assistant {e(v.get("workshop_where", "in person"))} before your conversation. Graded on attendance and participation. Nothing to submit.</p>'
            f'<p><a class="btn gold" href="{e(C["wconline"])}" target="_blank" rel="noopener">Sign up on WCONLINE</a></p>'
            + ('<div class="note"><b>Can\'t make any time at your campus?</b> Book any online workshop that week on WCONLINE. Lab assistants from Dahlonega and Gainesville run them, and any of them counts.</div>' if C.get("talk_dropbox") else '')
            + '<div class="box"><h3>Warm-up</h3>' + ul(w["warm"]) + '</div><div class="box"><h3>Partner drill</h3>' + ul(w["drill"]) + '</div><div class="box"><h3>Get ready</h3>' + ul(w["prep"]) + "</div>")

def talk_lab0(v):
    l0 = POLICY["lab0"]
    task = f"""<h2>Lab 0: {e(l0["title"])}</h2>
<ul class="facts"><li class="due"><b>Due</b> in the first week</li><li><b>Length</b> {e(l0["length"])}</li><li><b>Grade</b> 0%</li></ul>
<p>{es(l0["context"])}</p><p>Do this first. There is nothing to turn in: the Guidelines Quiz asks you to confirm it's done.</p>
<div class="box"><h3>Set up your account (one time)</h3>{steps(l0["steps"])}</div>
<div class="note"><b>Your labs unlock</b> when you pass the Guidelines Quiz.</div>"""
    tabs = [("assignment", "Lab 0", "Assignment", task, ""), ("troubleshooting", "Help", "Troubleshooting", "<h2>Troubleshooting</h2>\n" + trouble_blocks(v, {"n": 0}), "")]
    return page(f"{C['course']} · Lab 0 · {l0['title']}", head("", "0"), f'{e(l0["title"])} · Lab page · {e(v["label"])} · {e(CAMPUS["name"])}', console(tabs, "Lab 0 sections"), num="0")

def assignment_tab(L, v):
    if L.get("talk") or L.get("review"): return talk_tab(L, v)
    facts = [due_chip(L, v), f'<li>{e(L["ch_label"])}</li>', f'<li><b>Mode</b> {L["mode"]}{(" · " + str(L["prompts"]) + " prompts") if L.get("prompts") else ""}</li>']
    if length(L): facts.append(f'<li><b>Length</b> {e(length(L))}</li>')
    if L.get("peer"): facts.append('<li><b>+</b> video comment</li>')
    h = [hero(L), f'<h2>Lab {L["n"]}: <span lang="es">{e(L["title"])}</span></h2>', '<ul class="facts">' + "".join(facts) + "</ul>", f'<p>{es(L["context"])}</p>']
    if "question_groups" in L:
        # Individual assignment with the questions on the page (2026-10-07, SPAN 1002 Labs
        # De compras, Días festivos, La salud; they were Bongo Question & Answer prompts).
        h.append('<div class="box"><h3>Answer these questions, in order</h3><ol class="qlist">' + "".join(
            f'<li><span class="t" lang="es">{es(title)}</span><ul class="qsub">' + "".join(
                f'<li><span class="q" lang="es">{es(q)}</span><span class="g">{es(g)}</span></li>' for q, g in qs) + "</ul></li>"
            for title, qs in L["question_groups"]) + "</ol></div>")
    elif "questions" in L:
        h.append('<div class="box"><h3>Answer these questions</h3><ol class="qlist">' + "".join(
            f'<li><span class="q" lang="es">{es(q)}</span><span class="g">{es(g)}</span></li>' for q, g in L["questions"]) + "</ol></div>")
    else:
        h.append('<div class="box"><h3 style="margin-top:0">Your task</h3>' + "".join(f"<h3>{es(t)}</h3>" + ul(items) for t, items in L["parts"]) + "</div>")
    if L.get("tips"):
        h.append('<div class="note"><b>Remember:</b> ' + " ".join(es(t) for t in L["tips"]) + "</div>")
    if "slides" in L:
        s = L["slides"]
        h.append('<div class="box"><h3>Your slides</h3>' + ul(s["rules"] + ["Your slides must be visible for the whole video. If they aren't, Task Completion drops to 2 of 5 points."]) +
                 f'<div class="slide-ex"><div class="ok"><b>Good slide</b><span class="t" lang="es">{e(s["good"][0])}</span><span lang="es">{e(s["good"][1])}</span></div>'
                 f'<div class="no"><b>Not this</b><span lang="es">{e(s["bad"])}</span></div></div>')
        if "photo_links" in L and C.get("photo_cards"):
            h.append(f'<h3>{e(L.get("photo_label", "Photos"))}</h3><div class="pcards">' + "".join(f'<a class="pcard" href="{e(x[1])}" target="_blank" rel="noopener"><b>{e(x[0])}</b><span>{e(x[2])}</span></a>' for x in L["photo_links"]) + "</div>")
        elif "photo_links" in L:
            h.append('<p style="margin-top:10px">Photos: ' + " · ".join(f'<a href="{e(x[1])}" target="_blank" rel="noopener">{e(x[0])}</a>' for x in L["photo_links"]) + "</p>")
        h.append("</div>")
    if "checklist" in L:
        h.append('<div class="box"><h3>Before you record, check that you used:</h3><ul class="check">' + "".join(
            f'<li><input type="checkbox" id="ck{i}"><label for="ck{i}">{es(c)}</label></li>' for i, c in enumerate(L["checklist"])) + "</ul></div>")
    if L.get("peer"):
        h.append('<div class="box"><h3>Your video comment</h3><p>' + e(L.get('peer_intro', "Watch one classmate's video, especially their dilemma.")) + ' In your video comment:</p><ol>' +
                 "".join(f"<li>{es(p)}</li>" for p in L["peer_points"]) + "</ol><p>Face visible, Spanish only.</p></div>")
    h.append('<div class="box"><h3>Every video</h3>' + video_rules_html(L) + "</div>")
    h.append('<div class="box"><h3>Record in Bongo</h3>' + record_steps(L) +
             '<p>Problems? See <a href="#troubleshooting" data-goto="troubleshooting">Troubleshooting</a>.</p></div>')
    return "\n".join(h)

def vocab_tab(L, v):
    by_topic = v.get("vocab_label") == "topic"
    subs = []
    if L.get("lab_vocab") or L.get("lab_images"):
        body = ""
        if L.get("lab_images"):
            body += '<div class="imgs">' + "".join(
                f'<figure><img src="{C["github_images"]}{f}" alt="" loading="lazy"><figcaption><b lang="es">{e(w)}</b>{e(en)}</figcaption></figure>'
                for (w, f), en in zip(L["lab_images"], L["lab_images_en"])) + f'</div><p class="credit">{e(L["lab_images_credit"])}</p>'
        for t, rows in L.get("lab_vocab", []):
            body += f"<h3>{es(t)}</h3>" + vtable(rows, speak=True, caption=t, forvo=AUDIO)   # 2026-11-09: Forvo on the lab's own words too
        subs.append(("lab", "This lab", body))
    for ch in L["vocab_chapters"]:
        body = "".join(f"<h3>{e(cat)}</h3>" + vtable(rows, caption=cat, speak=AUDIO, forvo=AUDIO) for cat, rows in V[str(ch)].items())
        label = VOC.get("titles", {}).get(str(ch), f"Chapter {ch}") if by_topic else f"Chapter {ch}"
        subs.append((f"ch{ch}", label, body))
    nav = "".join(f'<button type="button" role="tab" class="subtab" id="st-{k}" aria-controls="sp-{k}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}"><span lang="{"es" if by_topic and k != "lab" else "en"}">{e(t)}</span></button>' for i, (k, t, _) in enumerate(subs))
    panels = "".join(f'<div role="tabpanel" id="sp-{k}" aria-labelledby="st-{k}" tabindex="0"{"" if i == 0 else " hidden"}>{b}</div>' for i, (k, _, b) in enumerate(subs))
    intro = "Words for this lab, then the full vocabulary lists by topic." if by_topic else f'{e(L.get("vocab_intro", "Chapters " + L["chapters"]))}. Use these words in your video.'
    if AUDIO: intro = f'{e(L.get("vocab_intro", "Chapters " + L["chapters"]))}. Compare your pronunciation with real speakers: <b>Forvo</b> opens in a new tab. If Forvo has no recording, press <b>▶</b> to hear your device\'s voice.'
    return f'<h2>Vocabulary</h2><p>{intro}</p><div class="subtabs" role="tablist" aria-label="Vocabulary lists">{nav}</div>{panels}'

def emails_html():
    return f'<p><a href="mailto:{CAMPUS["email"]}">{CAMPUS["email"]}</a> ({e(CAMPUS["name"])} Language Lab)</p>'

def labs_with(v, test):
    ns = [str(L["n"]) for L in v.labs if test(L)]
    return ("Lab " + ns[0]) if len(ns) == 1 else ("Labs " + ", ".join(ns[:-1]) + " and " + ns[-1]) if ns else ""

def is_screen(L): return L["mode"] == "Camera + Screen"

def trouble_kind(kind, v, labs, folder):
    """One kind of recording help, as decided in the lab policy: "video" (Camera and Upload
    labs) or "screen" (Camera + Screen labs and Lab 0)."""
    dt = v.due_time or "the due time"
    h = ['<div class="box"><h3>Before you record</h3>' + ul([
             "Use Google Chrome on a laptop or desktop. iPads and phones don't work well.",
             "Allow the camera and microphone" + (", and screen sharing" if kind == "screen" else "") + ". If you blocked them, click the camera icon in Chrome's address bar.",
             "Close Zoom, Teams, FaceTime, or anything else using your camera."] +
             (["<b>Turn on Do Not Disturb</b> and close email and other tabs, so nothing private shows in your video."] if kind == "screen" else [])) + "</div>",
         '<div class="box"><h3>The recorder won\'t load</h3>' + steps([
             "Clear Chrome's cache and cookies, then reload the page.",
             "Try a Chrome Incognito window.",
             "If the D2L home page shows up inside Bongo, open it in Chrome on a computer.",
             "<b>Restart your computer</b>, then try again."]) + "</div>"]
    if kind == "screen":
        h.append('<div class="box"><h3>Sharing your screen</h3>'
                 '<p><b>Mac: Chrome can\'t share the screen, or you only see the wallpaper.</b> macOS blocks screen sharing until you allow it:</p>' + steps([
                     "Click the <b>Apple menu</b> → <b>System Settings</b> → <b>Privacy &amp; Security</b>.",
                     "Click <b>Screen &amp; System Audio Recording</b> (on older Macs: <b>Screen Recording</b>).",
                     "Turn on <b>Google Chrome</b>. If it isn't listed, click <b>+</b> and choose Chrome from Applications.",
                     "Choose <b>Quit &amp; Reopen</b>. Chrome must restart before sharing works.",
                     "Open the Bongo assignment again and share your slides' window."]) +
                 '<p>In the same Privacy &amp; Security list, check that Chrome is also on under <b>Camera</b> and <b>Microphone</b>. '
                 '<a href="https://support.apple.com/guide/mac-help/mchld6aa7d23/mac" target="_blank" rel="noopener">Apple\'s guide</a></p>' +
                 ul(["<b>Share the window with your slides</b>, not the Bongo tab. PowerPoint online and Canva can be shared as a Chrome tab.",
                     "<b>Your slideshow isn't in the list?</b> A full-screen slideshow can't be picked. In PowerPoint, use <b>View → Reading View</b>.",
                     "<b>Two monitors?</b> Share the screen that has your slides."]) + "</div>")
    h.append('<div class="box"><h3>Other things that stop a recording</h3>' + ul([
        "<b>Windows blocks the camera:</b> Settings → Privacy & security → Camera, and turn on <b>Let desktop apps access your camera</b>. Do the same under Microphone.",
        "<b>No sound:</b> AirPods and Bluetooth headphones can take over the microphone. Pick your microphone in Bongo's settings, or disconnect them.",
        "<b>Don't close the tab</b> until Bongo finishes uploading. Slow Wi-Fi makes this take longer.",
        "<b>Plug in your laptop.</b> Low-power mode and sleep can stop a recording."]) + "</div>")
    if kind == "video" and any(x["mode"] == "Upload" for x in labs):
        h.append('<div class="box"><h3>Uploading a phone video' + (f" ({labs_with(v, lambda x: x['mode'] == 'Upload')})" if folder else "") + "</h3>" + steps([
            "Move the video from your phone to your computer with AirDrop, Google Drive, or email.",
            "In Bongo, choose <b>Upload</b> (not Record) and select the file.",
            "Use MP4 or MOV. If the file is too large, trim the start or end, or record at a lower resolution."]) + "</div>")
    if kind == "video":
        h.append(f'<div class="box"><h3>Still failing? Record outside Bongo</h3><p>Record <b>one continuous take</b> with your phone or your computer\'s camera app. '
                 f'Then choose <b>Upload Video</b> in the same Bongo assignment before {dt}. Videos with cuts, joined clips or replaced audio get 0.</p></div>')
    else:
        h.append(f'<div class="box"><h3>Still failing? Record your slides in PowerPoint or Canva</h3><p>Only a <b>PowerPoint or Canva recording, exported as an MP4</b>, is accepted. '
                 f'Other screen recorders and edited videos aren\'t graded. Upload it to the same Bongo assignment before {dt}.</p>'
                 '<p><b>PowerPoint</b> (free with your UNG account):</p>' + steps([
                     'Go to <a href="https://office.com" target="_blank" rel="noopener">office.com</a>, sign in with your UNG email, and open your slides (or use the desktop app).',
                     "Open the <b>Record</b> tab and choose <b>Record from Beginning</b> with the camera on.",
                     "Talk through your slides, then click <b>Stop</b>.",
                     "<b>File → Export → Export to Video</b> (720p, MP4).",
                     "In Bongo, choose <b>Upload Video</b> and select the file."]) +
                 '<p><b>Canva:</b> build your slides at <a href="https://www.canva.com" target="_blank" rel="noopener">canva.com</a>, choose <b>Present → Present and record</b>, download the MP4, and upload it in Bongo.</p>'
                 "<p>Both record slide by slide. That's fine: upload the video as exported, with no other editing.</p></div>")
    redo = []
    if any(not x.get("prompts") for x in labs): redo.append("Open the <b>⋮</b> menu at the top right of the assignment and choose <b>Reset Submission</b>.")
    if any(x.get("prompts") for x in labs): redo.append("For separate prompts: open the <b>⋮</b> menu next to the prompt and choose <b>Retake</b>.")
    h.append('<div class="box"><h3>Redo your recording</h3><p>' + " ".join(redo) + " You can do this until the due time.</p></div>")
    if kind == "video" and any(x.get("peer") for x in labs):
        h.append('<div class="box"><h3>Video comments' + (f" ({labs_with(v, lambda x: x.get('peer'))})" if folder else "") + '</h3><ul>'
                 "<li>You see classmates' videos only after you submit your own.</li>"
                 "<li>To comment: open a classmate's video, click the comment icon, choose <b>Video Comment</b>, and allow the camera.</li>"
                 "<li>No videos yet? Classmates haven't posted. Check back before the due date.</li></ul></div>")
    return "\n".join(h)

def trouble_rules(v):
    """What the Lab does and doesn't do when recording fails (lab policy: technical problems)."""
    dt = v.due_time or "the due time"
    return ('<div class="box honesty"><h3>Your responsibility</h3>' + f"<p>{es(POLICY['responsibility'])}</p>" + ul([
        f"Only videos submitted <b>in Bongo</b> are graded, not videos sent through D2L, by email, or as a link.",
        f"The Language Lab doesn't extend a deadline for a technology problem, even one reported before {dt}.",
        POLICY["system_wide"]]) + "</div>")

def trouble_blocks(v, L=None):
    if C.get("talk_trouble"):
        return "\n".join(f'<div class="box"><h3>{e(t)}</h3>' + "<ul>" + "".join(f"<li>{x}</li>" for x in xs) + "</ul></div>" for t, xs in C["talk_trouble"]) + \
               f'<div class="box"><h3>Still stuck?</h3><p>See the <a href="{C["bongo_help"]}" target="_blank" rel="noopener">TalkAbroad student manual</a>, then email your campus Language Lab well before the due time.</p></div>'
    """Recording problems, shared by the folder description and every Bongo page (students
    hit them in Bongo, so the Bongo copy is deliberate). L=None gives the folder version, with
    one subtab per kind; a Bongo page gets only its own kind."""
    still = (f'<div class="box"><h3>Still stuck?</h3><p>Try the <a href="{C["bongo_help"]}" target="_blank" rel="noopener">Bongo Help Center</a>. '
             'Then use the backup for your kind of lab, or come to your campus Language Lab <b>well before</b> the due time. Contacting the Lab doesn\'t extend the deadline.</p>')
    if L is not None:
        return "\n".join([trouble_kind("screen" if is_screen(L) else "video", v, [L], False), trouble_rules(v), still + emails_html() + "</div>"])
    video = [x for x in v.labs if not is_screen(x)]
    screen = [x for x in v.labs if is_screen(x)]
    kinds = [("video", "Video labs", labs_with(v, lambda x: not is_screen(x)), video),
             ("screen", "Slide labs: camera + screen", "Lab 0" + (", " + labs_with(v, is_screen) if screen else ""), screen)]
    nav = "".join(f'<button type="button" role="tab" class="subtab" id="tk-{k}" aria-controls="tp-{k}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">{e(t)}</button>'
                  for i, (k, t, _, _) in enumerate(kinds))
    panels = "".join(f'<div role="tabpanel" id="tp-{k}" aria-labelledby="tk-{k}" tabindex="0"{"" if i == 0 else " hidden"}><p class="muted">For {which}.</p>{trouble_kind(k, v, labs, True)}</div>'
                     for i, (k, _, which, labs) in enumerate(kinds))
    quiz = ('<div class="box"><h3>Quizzes</h3><ul>'
            "<li>Lab 1 is locked? Complete both parts of Lab 0: pass the Guidelines Quiz (75%) and get the Bongo setup check marked Complete.</li>"
            '<li>Accents won\'t type? On Windows, check that the taskbar says <b>ESP</b>. Setup steps are in <a href="#quizzes" data-goto="quizzes">Quizzes &amp; accents</a>.</li>'
            "<li>A quiz video or audio clip won't play? Reload the page in Chrome, then try Incognito.</li></ul></div>")
    return "\n".join([f'<div class="subtabs" role="tablist" aria-label="Kind of lab">{nav}</div>{panels}', quiz,
                      still + '<p>Addresses and what to include are in <a href="#contact" data-goto="contact">Contact</a>.</p></div>'])

def inlab_tab(context="lab", L=None):
    """Recording Bongo in the Lab, for section types with "inlab" (regular in-person sections)."""
    rooms = f'<p>{e(CAMPUS["room"])} ({e(CAMPUS["name"])})<br>{e(CAMPUS["hours"])}</p>'
    intro = ("You can record this lab at home or in the Language Lab." if context == "lab"
             else "You can record your labs at home or in the Language Lab. In the Lab:")
    bring = "Bring your notecard" + (" and slides" if (L and L["mode"] == "Camera + Screen") or context != "lab" else "") + "."
    note = f"<p>{es(C['wconline_note'])}</p>" if C.get("wconline_note") else "<p>Sign up with your UNG student email.</p>"
    return f"""<div class="labpanel"><h2>Record in the Lab</h2>
<p>{intro}</p>
<ul>
<li>The computers are ready for Bongo: camera, microphone, and Chrome are set up.</li>
<li>A Lab assistant can help you practice before you record.</li>
<li>{bring}</li>
<li>Book a time so a station is ready for you. Walk-ins are welcome when there's space.</li>
</ul>
<p><a class="btn gold" href="{CAMPUS["wconline"]}" target="_blank" rel="noopener">Book a lab time on WCONLINE</a></p>
{note}
<h3>Where</h3>{rooms}</div>"""

def where_you_record(v):
    return ("You can record at home or in the Language Lab (see <a href=\"#inlab\" data-goto=\"inlab\">Record in the Lab</a>)." if v.get("inlab")
            else "You record every lab on your own computer (Chrome on a laptop or desktop), somewhere quiet.")

def tutoring_line(v):
    """WCONLINE tutoring (help with a lab, practice). Separate from the lab session service (inlab)."""
    if not v.get("tutoring"): return ""
    return (f'<p>Need help with a lab? Book a free tutoring session ({e(v["tutoring"])}) with a Lab assistant on '
            f'<a href="{CAMPUS["wconline"]}" target="_blank" rel="noopener">WCONLINE</a> with your UNG email.</p>')

def booking_card(v):
    """Announcement card, the same shape in every setup."""
    if not v.get("tutoring"): return ""
    wk = C.get("platform") == "talkabroad" and not v.get("no_workshop")
    title, text, btn = (("Book your workshop", f'Sign up for a workshop {e(v.get("workshop_where", "in person"))} before each conversation, with your UNG email.', "Book a workshop on WCONLINE") if wk else
                        ("Need help with a lab?", f'Book a free tutoring session ({e(v["tutoring"])}) with a Lab assistant, with your UNG email.', "Book a session on WCONLINE"))
    return (f'<div class="labpanel" style="margin-top:14px"><h3 style="margin-top:0">{title}</h3><p>{text}</p>'
            f'<p style="margin:0"><a class="btn gold" href="{CAMPUS["wconline"]}" target="_blank" rel="noopener">{btn}</a></p></div>')

def bongo_page(L, v):
    tabs = [("assignment", f"Lab {L['n']}", "Assignment", assignment_tab(L, v), ""),
            ("vocabulary", e(L["ch_label"]), "Vocabulary", vocab_tab(L, v), ""),
            ("troubleshooting", "Help", "Troubleshooting", "<h2>Troubleshooting</h2>\n" + trouble_blocks(v, L), "")]
    if L.get("talk") and not v.get("no_workshop"):
        tabs.insert(1, ("workshop", "Before you talk", "Workshop", workshop_tab(L, v), ""))
    if v.get("inlab"):
        tabs.append(("inlab", "In person", "Record in the Lab", inlab_tab("lab", L), "lab"))
    return page(f"{C['course']} · Lab {L['n']} · {L['title']}", head("", L["n"]),
                f'<span lang="es">{e(L["title"])}</span> · Bongo assignment · {e(v["label"])} · {e(CAMPUS["name"])}', console(tabs, f"Lab {L['n']} sections"), num=str(L["n"]))

def walt_page(L, v):
    """FREN 1002 workshop alternative (2026-11-13, Daniel): the lab page's look and hero image, for students the Lab
    approved by email. D2L: a separate, restricted folder links these pages; submissions go to the lab's own dropbox.
    Only built for labs with "alt" in sections that have workshops, so no other course changes."""
    a, H = L["alt"], C["alt_help"]
    talk = a.get("talk", True)
    if a.get("mode") == "review": return walt_review_page(L, v)
    WL = dict(L, date=L.get("workshop_date") or L["date"]) if C.get("talk_dropbox") else L   # 2026-11-16: due with the workshop, not the conversation
    facts = [due_chip(WL, v), f'<li>{e(L["ch_label"])}</li>', '<li><b>Mode</b> Video + reflection sheet</li>', '<li><b>Length</b> 1.5–2 min</li>']
    still = ('<div class="note"><b>Your TalkAbroad conversation is still due</b>' + (f' {due_long(L, v)}, in the Lab {L["n"]} TalkAbroad dropbox' if C.get("talk_dropbox") and L["date"] else '') + '. This replaces the workshop only.</div>') if talk else ""
    task = [hero(L), f'<h2>Lab {L["n"]}: <span lang="es">{e(a["t"])}</span></h2>', '<ul class="facts">' + "".join(facts) + "</ul>",
            f'<p><b>Workshop alternative</b> for <span lang="es">{e(L["title"])}</span>, set up for you by the Language Lab. {es(a["context"])}</p>',
            '<div class="box"><h3>Your video: every item counts</h3><ol>' + "".join(f"<li>{es(x)}</li>" for x in a["task"]) + "</ol></div>",
            '<div class="box"><h3>Video rules</h3>' + ul(C["alt_rules"]) + "</div>",
            '<div class="box"><h3>What to do</h3>' + steps([
                '<b>Record</b> your video. Step-by-step help is on the <a href="#record" data-goto="record">Record</a> tab.',
                f'<b>Reflection sheet:</b> <a href="../workshop-alternative.html?lab={L["n"]}" target="_blank" rel="noopener">download the PDF form</a>, fill it in, and save it.',
                (f'<b>Submit</b> the video and the form to the <b>Lab {L["n"]} Workshop</b> dropbox by {due_long(WL, v) if WL["date"] else "the due time"}. See the <a href="#submit" data-goto="submit">Submit</a> tab.' if C.get("talk_dropbox") else
                 '<b>Submit</b> the video and the PDF to this lab\'s dropbox by the due time. See the <a href="#submit" data-goto="submit">Submit</a> tab.')]) + "</div>", still]
    devs = H["slides"] if a.get("mode") == "slides" else H["camera"]
    nav = "".join(f'<button type="button" role="tab" class="subtab" id="rk-{i}" aria-controls="rp-{i}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">{e(t)}</button>' for i, (t, _) in enumerate(devs))
    panels = "".join(f'<div role="tabpanel" id="rp-{i}" aria-labelledby="rk-{i}" tabindex="0"{"" if i == 0 else " hidden"}><div class="box"><h3>{e(t)}</h3>{steps(xs)}</div></div>' for i, (t, xs) in enumerate(devs))
    lead = ("This lab is a <b>slide video</b>: you talk over 3 slides with your camera on. Pick PowerPoint or Canva." if a.get("mode") == "slides"
            else "Pick what you'll record with. A phone is easiest.")
    record = ("<h2>Record your video</h2>" + '<div class="box"><h3>Before you record</h3>' + steps(H["before"]) + "</div>"
              + f'<p>{lead}</p><div class="subtabs" role="tablist" aria-label="Record with">{nav}</div>{panels}'
              + '<div class="box"><h3>Check your video</h3>' + steps(H["check"]) + "</div>")
    submit = "<h2>Submit</h2>" + '<div class="box"><h3>Upload to D2L</h3>' + steps(H["upload"]) + "</div>" + still
    tabs = [("assignment", f"Lab {L['n']}", "Your task", "\n".join(task), ""), ("record", "Step 2", "Record", record, ""),
            ("submit", "Step 3", "Submit", submit, ""), ("vocabulary", e(L["ch_label"]), "Vocabulary", vocab_tab(L, v), ""),
            ("help", "Help", "Troubleshooting", "<h2>Troubleshooting</h2>" + '<div class="box">' + ul(H["help"]) + "</div>", "")]
    return page(f"{C['course']} · Lab {L['n']} · Workshop alternative", head("", L["n"]),
                f'<span lang="es">{e(L["title"])}</span> · Workshop alternative · {e(v["label"])} · {e(CAMPUS["name"])}', console(tabs, f"Lab {L['n']} workshop alternative"), num=str(L["n"])).replace("</title>", '</title><meta name="robots" content="noindex">', 1)

def walt_review_page(L, v):
    """FREN 1002 workshop alternative for a lab with a TalkAbroad conversation (2026-11-16, Daniel), in two parts so no
    due date changes: Before (the five workshop stages done alone, Before form, Workshop dropbox, workshop due date) and
    After (After form from their own recording + a 1-minute correction video, TalkAbroad dropbox, with the conversation).
    Offered only by the professor or the lab coordinator."""
    a, H = L["alt"], C["alt_help"]
    WL = dict(L, date=L.get("workshop_date") or L["date"])
    q = f'?lab={L["n"]}'
    before = f'<a href="../workshop-alternative.html{q}" target="_blank" rel="noopener">Download the Before form</a>'
    after = f'<a href="../workshop-alternative-after.html{q}" target="_blank" rel="noopener">Download the After form</a>'
    lab = f'<a href="{e(CODE)}-lab-{L["n"]}-{SLUG}-{v.key}.html" target="_blank" rel="noopener">your Lab {L["n"]} page</a>'
    when = lambda X, alt: due_long(X, v) if X["date"] else alt
    facts = [due_chip(WL, v), f'<li>{e(L["ch_label"])}</li>', '<li><b>Mode</b> Workshop on your own + review</li>', '<li><b>Video</b> about 1 min</li>']
    task = [hero(L), f'<h2>Lab {L["n"]}: <span lang="fr">{e(a["t"])}</span></h2>', '<ul class="facts">' + "".join(facts) + "</ul>",
            f'<p><b>Workshop alternative</b> for <span lang="fr">{e(L["title"])}</span>, set up for you by the Language Lab. {e(a["context"])}</p>',
            f'<div class="box"><h3>1 · The workshop, on your own</h3><p>Due {when(WL, "by the workshop due date")}, in the <b>Lab {L["n"]} Workshop</b> dropbox.</p>' + steps([
                f'Open {lab} and its <b>Workshop</b> tab. Do the 5 stages <b>out loud, on your own</b>.',
                f'{before} and write each stage in it.',
                f'Upload the form to the <b>Lab {L["n"]} Workshop</b> dropbox. See the <a href="#submit" data-goto="submit">Submit</a> tab.']) + "</div>",
            f'<div class="box"><h3>2 · Your conversation</h3>' + steps([
                f'Have your TalkAbroad conversation as usual, by {when(L, "its due time")}. Ask your 2 questions and check your guesses.']) + "</div>",
            f'<div class="box"><h3>3 · After your conversation</h3><p>Due with your conversation, {when(L, "by its due time")}, in the <b>Lab {L["n"]} TalkAbroad</b> dropbox.</p>' + steps([
                f'Listen to your recording. {after} and fill it in.',
                f'Record about 1 minute: your 3 corrected sentences. After each one, add 1 new sentence of your own with {e(a["one"])}. See the <a href="#record" data-goto="record">Record</a> tab.',
                'Upload the After form and the video with your conversation and notes.']) + "</div>",
            '<div class="box"><h3>Video rules</h3>' + ul(C["alt_rules_review"]) + "</div>"]
    devs = H["camera"]
    nav = "".join(f'<button type="button" role="tab" class="subtab" id="rk-{i}" aria-controls="rp-{i}" aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">{e(t)}</button>' for i, (t, _) in enumerate(devs))
    panels = "".join(f'<div role="tabpanel" id="rp-{i}" aria-labelledby="rk-{i}" tabindex="0"{"" if i == 0 else " hidden"}><div class="box"><h3>{e(t)}</h3>{steps(xs)}</div></div>' for i, (t, xs) in enumerate(devs))
    record = ("<h2>Record your video</h2>" + '<div class="box"><h3>Before you record</h3>' + steps(H["before_review"]) + "</div>"
              + f'<p>Pick what you\'ll record with. A phone is easiest.</p><div class="subtabs" role="tablist" aria-label="Record with">{nav}</div>{panels}'
              + '<div class="box"><h3>Check your video</h3>' + steps(H["check_review"]) + "</div>")
    submit = "<h2>Submit</h2>" + '<div class="box"><h3>Upload to D2L, in two parts</h3>' + steps(H["upload_review"]) + "</div>"
    tabs = [("assignment", f"Lab {L['n']}", "Your task", "\n".join(task), ""), ("record", "Step 3", "Record", record, ""),
            ("submit", "Step 3", "Submit", submit, ""), ("vocabulary", e(L["ch_label"]), "Vocabulary", vocab_tab(L, v), ""),
            ("help", "Help", "Troubleshooting", "<h2>Troubleshooting</h2>" + '<div class="box">' + ul(H["help"]) + "</div>", "")]
    return page(f"{C['course']} · Lab {L['n']} · Workshop alternative", head("", L["n"]),
                f'<span lang="es">{e(L["title"])}</span> · Workshop alternative · {e(v["label"])} · {e(CAMPUS["name"])}', console(tabs, f"Lab {L['n']} workshop alternative"), num=str(L["n"])).replace("</title>", '</title><meta name="robots" content="noindex">', 1)

def lab0_page(v):
    """Lab 0: the Bongo setup check (Camera + Screen, PowerPoint slides). Ungraded; with the
    Guidelines Quiz it unlocks the labs through D2L release conditions."""
    if C.get("platform") == "talkabroad": return talk_lab0(v)
    l0 = POLICY["lab0"]
    L = {"n": 0, "mode": l0["mode"]}
    facts = ['<li class="due"><b>Due</b> in the first week</li>', f'<li><b>Mode</b> {l0["mode"]}</li>', f'<li><b>Length</b> {e(l0["length"])}</li>',
             '<li><b>Tries</b> unlimited</li>', '<li><b>Grade</b> 0%</li>']
    task = f"""<h2>Lab 0: {e(l0["title"])}</h2>
<ul class="facts">{"".join(facts)}</ul>
<p>{es(l0["context"])}</p>
<p>This is part 2 of Lab 0. Part 1 is the Guidelines Quiz.</p>
<div class="box"><h3>Make 3 PowerPoint slides</h3>
<p>Keywords or pictures only, no sentences. PowerPoint is free with your UNG account at <a href="https://office.com" target="_blank" rel="noopener">office.com</a>.</p>
<ol class="steps">{"".join(f"<li>{es(s)}</li>" for s in l0["slides"])}</ol></div>
<div class="box"><h3>Record in Bongo</h3>{steps([
    "Open your slides in their own window. Desktop PowerPoint: <b>View → Reading View</b>. PowerPoint online: start the slide show in its own Chrome tab.",
    "Open Lab 0 in Bongo and choose <b>Camera + Screen</b>. Allow the camera, the microphone, and screen sharing.",
    "Share the window (or tab) with your slides, not the Bongo tab.",
    "Talk through your slides for about a minute. " + es(l0["say"]),
    "Watch your recording, then <b>Submit</b>."])}
<p>Problems? See <a href="#troubleshooting" data-goto="troubleshooting">Troubleshooting</a>. If screen sharing still fails, record your slides in PowerPoint and upload the MP4: that's also what you'd do if a slide lab fails on a due date.</p></div>
<div class="box"><h3>What the Lab checks</h3><ul class="check">{"".join(f'<li><input type="checkbox" id="l0c{i}"><label for="l0c{i}">{es(c)}</label></li>' for i, c in enumerate(l0["checks"]))}</ul>
<p>{l0["marking"]}</p></div>
<div class="note"><b>Your labs unlock</b> when you've passed the Guidelines Quiz and this check is marked Complete.</div>"""
    tabs = [("assignment", "Lab 0", "Assignment", task, ""),
            ("troubleshooting", "Help", "Troubleshooting", "<h2>Troubleshooting</h2>\n" + trouble_blocks(v, L), "")]
    return page(f"{C['course']} · Lab 0 · {l0['title']}", head("", "0"),
                f'{e(l0["title"])} · Bongo assignment · {e(v["label"])} · {e(CAMPUS["name"])}', console(tabs, "Lab 0 sections"), num="0")

# ---------------- LAB folder description ----------------

def folder_page(v):
    n_labs = len(v.labs)
    dl = (f"Labs are due by {v.due_time} on the {v.due_day} listed in <a href=\"#tasks\" data-goto=\"tasks\">Lab tasks</a>."
          if v.has_dates else (f"Labs are due {v.due_day}s by {v.due_time}. Each lab's date is in D2L." if C.get("due_day_known") and v.due_day else "Each lab's due date and time are in D2L."))
    req = f"""<h2>Lab Requirement Summary</h2>
<ul class="facts"><li><b>{n_labs}</b> labs</li><li><b>{C["points"]}</b> points each</li><li class="due"><b>Due</b> {when_text(v)}</li></ul>
<p>{es(v.get("credit_line", C["credit_line"]).replace("{N_LABS}", str(n_labs)))}</p>
<div class="box"><h3>How this folder works</h3><ol class="steps">
<li>Complete <b>Lab 0</b> in the first week: pass the <b>Guidelines Quiz</b> (75% or higher; unlimited tries), then record the one-minute <b>Bongo setup check</b>. Together they unlock the labs.</li>
<li>For each lab, take the <b>Lab Mini-Quiz</b>. It's part of the lab grade.</li>
<li>Then record the <b>Lab Bongo</b> assignment. Its instructions are inside Bongo.</li>
</ol>
<p style="margin:8px 0 0">{where_you_record(v)} Set up Spanish accents before your first quiz: see <a href="#quizzes" data-goto="quizzes">Quizzes &amp; accents</a>.</p>
{"" if v.get("inlab") else tutoring_line(v)}</div>
<div class="box"><h3>Every video</h3>{video_rules_html()}</div>
<div class="box honesty"><h3>Academic honesty</h3>
<p>Every lab must be your own work, in your own words.</p>
<ul><li><b>Not allowed:</b> online translators, AI tools (for example ChatGPT or Google Translate), help from another person, or reading from a script.</li>
<li><b>Allowed while you prepare:</b> {es(v.get("allowed", C["allowed"]))}</li></ul>
<p>Breaking these rules is academic misconduct. It can mean a 0 on the lab and other consequences from the Office of Student Conduct. You agree to this in the Guidelines Quiz.</p></div>
<div class="box"><h3>Deadlines and technology</h3><p>{dl} Late work is not accepted.</p>
<p>{es(POLICY["responsibility"])} If Bongo fails, follow <a href="#troubleshooting" data-goto="troubleshooting">Troubleshooting</a>.</p>
<p>{es(POLICY["excused"])}</p>
<p>{es(POLICY["accommodations"])}</p></div>
<div class="box"><h3>Grades</h3><p>Language Lab staff grade the labs, not your professor, usually within a week. Send grade questions to the Language Lab.</p></div>
<p>Changes to dates or instructions are sent to your UNG email.</p>"""
    rows = "".join(f"""<div class="labrow"{f' data-due="{due_iso(L, v)}"' if L["date"] else ""}><span class="n" aria-hidden="true">{L["n"]}</span><div>
<p class="labstate" aria-hidden="false"></p>
<h3>Lab {L["n"]}: <span lang="es">{e(L["title"])}</span></h3>
<p class="meta"><b>{"Due " + due(L, v).rsplit(",", 1)[0] if L["date"] else "Due date in D2L"}</b> · {e(L["ch_label"])} · {L["mode"]}{(" · " + str(L["prompts"]) + " prompts") if L.get("prompts") else ""}{" · video comment" if L.get("peer") else ""}</p>
<p style="margin:0">{es(L["summary"])}</p></div></div>""" for L in v.labs)
    l0 = POLICY["lab0"]
    rows = f"""<div class="labrow"><span class="n" aria-hidden="true">0</span><div>
<h3>Lab 0: Guidelines Quiz + {e(l0["title"])}</h3>
<p class="meta"><b>Complete in the first week</b> · Quiz, then {l0["mode"]} · 0% of your grade</p>
<p style="margin:0">Pass the Guidelines Quiz, then record a one-minute test with your camera and PowerPoint slides. Together they unlock the labs.</p></div></div>""" + rows
    tasks = (f'<h2>Lab tasks</h2><p>{e(v.get("term", SEMESTER))}. ' + (f"All due by {v.due_time}." if v.has_dates else "Due dates are in D2L.") + f"</p>{rows}"
             '<div class="note" style="margin-top:16px"><b>Don\'t see the labs listed below this description?</b> They unlock when you pass the Guidelines Quiz. '
             'Review the <a href="#requirements" data-goto="requirements">Requirements</a> first.</div>')
    wc = tutoring_line(v)
    quizzes = f"""<h2>Quizzes &amp; accents</h2>
<div class="box"><h3>Mini-quizzes</h3><ul>
<li>Each lab starts with a mini-quiz in this folder. It's part of the lab grade.</li>
<li>Some quizzes have a video or audio clip. It plays inside the quiz.</li>
<li>Spelling and accents count in fill-in answers. When a question says so, write numbers as words.</li>
<li>Set up accents <b>before</b> your first quiz.</li></ul></div>
{K.section("fold", 3)}"""
    c = CAMPUS
    camps = f"""<div class="camp"><h3>{e(c["name"])} Language Lab</h3>
{e(c["coordinator"])}, coordinator<br>{e(c["room"])}<br>{e(c["hours"])}<br>
<a href="mailto:{c["email"]}">{c["email"]}</a><br>{e(c["phone"])}</div>"""
    contact = f"""<h2>Contact</h2>
<div class="grid2">{camps}</div>
<div class="box" style="margin-top:14px"><h3>When you email the Lab</h3><p>Send it from your UNG email and include:</p>{ul(C["email_include"])}</div>
{wc}"""
    tabs = [("requirements", "Start here", "Requirements", req, ""),
            ("tasks", f"Labs 1–{n_labs}", "Lab tasks", tasks, ""),
            ("quizzes", "Before quizzes", "Quizzes &amp; accents", quizzes, ""),
            ("troubleshooting", "Help", "Troubleshooting", "<h2>Troubleshooting</h2>\n" + trouble_blocks(v), ""),
            ("contact", "Help", "Contact", contact, "")]
    if v.get("inlab"):
        tabs.append(("inlab", "In person", "Record in the Lab", inlab_tab("folder"), "lab"))
    if C.get("no_accents"): tabs = [x for x in tabs if x[0] != "quizzes"]
    return page(f"{C['course']} · Language Lab", head(""),
                f"{e(C['course_name'])} · {e(v['sub'])} · {e(CAMPUS['name'])} · {e(v.get('term', SEMESTER))}", console(tabs, "Lab folder sections") + FOLDER_JS, kb=True)

FOLDER_JS = """<script>
window.addEventListener('DOMContentLoaded', function(){
  // Past labs fade, the next one due is marked "Current lab". Requirements opens first until
  // Lab 1 is due; after that the folder opens on Lab tasks (unless a link asks for a tab).
  var now = new Date(), rows = [].slice.call(document.querySelectorAll('.labrow[data-due]')), current = null;
  rows.forEach(function(r){
    var due = new Date(r.getAttribute('data-due')), st = r.querySelector('.labstate');
    if(now > due){ r.classList.add('past'); st.textContent = 'Closed'; }
    else if(!current){ current = r; r.classList.add('current'); st.textContent = 'Current lab'; }
  });
  if(rows.length && now > new Date(rows[0].getAttribute('data-due')) && !location.hash){
    var t = document.getElementById('tab-tasks'); if(t){ t.click(); try{history.replaceState(null,'',location.pathname+location.search);}catch(e){} }
  }
});
</script>"""

# ---------------- Quiz descriptions (start page) ----------------

def quiz_page(L, v):
    """Shown on the quiz's start page only, before the attempt. What students need while
    answering (videos, audio, new words, accent bar) is inside the quiz (build_quiz_pages.py)."""
    q = QUIZZES.get(L["id"], {})
    items = [b for b in q.get("blocks", []) if b["kind"] == "item"]
    facts = [due_chip(L, v), f'<li>{e(L["ch_label"])}</li>']
    if items:
        facts += [f'<li><b>{len(items)}</b> questions</li>', f'<li><b>{sum(i["points"] for i in items):g}</b> points</li>']
    facts.append('<li><b>1</b> attempt</li>')
    types = {i["type"] for i in items}
    media = L.get("quiz_media", True)
    h = [f'<main id="main" class="single"><h2>Lab {L["n"]} Mini-Quiz</h2>', '<ul class="facts">' + "".join(facts) + "</ul>",
         f"<p>This quiz is part of your Lab {L['n']} grade. It reviews:</p>" + ul(L["quiz_topics"])]
    if "quiz_rules" in L:
        h.append('<div class="box"><h3>Rules</h3>' + ul(L["quiz_rules"]) + "</div>")
    before = ["You get <b>one attempt</b>. Start when you have time to finish.",
              "Use Chrome on a computer, with headphones or sound on." if media else "Use Chrome on a computer."]
    if items and "Fill in the Blanks" not in types:
        before.append("No typing in this quiz: every question is multiple choice, true/false, select-all, or matching.")
    else:
        before.append("Spelling and accents count. Set up your Spanish keyboard first: LAB folder description › <b>Quizzes &amp; accents</b>. Inside the quiz there's also a bar to copy accents.")
    h.append('<div class="box"><h3>Before you start</h3><ul>' + "".join(f"<li>{x}</li>" for x in before) + "</ul></div></main>")
    return page(f"{C['course']} · Lab {L['n']} Mini-Quiz", head("", L["n"]),
                f'<span lang="es">{e(L["title"])}</span> · Mini-quiz', "\n".join(h), num=str(L["n"]))

def announcement_page(v):
    first = v.labs[0]
    tut = (f'<div class="labpanel" style="margin-top:14px"><h3 style="margin-top:0">Want to record in the Lab?</h3><p>It\'s optional. Lab computers are set up for Bongo, and a Lab assistant can help you practice.</p>'
           f'<p style="margin:0"><a class="btn gold" href="{CAMPUS["wconline"]}" target="_blank" rel="noopener">Book a lab time on WCONLINE</a></p></div>') if v.get("inlab") else booking_card(v)
    facts = (f'<li class="due"><b>Lab 1 due</b> {due_long(first, v)}</li><li><b>All labs</b> {when_text(v)}</li>' if v.has_dates
             else (f'<li class="due"><b>All labs</b> {when_text(v)}</li>' if C.get("due_day_known") and v.due_day else '<li class="due"><b>Due dates</b> listed in D2L</li>')) + "<li><b>Late work</b> not accepted</li>"
    body = f"""<main id="main" class="single">
<h2 lang="es">¡Bienvenidos al Language Lab!</h2>
<p>{C['course']} includes {len(v.labs)} short speaking labs. Everything is in one place: <b>Content › LAB</b>.</p>
<div class="btnrow"><a class="btn" href="{e(C["d2l"]["lab_folder"])}">Open the LAB folder</a><a class="btn ghost" href="{e(v["gq_link"])}">Take the Guidelines Quiz</a></div>
<div class="box"><h3>Get started</h3><ol class="steps">
<li>Open <b>Content › LAB</b> and read the folder description, starting with <b>Requirements</b>.</li>
<li>Set up Spanish accents on your computer. Steps are in the <b>Quizzes &amp; accents</b> tab.</li>
<li>Complete <b>Lab 0</b>: pass the <b>Guidelines Quiz</b> (75%), then record the one-minute <b>Bongo setup check</b>. Together they unlock Lab 1.</li>
<li>For each lab: take the <b>Mini-Quiz</b>, then record the <b>Bongo</b> assignment.</li>
</ol></div>
<ul class="facts">{facts}</ul>
{tut}
<p style="margin-top:14px">Questions? Email the {e(CAMPUS["name"])} Language Lab:</p>{emails_html()}
<p lang="es">¡Buen semestre!<br>UNG Language Lab</p>
</main>"""
    return page(f"{C['course']} · Language Lab announcement", head(""), f"Welcome · {e(v['sub'])} · {e(CAMPUS['name'])}", body)

def keyboard_page():
    body = f"""<main id="main" class="single">
<h2>Type Spanish accents</h2>
<p>Choose your computer. Set up once, then practice until the accents feel easy.</p>
{K.section("tut", 3)}
</main>"""
    return page(f"{C['course']} · Spanish keyboard", head(""), "Spanish keyboard: setup and practice", body, kb=True)

def guidelines_page():
    body = """<main id="main" class="single"><h2>Guidelines Quiz</h2>
<ul class="facts"><li><b>Pass</b> 75%</li><li><b>Tries</b> unlimited</li><li><b>Counts</b> your highest score</li></ul>
<p>Read the <b>Requirements</b> tab in the LAB folder description first. The questions come from it.</p>
<p>Three questions ask you to type a word with an accent. Set up your Spanish keyboard first: LAB folder description › <b>Quizzes &amp; accents</b>.</p>
<p>This is part 1 of Lab 0. Part 2 is the Bongo setup check. Together they unlock your labs.</p></main>"""
    return page(f"{C['course']} · Lab Guidelines Quiz", head(""), "Guidelines Quiz", body)

def campus_dir(code): return OUT / code

def outputs():
    """Pages for every campus: <course>/<campus>/d2l/... and <course>/<campus>/github/..."""
    out = []
    for camp in CAMPUSES:
        set_campus(camp["code"])
        D2L, GH = campus_dir(camp["code"]) / "d2l", campus_dir(camp["code"]) / "github"
        D2L.mkdir(parents=True, exist_ok=True); GH.mkdir(parents=True, exist_ok=True)
        seen = set()
        for v in VARIANTS:
            out.append((D2L / f"{CODE}-announcement-{v.key}.html", announcement_page(v)))
            out.append((D2L / f"{CODE}-lab-folder-{v.key}.html", folder_page(v)))
            out.append((GH / f"{CODE}-lab-0-{SLUG}-{v.key}.html", lab0_page(v)))
            for L in v.labs:
                out.append((GH / f"{CODE}-lab-{L['n']}-{SLUG}-{v.key}.html", bongo_page(L, v)))
                if L.get("alt") and C.get("alt_help") and not v.get("no_workshop"):   # FREN 1002 workshop alternative (2026-11-13)
                    out.append((GH / f"{CODE}-lab-{L['n']}-workshop-alt-{v.key}.html", walt_page(L, v)))
                name = D2L / f"{CODE}-lab-{L['n']}-quiz{quiz_suffix(v)}.html"
                if MINI_QUIZZES and name not in seen:
                    seen.add(name); out.append((name, quiz_page(L, v)))
        out.append((D2L / f"{CODE}-spanish-keyboard.html", keyboard_page()))
        out.append((D2L / f"{CODE}-guidelines-quiz.html", guidelines_page()))
    set_campus(CAMPUSES[0]["code"])
    return out

if __name__ == "__main__":
    import shutil
    for old in ("d2l", "github"):          # pre-campus layout
        if (OUT / old).exists(): shutil.rmtree(OUT / old)
    out = outputs()
    for p, s in out:
        p.write_text(s, encoding="utf8")
    print(f"{C['course']}: {len(out)} pages written for {len(CAMPUSES)} campuses ({', '.join(c['name'] for c in CAMPUSES)})")
    for v in VARIANTS:
        print(f"  {v['label']:10} " + (", ".join(f"Lab {L['n']} {L['title']} ({L['date'].strftime('%b %d') if L['date'] else 'no date'})" for L in v.labs)))
