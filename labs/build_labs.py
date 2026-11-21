"""Build the Language Lab's student instruction pages from the editable sources in labs/ (2026-11-21, Daniel).

    python3 labs/build_labs.py                 build every course whose status is "approved" -> instructions/<code>/
    python3 labs/build_labs.py --sync-engine   first copy the engine from TeachingOS (labs/lab-builder), then build
    python3 labs/build_labs.py --import CODE SRC   (TeachingOS only) bring a course's local source into labs/courses/CODE
    python3 labs/build_labs.py --to-local      (TeachingOS only) write the GitHub edits back to the local source folders

Runs on GitHub after every save in the website editor or the console (.github/workflows/labs.yml), so an edit is live in
about two minutes. Same engine as TeachingOS (labs/lab-builder), copied to labs/engine/ by --sync-engine.

What lives where (no student data anywhere):
  labs/registry.json       languages, courses, status, lab type, theme, due day and time      (console › Student view, editor)
  labs/types.json          lab types (Bongo video, TalkAbroad with workshops, Global Passport…)
  labs/themes.json         page themes: colors and an optional header pattern                (editor › Lab themes)
  labs/shared/policy.json  Language Lab policy every course shares                           (editor › Lab policy)
  labs/shared/lab-due-dates.json   the Semester plan's export (Lab calendar › Share)        (upload it in the editor)
  labs/courses/<code>/course.json  one course's instructions, in the editor's shape (named fields, not lists of lists)
  labs/courses/<code>/vocab.json, quiz-facts.json (question counts and points only: no questions or answers)
  instructions/<code>/     the built pages (don't edit: rebuilt on every save) + instructions/manifest.json

The editor stores lists of pairs as named fields ({"question", "guide"} instead of ["…", "…"]); decode() turns them back
into the engine's shape, and the round trip is checked (python3 labs/build_labs.py --check).
"""
import json, os, re, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path

LABS = Path(__file__).resolve().parent
REPO = LABS.parent
OUT = REPO / "instructions"
ENGINE = LABS / "engine"
ENGINE_FILES = ["build.py", "make_site.py", "keyboard.py", "keyboard_fr.py", "fr_locale.py"]
load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
dump = lambda o: json.dumps(o, ensure_ascii=False, indent=1) + "\n"

# ---------------- codec: lists of pairs <-> named fields ----------------
PAIR = ["question", "guide"]
WORDS = ["title", ("words", ["word", "meaning"])]
TUPLES = {  # field: names of the positions (a tuple inside means a nested list of tuples)
    "questions": PAIR, "question_groups": ["title", ("questions", PAIR)], "parts": ["title", "items"], "lab_vocab": WORDS,
    "lab_images": ["label", "image"], "photo_links": ["name", "url", "note"],
}
ONE = {"hero": ["image", "credit", "url"]}             # a single tuple, not a list of them
NESTED = {"quiz_words": {"groups": WORDS}}             # tuples one level down

def _enc(t, spec):
    o = {}
    for i, x in enumerate(t):
        k = spec[i]
        if isinstance(k, tuple): o[k[0]] = [_enc(y, k[1]) for y in x]
        else: o[k] = x
    return o

def _dec(o, spec):
    out = []
    for k in spec:
        name = k[0] if isinstance(k, tuple) else k
        if name not in o: break                      # optional trailing position (a photo link without a note)
        out.append([_dec(y, k[1]) for y in o[name]] if isinstance(k, tuple) else o[name])
    return out

def encode_lab(L):
    L = dict(L)
    for k, spec in TUPLES.items():
        if k in L: L[k] = [_enc(t, spec) for t in L[k]]
    for k, spec in ONE.items():
        if k in L: L[k] = _enc(L[k], spec)
    for k, sub in NESTED.items():
        if k in L: L[k] = dict(L[k], **{s: [_enc(t, spec) for t in L[k][s]] for s, spec in sub.items() if s in L[k]})
    return L

# The website editor can save a field an item never had as "", [], {}, null (or an object of those). The engine checks
# whether keys exist ("questions" in L), so empty values are dropped at the lab, section-type and course level.
def empty(v): return v is None or v == "" or (isinstance(v, (list, dict)) and all(empty(x) for x in (v.values() if isinstance(v, dict) else v)))
def prune(d, keep=()): return {k: v for k, v in d.items() if k in keep or not empty(v)}

def decode_lab(L):
    L = prune(L)
    for k, spec in TUPLES.items():
        if k in L: L[k] = [_dec(t, spec) for t in L[k]]
    for k, spec in ONE.items():
        if k in L: L[k] = _dec(L[k], spec)
    for k, sub in NESTED.items():
        if k in L: L[k] = dict(L[k], **{s: [_dec(t, spec) for t in L[k][s]] for s, spec in sub.items() if s in L[k]})
    return L

# Section types are a dict keyed by type in the engine; the editor wants a list. A type's lab overrides (e.g. SPAN 1002
# Stone's own Lab 2) are a dict keyed by lab id: a list of {"lab": id, ...} in the editor. tutoring False <-> "" (none).
def enc_variant(k, v):
    v = dict(v, key=k)
    if "overrides" in v: v["overrides"] = [dict(encode_lab(o), lab=lid) for lid, o in v["overrides"].items()]
    if v.get("tutoring") is False: v["tutoring"] = ""
    return v

def dec_variant(v):
    v = prune({k: x for k, x in v.items() if k != "key"}, keep=("tutoring",))
    if "overrides" in v: v["overrides"] = {o["lab"]: decode_lab({k: x for k, x in o.items() if k != "lab"}) for o in v["overrides"]}
    if v.get("tutoring") == "": v["tutoring"] = False
    return v

def encode(C):
    C = dict(C, labs=[encode_lab(L) for L in C["labs"]])
    C["variants"] = [enc_variant(k, v) for k, v in C["variants"].items()]
    return C

def decode(C):
    C = dict(prune(C), labs=[decode_lab(L) for L in C["labs"]])
    C["variants"] = {v["key"]: dec_variant(v) for v in C["variants"]}
    return C

# ---------------- themes ----------------
def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]

def contrast(a, b):
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + .05) / (y + .05)

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
def theme_css(key, themes, warn):
    """CSS appended to every page. The default theme (no "colors") adds nothing, so pages stay as they were."""
    t = themes.get(key)
    if not t: warn.append(f"Theme “{key}” isn't in labs/themes.json, so the default colors are used."); return ""
    c = {k: v for k, v in (t.get("colors") or {}).items() if v}   # empty boxes = keep the approved color
    if not c: return ""
    bad = [k for k, v in c.items() if not HEX.match(str(v))]
    if bad: warn.append(f"Theme “{t.get('label', key)}”: {', '.join(bad)} must be hex colors like #1A3A6B. Default colors used."); return ""
    checks = [("header", "#FFFFFF", 4.5, "white text on the header"), ("header", "#D6E2F0", 4.5, "the header's small text"), ("header", c.get("header_accent", "#9cc9ee"), 3, "the header's colored words"),
              ("link", "#F7F9FC", 4.5, "links on the page"), ("button", "#FFFFFF", 4.5, "white text on buttons")]
    fails = [f"{why} ({contrast(c[k], o):.1f}:1, needs {need}:1)" for k, o, need, why in checks if k in c and contrast(c[k], o) < need]
    if fails: warn.append(f"Theme “{t.get('label', key)}” is hard to read: {'; '.join(fails)}. Default colors used until it's fixed."); return ""
    m = {"header": "--navy", "header_accent": "--sky", "link": "--blue", "button": "--red", "highlight": "--gold"}
    css = ":root{" + "".join(f"{m[k]}:{v};" for k, v in c.items() if k in m) + "}"
    if c.get("button"): css += f".flag i{{background:{c['button']};}}"
    if c.get("highlight"): css += f".flag i:nth-child(2){{background:{c['highlight']};}}"
    if t.get("pattern"):
        svg = f"<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120' viewBox='0 0 120 120'><g fill='none' stroke='white' stroke-opacity='.14' stroke-width='2'>{t['pattern']}</g></svg>"
        uri = "data:image/svg+xml," + re.sub(r"[<>#%\"]", lambda x: "%{:02X}".format(ord(x.group())), svg)
        css += f'header.top{{background-image:url("{uri}");background-repeat:repeat;}}@media print{{header.top{{background-image:none;}}}}'
    return css

# ---------------- one course ----------------
def stage(code, R, themes, warn, course=None, policy=None):
    """Lay out a temp folder the engine can build from. course: the course.json contents (the console's live preview
    passes its unsaved copy; policy likewise for shared/policy.json); None reads the file. Returns (work, engine folder, env, decoded course)."""
    reg = R["courses"][code]
    src = LABS / "courses" / code
    C = decode(course if course is not None else load(src / "course.json"))
    dd = load(LABS / "shared" / "lab-due-dates.json")
    # due day and time come from the registry (faculty-approved); dates from the Semester plan's export when it has them
    for v in C["variants"].values():
        k = v.get("due_key")
        if not k or not k.endswith("_regular"): continue
        cls = next((c for c in dd["classes"] if c["key"] == k), None)
        if cls and (cls.get("due_day"), cls.get("due_time")) != (reg["due_day"], reg["due_time"]):
            warn.append(f"{reg['course']}: the Semester plan says {cls.get('due_day')}s at {cls.get('due_time')}, the course is set to {reg['due_day']}s at {reg['due_time']}. "
                        "Pages use the course setting; fix the Semester plan's Lab calendar so the two agree.")
        if cls: cls.update(due_day=reg["due_day"], due_time=reg["due_time"])
        else: dd["classes"].append({"key": k, "due_day": reg["due_day"], "due_time": reg["due_time"], "labs": []})
    C.setdefault("policy_overrides", {})["due_time"] = reg["due_time"]
    C["due_day_known"] = True
    C["theme_css"] = theme_css(reg.get("theme", "ung"), themes, warn)
    work = Path(tempfile.mkdtemp(prefix=f"labs-{code}-"))
    eng = work / "engine"; shutil.copytree(ENGINE, eng)
    (eng / "policy.json").write_text(dump(policy if policy is not None else load(LABS / "shared" / "policy.json")), encoding="utf-8")
    s = work / "course" / "source"; s.mkdir(parents=True)
    (work / "dd.json").write_text(dump(dd), encoding="utf-8")
    C["due_dates_json"] = str(work / "dd.json"); C["campuses_json"] = str((LABS / "shared" / "campuses.json").resolve())
    (s / f"{code}-labs.json").write_text(dump(C), encoding="utf-8")
    shutil.copy(src / "vocab.json", s / "vocab.json")
    if (src / "quiz-facts.json").exists(): shutil.copy(src / "quiz-facts.json", s / "quizzes.json")
    env = dict(os.environ, LABS_COURSE=str(s))
    return work, eng, env, C

def build_course(code, R, themes, warn):
    work, eng, env, C = stage(code, R, themes, warn)
    reg = R["courses"][code]
    src = LABS / "courses" / code
    try:
        for step in ("build.py", "make_site.py"):
            r = subprocess.run([sys.executable, step], cwd=eng, env=env, capture_output=True, text=True)
            if r.returncode: raise RuntimeError(f"{code} {step} failed:\n{r.stderr[-2000:]}")
        dest = OUT / code
        if dest.exists(): shutil.rmtree(dest)
        shutil.copytree(work / "course" / "site", dest)
        campuses = load(LABS / "shared" / "campuses.json")["campuses"]
        if C.get("campus_codes"): campuses = [c for c in campuses if c["code"] in C["campus_codes"]]
        for c in campuses:   # the D2L pages too (announcement, Guidelines Quiz and mini-quiz descriptions), for previews and copying
            d2l = work / "course" / c["code"] / "d2l"
            if d2l.exists(): shutil.copytree(d2l, dest / c["code"] / "d2l")
        byid = {L["id"]: L for L in C["labs"]}
        def vlabs(v):   # the labs in this section type's order, with its own titles
            return [{"n": i, "id": lid, "title": (v.get("overrides", {}).get(lid, {}).get("title") or byid[lid]["title"]), "mode": byid[lid].get("mode", "")}
                    for i, lid in enumerate(v.get("order") or list(byid), 1)]
        return {"course": reg["course"], "variants": [{"key": k, "label": v["label"], "sub": v.get("sub", ""), "labs": vlabs(v)} for k, v in C["variants"].items()],
                "campuses": [{"code": c["code"], "name": c["name"]} for c in campuses],
                "labs": [{"id": L["id"], "title": L["title"], "mode": L.get("mode", ""), "ch": L.get("ch_label", "")} for L in C["labs"]],
                "slug": C.get("page_slug", "bongo"), "mini_quizzes": C.get("mini_quizzes", True), "has_policy": bool(load(src / "course.json").get("policy_overrides")),
                "files": sorted(str(p.relative_to(dest)).replace(os.sep, "/") for p in dest.rglob("*.html"))}
    finally:
        shutil.rmtree(work, ignore_errors=True)

def build():
    R, themes = load(LABS / "registry.json"), load(LABS / "themes.json")["themes"]
    man = {"_about": "Written by labs/build_labs.py. The console's Student view reads it.", "built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "semester": load(LABS / "shared" / "lab-due-dates.json").get("semester_label", ""), "courses": {}, "warnings": []}
    OUT.mkdir(exist_ok=True)
    (OUT / "d2l").mkdir(exist_ok=True)   # the one file coordinators upload to D2L (labs/d2l/lab-page.html)
    shutil.copy(LABS / "d2l" / "lab-page.html", OUT / "d2l" / "lab-page.html")
    for code, reg in R["courses"].items():
        if reg.get("status") != "approved" or not (LABS / "courses" / code / "course.json").exists(): continue
        warn = []
        try:
            man["courses"][code] = build_course(code, R, themes, warn)
            print("built", code, len(man["courses"][code]["files"]), "pages")
        except Exception as ex:   # one broken course doesn't stop the others; the console shows the message
            warn.append(f"{reg['course']} didn't build, so its pages weren't changed. {ex}")
            print(ex, file=sys.stderr)
        man["warnings"] += [{"course": code, "text": w} for w in warn]
    (OUT / "manifest.json").write_text(dump(man), encoding="utf-8")
    for w in man["warnings"]: print("WARNING", w["course"], w["text"])
    return man

# ---------------- TeachingOS helpers ----------------
TOS = REPO.parent / "lab-builder"
def sync_engine():
    ENGINE.mkdir(exist_ok=True)
    for f in ENGINE_FILES: shutil.copy(TOS / f, ENGINE / f)
    print("engine copied from", TOS)

QUIZ_FACTS = lambda q: {lid: {"blocks": [{"kind": "item", "type": b["type"], "points": b["points"]} for b in x.get("blocks", []) if b.get("kind") == "item"]} for lid, x in q.items()}

def import_course(code, src):
    src = Path(src); d = LABS / "courses" / code; d.mkdir(parents=True, exist_ok=True)
    C = load(next(src.glob("*-labs.json")))
    for k in ("due_dates_json", "campuses_json"): C.pop(k, None)
    C = prune(C)                                            # empty top-level keys mean the same as missing ones
    for L in C["labs"]: L.setdefault("quiz_media", True)   # the engine's default, written out so the editor can't flip it
    assert decode(encode(C)) == C, "round trip changed the course"
    (d / "course.json").write_text(dump(encode(C)), encoding="utf-8")
    shutil.copy(src / "vocab.json", d / "vocab.json")
    if (src / "quizzes.json").exists(): (d / "quiz-facts.json").write_text(dump(QUIZ_FACTS(load(src / "quizzes.json"))), encoding="utf-8")
    print("imported", code, "from", src)

def to_local():
    """GitHub is the source for approved courses: write their edits back to the TeachingOS folders the other tools read."""
    for code, reg in load(LABS / "registry.json")["courses"].items():
        if reg.get("status") != "approved" or not reg.get("local_source"): continue
        dst = REPO.parent / reg["local_source"]; f = next(dst.glob("*-labs.json"))
        old = load(f); C = decode(load(LABS / "courses" / code / "course.json"))
        for k in ("due_dates_json", "campuses_json"): C[k] = old[k]
        f.write_text(dump(C), encoding="utf-8"); shutil.copy(LABS / "courses" / code / "vocab.json", dst / "vocab.json")
        print("wrote", f)

def check():
    ok = True
    for d in sorted((LABS / "courses").iterdir()):
        C = load(d / "course.json")
        if encode(decode(C)) != C: ok = False; print("round trip differs:", d.name)
    print("round trip ok" if ok else "round trip FAILED"); return ok

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--import" in a: i = a.index("--import"); import_course(a[i + 1], a[i + 2]); sys.exit()
    if "--to-local" in a: to_local(); sys.exit()
    if "--check" in a: sys.exit(0 if check() else 1)
    if "--sync-engine" in a: sync_engine()
    build()
