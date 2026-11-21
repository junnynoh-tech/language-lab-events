"""Student-facing GitHub Pages site for a course (the <code>-instructions repository).

    LABS_COURSE=<course source folder> python3 make_site.py   ->  <course>/site/

site/ mirrors the repository root, ready to push:
  index.html                                  pick section type + campus → your labs, due dates, Bongo pages
  <campus>/<code>-lab-N-bongo-<variant>.html  Bongo instructions (link these from the Bongo descriptions in D2L)
  <campus>/<code>-lab-folder-<variant>.html   the same LAB folder description students see in D2L

The index adds nothing new: it lists the labs and shows the pages students already get in D2L.
"""
import json, shutil
import build as B

C, e, es = B.C, B.e, B.es
SITE = B.OUT / "site"

def data():
    out = []
    for v in B.VARIANTS:
        out.append({"key": v.key, "label": v["label"], "sub": v["sub"], "time": v.due_time or "", "day": v.due_day or "",
                    "labs": [{"n": L["n"], "title": L["title"], "ch": L["ch_label"],
                              "mode": L["mode"] + (f" · {L['prompts']} prompts" if L.get("prompts") else ""),
                              "due": B.due_iso(L, v) if L["date"] else "", "dueText": B.due(L, v) if L["date"] else "Due date in D2L",
                              "summary": L["summary"]} for L in v.labs]})
    return out

CSS = """
.pick{max-width:1060px;margin:18px auto 0;padding:0 24px;display:flex;flex-wrap:wrap;gap:10px 18px;align-items:flex-end;}
.pick label{display:block;font-weight:700;font-size:.9rem;margin:0 0 4px;color:var(--navy);}
.pick select{font:inherit;padding:8px 12px;border:1.5px solid var(--line-2);border-radius:8px;min-height:46px;background:var(--white);min-width:200px;}
.pick p{margin:0;color:var(--muted);font-size:.95rem;flex-basis:100%;}
.labs{list-style:none;padding:0;margin:0 0 16px;display:grid;gap:8px;}
.labs li{margin:0;}
.lb{display:grid;grid-template-columns:44px 1fr;gap:10px;width:100%;text-align:left;font:inherit;background:var(--white);border:1.5px solid var(--line);border-radius:10px;padding:10px 12px;cursor:pointer;color:var(--ink);}
.lb:hover{border-color:var(--navy);}
.lb[aria-pressed="true"]{border-color:var(--navy);box-shadow:0 0 0 2px var(--navy) inset;}
.lb .n{font-family:'Fraunces',Georgia,serif;font-weight:900;font-size:1.7rem;color:var(--blue);line-height:1;}
.lb b{display:block;color:var(--navy);font-size:1.05rem;}
.lb .m{display:block;font-size:.92rem;color:var(--muted);}
.lb .st{display:inline-block;font-size:.8rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:2px;}
.lb.past{background:var(--cream);border-style:dashed;} .lb.past .n,.lb.past b{color:var(--muted);}
.lb.current{border:2px solid var(--gold);background:var(--gold-lt);}
.lb.current .st{background:var(--gold-dk);color:#fff;border-radius:999px;padding:1px 10px;}
.pv{border:1px solid #cdd5dc;border-radius:12px;overflow:hidden;background:#fff;box-shadow:0 6px 24px rgba(0,0,0,.08);}
.pvbar{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;align-items:center;background:#f9fbff;border-bottom:1px solid #e3e9f1;padding:8px 14px;font-size:.95rem;}
.pv iframe{display:block;width:100%;height:min(85vh,1000px);border:0;}
"""

JS = r"""
var DATA = __DATA__, CODE = '__CODE__', KEY = 'labsite-' + CODE;
var selV = document.getElementById('selV'), selC = document.getElementById('selC');
(function(){ var q = new URLSearchParams(location.search), saved = {};
  try{ saved = JSON.parse(localStorage.getItem(KEY) || '{}'); }catch(e){}
  var v = q.get('section') || saved.v, c = q.get('campus') || saved.c;
  if(v && [...selV.options].some(o => o.value === v)) selV.value = v;
  if(c && [...selC.options].some(o => o.value === c)) selC.value = c; })();
var current = null, chosen = null;
function render(){
  var v = DATA.find(x => x.key === selV.value), c = selC.value, now = new Date(), list = document.getElementById('labs');
  try{ localStorage.setItem(KEY, JSON.stringify({v: v.key, c: c})); }catch(e){}
  document.getElementById('due').textContent = v.time ? `${v.labs.length} labs, due ${v.day}s at ${v.time}. Late work is not accepted.` : `${v.labs.length} labs. Due dates are in D2L.`;
  current = null;
  list.innerHTML = v.labs.map(L => {
    var st = '', cls = '';
    if(L.due){ if(now > new Date(L.due)){ cls = 'past'; st = 'Closed'; } else if(!current){ current = L.n; cls = 'current'; st = 'Current lab'; } }
    return `<li><button type="button" class="lb ${cls}" data-n="${L.n}" aria-pressed="false"><span class="n" aria-hidden="true">${L.n}</span><span>${st ? `<span class="st">${st}</span>` : ''}<b lang="es">Lab ${L.n}: ${L.title}</b><span class="m">${L.dueText} · ${L.ch} · ${L.mode}</span><span class="m">${L.summary}</span></span></button></li>`;
  }).join('');
  list.querySelectorAll('.lb').forEach(b => b.addEventListener('click', () => open(+b.dataset.n, true)));
  document.getElementById('folder').src = `${c}/${CODE}-lab-folder-${v.key}.html`;
  open(chosen && chosen <= v.labs.length ? chosen : (current || 1), false);
}
function open(n, user){
  var v = DATA.find(x => x.key === selV.value), L = v.labs[n - 1], url = `${selC.value}/${CODE}-lab-${n}-bongo-${v.key}.html`;
  chosen = user ? n : chosen;
  document.querySelectorAll('.lb').forEach(b => b.setAttribute('aria-pressed', +b.dataset.n === n));
  var f = document.getElementById('bongo'); f.src = url; f.title = `Bongo instructions, Lab ${n}: ${L.title}`;
  document.getElementById('pvname').textContent = `Lab ${n}: ${L.title} · Bongo instructions`;
  document.getElementById('pvopen').href = url;
}
selV.addEventListener('change', () => { chosen = null; render(); });
selC.addEventListener('change', render);
render();
"""

def index():
    opts_v = "".join(f'<option value="{v.key}">{e(v["sub"])}</option>' for v in B.VARIANTS)
    opts_c = "".join(f'<option value="{c["code"]}">{e(c["name"])}</option>' for c in B.CAMPUSES)
    pick = f"""<div class="pick no-print">
<div><label for="selV">My section</label><select id="selV">{opts_v}</select></div>
<div><label for="selC">My campus</label><select id="selC">{opts_c}</select></div>
<p>Not sure? It's in your course name in D2L. Your choice is remembered on this device.</p>
</div>"""
    labs = """<h2>My labs</h2>
<p id="due"></p>
<ul class="labs" id="labs" aria-label="Labs"></ul>
<div class="pv"><div class="pvbar"><b id="pvname"></b><a id="pvopen" target="_blank" rel="noopener">Open in a new tab</a></div><iframe id="bongo" title="Bongo instructions"></iframe></div>"""
    req = """<h2>Requirements &amp; help</h2>
<p>The same LAB folder description you see in D2L: requirements, quizzes and accents, troubleshooting, and contact.</p>
<div class="pv"><iframe id="folder" title="LAB folder description"></iframe></div>"""
    body = pick + B.console([("labs", "Start here", "My labs", labs, ""), ("help", "From D2L", "Requirements &amp; help", req, "")], "Sections")
    doc = B.page(f"{C['course']} · Language Lab", B.head(""), f"{e(C['course_name'])} · Lab instructions", body)
    doc = doc.replace("</style>", CSS + "</style>", 1).replace("</body>", "<script>" + JS.replace("__DATA__", json.dumps(data(), ensure_ascii=False).replace("</", "<\\/")).replace("__CODE__", B.CODE) + "</script>\n</body>")
    return doc

def main():
    if SITE.exists(): shutil.rmtree(SITE)
    SITE.mkdir()
    n = 0
    for c in B.CAMPUSES:
        d = SITE / c["code"]; d.mkdir()
        for f in (B.OUT / c["code"] / "github").glob("*.html"): shutil.copy(f, d / f.name); n += 1
        for f in (B.OUT / c["code"] / "d2l").glob(f"{B.CODE}-lab-folder-*.html"): shutil.copy(f, d / f.name); n += 1
    (SITE / "index.html").write_text(index(), encoding="utf8")
    print(f"site/: index.html + {n} pages in {len(B.CAMPUSES)} campus folders")

if __name__ == "__main__":
    main()
