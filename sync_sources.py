"""Two-way sync between the website editor (Pages CMS, edits land on GitHub) and the local sources.

Run by publish.sh right after `git pull`, before the local copies are pushed out:
    python3 sync_sources.py          # decide, copy GitHub edits back, or stop on a clash
    python3 sync_sources.py --mark   # after a successful push: remember what was published

For each pair (events.json, themes.json) it compares both sides with what was published last time
(labs/.events-sync-state.json, kept out of the public repo):
  * only GitHub changed  -> copy GitHub's file over the local source (the edit made on the website wins)
  * only local changed   -> nothing here; publish.sh pushes the local file as before
  * both changed         -> stop and say so. Re-run with KEEP=github or KEEP=local to choose.
Files are compared by content (parsed JSON), so spacing differences don't count as edits.
"""
import hashlib, json, os, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABS = HERE.parent
HUB = LABS / "lab-assistant-training-d2l/lab-hub/events/current"
STATE = LABS / ".events-sync-state.json"
PAIRS = {  # name: (local source, GitHub copy)
    "events.json": (HUB / "events.json", HERE / "current/events.json"),
    "themes.json": (LABS / "class-pages/themes.json", HERE / "current/themes.json"),
}


def digest(p):
    if not p.exists():
        return None
    return hashlib.sha256(json.dumps(json.loads(p.read_text(encoding="utf-8")), sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    if "--mark" in sys.argv:
        STATE.write_text(json.dumps({n: digest(g) for n, (_, g) in PAIRS.items()}, indent=2) + "\n")
        return
    keep = os.environ.get("KEEP", "").lower()
    for name, (local, gh) in PAIRS.items():
        l, g, last = digest(local), digest(gh), state.get(name)
        if l == g or g is None:
            continue
        gh_changed, local_changed = g != last, l != last
        if last is None:  # first run: no record yet; treat GitHub as the newer side only if told
            gh_changed, local_changed = keep == "github", keep != "github"
        if gh_changed and local_changed and keep not in ("github", "local"):
            sys.exit(f"{name} was changed on the website AND on this computer since the last publish.\n"
                     f"  Keep the website version:  KEEP=github bash publish.sh\n"
                     f"  Keep this computer's:      KEEP=local bash publish.sh\n"
                     f"(Or open both and copy the changes you want into one, then publish.)")
        if (gh_changed and not local_changed) or keep == "github":
            shutil.copy2(gh, local)
            print(f"{name}: took the website's edits -> {local.relative_to(LABS)}")


if __name__ == "__main__":
    main()
