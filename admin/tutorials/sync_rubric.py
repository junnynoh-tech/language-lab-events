"""Copy the speaking rubric from the Lab's one policy source into the grading tutorial.

    python3 labs/lab-assistant-training-d2l/tutorials/sync_rubric.py

labs/lab-builder/policy.json is the source (rubric rows, the Nothing-to-rate rule, the caps). Run this after any
rubric change so the tutorial never drifts from the Bongo instructions and the LA guide.
"""
import html, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
policy = json.loads((HERE.parents[2] / "lab-builder" / "policy.json").read_text(encoding="utf-8"))
r = policy["rubric"]
md = lambda s: html.unescape(re.sub(r"</?b>", "**", s))

f = HERE / "t" / "grading.json"
t = json.loads(f.read_text(encoding="utf-8"))
t["rubric"] = {"total": r["total"], "levels": r["levels"], "rows": [{"name": x["name"], "points": x["points"], "d": x["d"]} for x in r["rows"]]}
for s in t["sections"]:
    if s["id"] == "zero": s["text"] = md(r["zero"])
    if s["id"] == "caps": s["list"] = [md(n) for n in r["notes"]]
f.write_text(json.dumps(t, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("grading.json rubric synced:", ", ".join(f"{x['name']} {x['points'][0]}" for x in r["rows"]))
