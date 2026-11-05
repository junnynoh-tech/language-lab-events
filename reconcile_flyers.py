"""Keep flyer references pointing at whatever image actually exists, whatever its type.

Run by publish.sh after the flyers are copied into current/. For every flyer base name (gvl-3, dah-1, ...):
  * If current/ holds the same base in more than one type (e.g. gvl-3.jpg from labs/flyers-*/ and a gvl-3.png
    uploaded straight to GitHub), the NEWEST file wins. The others are removed from current/ and moved out of
    labs/flyers-*/ into labs/_superseded/flyers-<date>/, and the winner is copied back into that flyers folder,
    so the next publish doesn't bring the old one back.
  * HEIC/HEIF/TIFF/BMP can't be shown by most browsers: they're converted to .jpg when Pillow can read them,
    otherwise publishing stops and says to run the file through the Event Generator (which converts anything).
  * Every reference to that base in events.json and class-pages/classes/*.json (bare "gvl-3.jpg" or a full
    .../current/gvl-3.jpg URL) is rewritten to the winning file name.
"""
import datetime, re, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABS = HERE.parent
CUR = HERE / "current"
WEB = [".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif", ".pdf"]
CONVERT = [".heic", ".heif", ".tif", ".tiff", ".bmp"]
FLYER = re.compile(r"^[a-z]{2,4}-\d+$")          # event codes: gvl-3, dah-12 ...
REFS = [LABS / "lab-assistant-training-d2l/lab-hub/events/current/events.json", CUR / "events.json",
        *sorted((LABS / "class-pages/classes").glob("*.json"))]
FLYER_DIRS = sorted(LABS.glob("flyers-*"))


def convert(p: Path) -> Path:
    try:
        from PIL import Image
        try:
            import pillow_heif; pillow_heif.register_heif_opener()
        except ImportError:
            pass
        out = p.with_suffix(".jpg")
        Image.open(p).convert("RGB").save(out, "JPEG", quality=88)
        shutil.copystat(p, out); p.unlink()
        print(f"converted {p.name} -> {out.name}")
        return out
    except Exception:
        sys.exit(f"{p.name}: browsers can't show this type and it couldn't be converted here. "
                 f"Drop it into the Event Generator (it converts any photo/PDF) and export again.")


def main():
    files = {}
    for p in CUR.iterdir():
        ext = p.suffix.lower()
        if p.is_file() and FLYER.match(p.stem) and ext in WEB + CONVERT:
            if ext in CONVERT:
                p = convert(p)
            files.setdefault(p.stem, []).append(p)
    stamp = datetime.date.today().isoformat()
    for base, ps in files.items():
        ps.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        win, losers = ps[0], ps[1:]
        for old in losers:
            print(f"{base}: using {win.name}, dropping older {old.name}")
            old.unlink()
            for d in FLYER_DIRS:
                src = d / old.name
                if src.exists():
                    keep = LABS / "_superseded" / f"flyers-{stamp}"; keep.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), keep / old.name)
                    shutil.copy2(win, d / win.name)
        pat = re.compile(r"(?<![\w-])" + re.escape(base) + r"\.(?:jpe?g|png|webp|avif|gif|pdf|heic|heif|tiff?|bmp)\b", re.I)
        for ref in REFS:
            if not ref.exists():
                continue
            s = ref.read_text(encoding="utf-8")
            s2 = pat.sub(win.name, s)
            if s2 != s:
                ref.write_text(s2, encoding="utf-8")
                print(f"{ref.relative_to(LABS)}: {base} -> {win.name}")


if __name__ == "__main__":
    main()
