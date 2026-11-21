"""Live preview for the console's page editor (admin/student-view.html, Edit tab).

The console runs this file in the browser (Pyodide) with the same engine the GitHub Action uses, so the preview is the
real page. Every piece of text that comes from course.json is tagged on the way through the engine: render() builds the
course from an unsaved copy whose strings carry invisible markers, and page() turns the markers into
<span data-k="N">…</span>, where N indexes paths() (the place in course.json the text came from). Markers that land
inside tags, scripts or styles are removed, so those spots just aren't clickable.

Students never get these pages: the Action builds from course.json without markers. `python3 labs/preview.py --test`
checks that a marked build with the markers removed is byte-for-byte the normal build, for every approved course.
"""
import json, os, re, runpy, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_labs as BL

A, B, E = "", "", ""          # start, end of the id, end of the text (Unicode private use)
# Values the engine compares, looks up or turns into addresses; marking them would change the page, so they stay plain.
SKIP = {"id", "key", "lab", "mode", "image", "url", "due_key", "order", "page_slug", "campus_codes", "lang", "code",
        "type", "kind", "icon", "tutoring", "platform", "slug", "audio", "video", "file", "href", "src",
        "course_code", "vocab_label", "locale", "word"}
_STEPS = ("build.py", "make_site.py")
_MODS = ("build", "make_site", "keyboard", "keyboard_fr", "fr_locale")
_state = {"work": None, "paths": []}

def mark(obj, root, paths):
    """A copy of obj (course.json or the shared policy) with every editable string wrapped in markers. Each string's
    place, starting with root ("course" or "policy"), is added to paths."""
    def walk(v, p):
        if isinstance(v, dict): return {k: (x if k in SKIP or k.startswith("_") else walk(x, p + [k])) for k, x in v.items()}
        if isinstance(v, list): return [walk(x, p + [i]) for i, x in enumerate(v)]
        if isinstance(v, str) and v.strip():
            paths.append(p); return f"{A}{len(paths) - 1}{B}{v}{E}"
        return v
    return walk(obj, [root])

_ANY = re.compile(f"{A}\\d+{B}|{E}")
_ESC = re.compile(r"\\ue00[012]|%EE%80%8[012]|&#(?:57344|57345|57346|xe00[012]);", re.I)   # markers escaped by json, quote(), html
def strip(html):
    return _ESC.sub("", _ANY.sub("", _strip_ids(html)))

def _strip_ids(html):   # an escaped start marker is followed by its id digits and an escaped end-of-id marker
    return re.sub(r"(?:\\ue000|%EE%80%80|&#(?:57344|xe000);)\d+(?=\\ue001|%EE%80%81|&#(?:57345|xe001);)", "", html, flags=re.I)

_RAW = re.compile(r"(<(script|style|title|textarea)\b[^>]*>)(.*?)(</\2>)", re.S | re.I)
def annotate(html):
    """Markers in text become <span data-k>; markers anywhere else are removed."""
    html = _strip_ids(html)
    html = _ESC.sub("", html)
    html = _RAW.sub(lambda m: m.group(1) + _ANY.sub("", m.group(3)) + m.group(4), html)
    html = re.sub(r"<[^>]*>", lambda m: _ANY.sub("", m.group()), html)
    html = re.sub(f"{A}(\\d+){B}", r'<span data-k="\1">', html)
    return html.replace(E, "</span>")

def _run(eng, env):
    old_env, old_cwd, old_path = dict(os.environ), os.getcwd(), list(sys.path)
    os.environ.update(env); os.chdir(eng); sys.path.insert(0, str(eng))
    for m in _MODS: sys.modules.pop(m, None)
    try:
        for step in _STEPS: runpy.run_path(str(eng / step), run_name="__main__")
    finally:
        os.environ.clear(); os.environ.update(old_env); os.chdir(old_cwd); sys.path[:] = old_path

def render(code, course=None, policy=None, marked=True):
    """Build the course from course.json and shared/policy.json contents (JSON text or objects; None reads the saved
    files). Returns the warnings as JSON."""
    if isinstance(course, str): course = json.loads(course)
    if isinstance(policy, str): policy = json.loads(policy)
    if course is None: course = BL.load(BL.LABS / "courses" / code / "course.json")
    if policy is None: policy = BL.load(BL.LABS / "shared" / "policy.json")
    paths = []
    if marked: course, policy = mark(course, "course", paths), mark(policy, "policy", paths)
    R, themes = BL.load(BL.LABS / "registry.json"), BL.load(BL.LABS / "themes.json")["themes"]
    warn = []
    if _state["work"]: shutil.rmtree(_state["work"], ignore_errors=True)
    work, eng, env, _ = BL.stage(code, R, themes, warn, course, policy)
    _state.update(work=work, paths=paths)
    _run(eng, env)
    return json.dumps(warn)

def files():  # returned as JSON text for the console
    return json.dumps(_files())

def _files():
    """Every page of the last render, as paths like those under instructions/<code>/ (gvl/…, gvl/d2l/…, index.html)."""
    w = _state["work"] / "course"; out = []
    for p in (w / "site").rglob("*.html"): out.append(str(p.relative_to(w / "site")).replace(os.sep, "/"))
    for p in w.glob("*/d2l/*.html"): out.append(str(p.relative_to(w)).replace(os.sep, "/"))
    return sorted(set(out))

def page(rel):
    w = _state["work"] / "course"
    f = w / "site" / rel
    if not f.exists(): f = w / rel
    return annotate(f.read_text(encoding="utf-8"))

def paths(): return json.dumps(_state["paths"])

def _test():
    import filecmp, tempfile
    R = BL.load(BL.LABS / "registry.json"); ok = True
    for code, reg in R["courses"].items():
        if reg.get("status") != "approved": continue
        render(code, marked=False); plain = {f: _read(f) for f in _files()}
        render(code, marked=True); marked = {f: _read(f) for f in _files()}
        n = len(_state["paths"]); spans = sum(page(f).count("data-k=") for f in _files())
        bad = [f for f in plain if strip(marked.get(f, "")) != plain[f]] + [f for f in marked if f not in plain]
        print(f"{code}: {len(plain)} pages, {n} texts, {spans} clickable spots" + (f", {len(bad)} pages DIFFER: {bad[:3]}" if bad else ", identical without markers"))
        ok &= not bad
        for f in _files():   # markers must never survive into a finished page
            if re.search("[-]", strip(page(f))): print("  leftover marker in", f); ok = False
    return ok

def _read(rel):
    w = _state["work"] / "course"; f = w / "site" / rel
    return (f if f.exists() else w / rel).read_text(encoding="utf-8")

if __name__ == "__main__" and "--test" in sys.argv:
    sys.exit(0 if _test() else 1)
