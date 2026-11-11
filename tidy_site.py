"""Tidy the events site after any edit (run on GitHub after every save, and by publish.sh).

    python3 tidy_site.py            # fix codes + flyers in ./current
    python3 tidy_site.py --check    # say what would change, change nothing

1. Event codes: per campus, by date and start time, the earliest event is gvl-1 (event_library.codes()). Codes are
   locked in the website editor; this writes them. Delete an event and the later ones move up.
2. Flyers: whatever was uploaded (JPG, PNG, HEIC, PDF, GIF, AVIF, WebP...) becomes one web image, current/flyers/<code>.webp
   (at most 1600 px wide), and the flyer's entry in the Flyers tab is pointed at it. When an event's code changes, its
   flyer file is renamed with it. The old upload is removed.
   HEIC needs pillow-heif and PDF needs pypdfium2 (installed on GitHub). Without them the file is only renamed.
"""
import io, json, os, re, sys, unicodedata
from pathlib import Path
from event_library import Library, clean, codes

HERE = Path(__file__).resolve().parent
CUR = Path(os.environ.get("EVENTS_CURRENT") or HERE / "current")  # a test copy can be pointed at instead
MAXW, QUALITY = 1600, 88


def dump(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def to_webp(data: bytes, name: str):
    """Bytes of any flyer -> WebP bytes, or None if this machine can't read that type."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    try:
        if name.lower().endswith(".pdf") or data[:5] == b"%PDF-":
            import pypdfium2 as pdfium
            page = pdfium.PdfDocument(data)[0]
            im = page.render(scale=MAXW / page.get_width()).to_pil()
        else:
            im = Image.open(io.BytesIO(data))
            im.seek(0)  # first frame of a GIF
            from PIL import ImageOps
            im = ImageOps.exif_transpose(im)  # phone photos keep their way up
        alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
        im = im.convert("RGBA" if alpha else "RGB")
        if im.width > MAXW:
            im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
        out = io.BytesIO()
        im.save(out, "WEBP", quality=QUALITY, method=6)
        return out.getvalue()
    except Exception as x:  # unreadable here (e.g. HEIC without pillow-heif): keep the file, just rename it
        print(f"  could not convert {name} ({type(x).__name__}); renaming only")
        return None


def main(check=False):
    ev_path = CUR / "events.json"
    raw = ev_path.read_text(encoding="utf-8")
    doc = json.loads(raw)
    before = {id(e): e.get("key") for e in doc.get("events") or []}
    ids = {id(e): e.get("id") for e in doc.get("events") or []}
    codes(doc)
    seen = set()
    for e in doc.get("events") or []:  # a new event gets its web address name once, from its date and name (same as the pages); ids stay unique
        if not e.get("id"):
            slug = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFD", (e.get("title") or "").lower()).encode("ascii", "ignore").decode()).strip("-")
            e["id"] = "-".join(x for x in (e.get("date"), slug) if x)
        base, i = e["id"], 2
        while e["id"] in seen:
            e["id"], i = f"{base}-{i}", i + 1
        seen.add(e["id"])
    changes = [f"code {before[id(e)] or '(none)'} -> {e['key']}: {e.get('title')}" for e in doc["events"] if before[id(e)] != e["key"]]
    changes += [f"new event: id {e['id']}" for e in doc["events"] if e["id"] != ids[id(e)]]

    plans = []  # (entry file, entry, source path, target path, bytes)
    taken = set()
    if doc.get("library"):
        lib = Library(CUR)
        for e in sorted(doc["events"], key=lambda e: (e["key"].rsplit("-", 1)[0], int(e["key"].rsplit("-", 1)[1]))):  # gvl-2 before gvl-10
            pick = str(e.get("flyer_pick") or "").split("/")[-1]
            if not pick or pick in taken:
                continue
            taken.add(pick if pick.endswith(".json") else pick + ".json")
            entry_file = lib.root / "flyers" / (pick if pick.endswith(".json") else pick + ".json")
            entry = lib.get("flyers", pick)
            if not entry or not entry.get("image"):
                continue
            src = CUR / clean(entry["image"])
            if not src.is_file():
                print(f"  flyer missing for {e['key']}: {entry['image']}")
                continue
            data = src.read_bytes()
            target = f"flyers/{e['key']}.webp"
            if clean(entry["image"]) == target:
                continue
            webp = data if src.suffix.lower() == ".webp" else to_webp(data, src.name)
            if webp is None:
                target = f"flyers/{e['key']}{src.suffix.lower()}"
                webp = data
                if clean(entry["image"]) == target:
                    continue
            plans.append((entry_file, entry, src, target, webp))
            changes.append(f"flyer {clean(entry['image'])} -> {target}")

    # a flyer no event picks any more, sitting where a moved one will land: step it aside under its own name
    if plans:
        targets = {t for *_, t, _ in plans}
        for entry_file in sorted((CUR / "library" / "flyers").glob("*.json")):
            if entry_file.name in taken:
                continue
            entry = json.loads(entry_file.read_text(encoding="utf-8"))
            src = CUR / clean(entry.get("image") or "")
            if clean(entry.get("image") or "") not in targets or not src.is_file():
                continue
            stem = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFD", (entry.get("title") or entry_file.stem).lower()).encode("ascii", "ignore").decode()).strip("-") or "flyer"
            target, i = f"flyers/{stem}{src.suffix.lower()}", 2
            while (CUR / target).exists() or target in targets:
                target, i = f"flyers/{stem}-{i}{src.suffix.lower()}", i + 1
            targets.add(target)
            plans.append((entry_file, entry, src, target, src.read_bytes()))
            changes.append(f"unused flyer {clean(entry['image'])} -> {target}")
    if check or not changes:
        print("\n".join(changes) or "Nothing to tidy.")
        return bool(changes)
    # all sources were read into memory first, so swapping two codes can't overwrite a flyer
    targets = {CUR / t for *_, t, _ in plans}
    for _, _, src, _, _ in plans:
        if src not in targets and src.exists():
            src.unlink()
    (CUR / "flyers").mkdir(exist_ok=True)
    for entry_file, entry, _, target, data in plans:
        (CUR / target).write_bytes(data)
        entry["image"] = target
        entry_file.write_text(dump(entry), encoding="utf-8")
    ev_path.write_text(dump(doc), encoding="utf-8")
    print("\n".join(changes))
    return True


if __name__ == "__main__":
    main("--check" in sys.argv)
