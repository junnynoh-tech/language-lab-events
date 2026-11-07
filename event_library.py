"""The event library: events PICK things that are made in their own website-editor tabs (2026-11-07).

    current/events.json                      events: date, place, summary + picks
    current/library/flyers/<name>.json       a flyer: image + description           (event: flyer_pick)
    current/library/music/<name>.json        one ambient track + credit              (event: music_pick, a list)
    current/library/forms/<name>.json        a sign-up / entry form link             (event: signup {on, form, deadline, deadline_time})
    current/library/extra-credit/<name>.json what students are told about credit     (event: credit {on, option})
    current/library/assignments/<name>.json  a mini-project or assignment            (event: assignment {on, pick, due, due_time})
    current/library/competitions/<name>.json prizes, rules, rubric, how it works     (event: competition {on, pick})

resolve() fills each event's older fields (flyer, music, entry, extra_credit, mini_project, link, prizes, rules, rubric,
activities) from its picks, so everything that reads events.json keeps working. The student pages do the same in the
browser (resolveLibrary() in visual/event-carousel.html and event-details.html); keep the two in step.

Event codes: per campus, all events in the file by date and start time, the earliest is <campus>-1 (codes()).
"""
import json
from pathlib import Path

EC_NOTE = "Extra credit is up to each instructor. Ask yours whether this event counts in your course."
KINDS = ("flyers", "music", "forms", "extra-credit", "assignments", "competitions")
LEGACY = ("flyer", "flyer_alt", "music", "entry", "extra_credit", "mini_project", "link",
          "prizes", "prizes_note", "rules", "rubric", "activities")


def codes(doc):
    """Give every event its code: per campus, by date then start time (then name); the earliest is gvl-1."""
    count = {}
    for e in sorted(doc.get("events") or [], key=lambda e: (e.get("date") or "", e.get("start") or "", e.get("title") or "")):
        c = e.get("campus") or "gvl"
        count[c] = count.get(c, 0) + 1
        e["key"] = f"{c}-{count[c]}"
    return doc


def clean(path):
    """Uploads can come back as '/current/x.png' or 'current/prizes/x.jpg'; keep the part after current/."""
    if not isinstance(path, str):
        return path
    p = path.strip()
    if "current/" in p:
        p = p.split("current/", 1)[1]
    return p.lstrip("/")


class Library:
    def __init__(self, current: Path):
        self.root = Path(current) / "library"
        self.cache = {}

    def get(self, kind, name):
        name = str(name or "").strip().split("/")[-1]
        if not name:
            return None
        if not name.endswith(".json"):
            name += ".json"
        k = f"{kind}/{name}"
        if k not in self.cache:
            p = self.root / kind / name
            try:
                self.cache[k] = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self.cache[k] = None
        return self.cache[k]

    def all(self, kind):
        d = self.root / kind
        return {p.name: json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))} if d.is_dir() else {}


def on(o):
    return isinstance(o, dict) and o.get("on") is True


def resolve_event(e, lib):
    """Fill the event's older fields from its picks (same rules as resolveLibrary() in the student pages)."""
    S, C, A, K = (e.get(k) or {} for k in ("signup", "credit", "assignment", "competition"))
    fly = lib.get("flyers", e.get("flyer_pick"))
    form = lib.get("forms", S.get("form")) if on(S) else None
    ec = lib.get("extra-credit", C.get("option")) if on(C) else None
    task = lib.get("assignments", A.get("pick")) if on(A) else None
    comp = lib.get("competitions", K.get("pick")) if on(K) else None
    music = [m for m in (lib.get("music", n) for n in (e.get("music_pick") or [])) if m]
    e["flyer"] = clean((fly or {}).get("image") or "")
    e["flyer_alt"] = (fly or {}).get("alt") or ""
    e["music"] = [{**m, "file": clean(m.get("file") or "")} for m in music]
    e["entry"] = {"url": form["url"], "label": form.get("label") or "Sign up",
                  "deadline": S.get("deadline") or "", "deadline_time": S.get("deadline_time") or ""} if form and form.get("url") else None
    e["extra_credit"] = {"offered": on(C), "note": ((ec or {}).get("note") or EC_NOTE) if on(C) else ""}
    e["mini_project"] = {**{k: task.get(k) for k in ("kind", "title", "title_es", "steps", "step_titles", "deliverable", "submit") if task.get(k)},
                         "due": A.get("due") or "", "due_time": A.get("due_time") or ""} if task else None
    link = (task or {}).get("link") or {}
    e["link"] = {"label": link.get("label") or "Open", "url": link["url"]} if link.get("url") else None
    comp = comp or {}
    e["prizes"] = [{**p, "image": clean(p.get("image") or "")} for p in comp.get("prizes") or []]
    e["prizes_note"] = comp.get("prizes_note") or ""
    e["rules"] = comp.get("rules") or []
    e["rubric"] = clean(comp.get("rubric") or "")
    e["activities"] = [{"title": comp.get("title") or "", "text": comp["how"]}] if comp.get("how") else []
    return e


def resolve(doc, current: Path):
    """events.json with every event's picks filled in. Older inline files (no "library" flag) pass through unchanged."""
    codes(doc)
    if not doc.get("library"):
        return doc
    lib = Library(current)
    for e in doc.get("events") or []:
        resolve_event(e, lib)
    return doc


def load_resolved(events_json: Path):
    p = Path(events_json)
    return resolve(json.loads(p.read_text(encoding="utf-8")), p.parent)
