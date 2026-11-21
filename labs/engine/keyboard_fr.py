"""French accents: setup steps for Windows and Mac, a keyboard diagram, and typing practice.
Same interface as keyboard.py (CSS, section, js). Windows uses the United States-International
keyboard, so letters stay where they are; a Mac needs no setup."""
import json, re
import keyboard as K

e = K.e
CSS = K.CSS + """
.kb[data-os="mac"] .key .us{right:5px;top:4px;bottom:auto;font-size:13px;}
.pcards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:10px 0 0;}
.pcard{display:flex;flex-direction:column;justify-content:center;min-height:64px;padding:10px 14px;background:var(--white);border:1.5px solid var(--line-2);border-radius:10px;text-decoration:none;color:var(--ink);}
.pcard:hover{border-color:var(--navy);color:var(--ink);} .pcard b{color:var(--navy);} .pcard span{font-size:.88rem;color:var(--muted);}
"""
WIN_ROWS = K.MAC_ROWS[:-1] + [K.WIN_ROWS[-1]]
WIN_MOVED = {"quote", "grave", "6"}
MAC_OPT = {"e": "´", "grave": "", "i": "ˆ", "u": "¨", "c": "ç", "q": "œ"}
WIN_TABLE = [
    ("é", "Press <kbd>'</kbd>, then <kbd>e</kbd>."),
    ("à è ù", "Press <kbd>`</kbd> (left of 1), then the vowel."),
    ("â ê î ô û", "Press <kbd>Shift</kbd> + <kbd>6</kbd>, then the vowel."),
    ("ë ï ü", "Press <kbd>Shift</kbd> + <kbd>'</kbd>, then the vowel."),
    ("ç", "Press <kbd>'</kbd>, then <kbd>c</kbd>."),
    ("Ç À É", "Same keys, with <kbd>Shift</kbd> on the letter."),
    ("œ", "Hold <kbd>Right Alt</kbd> and press <kbd>k</kbd>."),
    ("' (apostrophe)", "Press <kbd>'</kbd>, then <kbd>Space</kbd>. Do this in <i lang=\"fr\">l'école</i> and <i lang=\"fr\">j'aime</i>."),
]
MAC_TABLE = [
    ("é", "Press <kbd>Option</kbd> + <kbd>e</kbd>, let go, then <kbd>e</kbd>."),
    ("à è ù", "Press <kbd>Option</kbd> + <kbd>`</kbd>, let go, then the vowel."),
    ("â ê î ô û", "Press <kbd>Option</kbd> + <kbd>i</kbd>, let go, then the vowel."),
    ("ë ï ü", "Press <kbd>Option</kbd> + <kbd>u</kbd>, let go, then the vowel."),
    ("ç", "<kbd>Option</kbd> + <kbd>c</kbd>. Add <kbd>Shift</kbd> for Ç."),
    ("œ", "<kbd>Option</kbd> + <kbd>q</kbd>"),
    ("Any accent", "Or press and hold the letter, then pick the number of the accent you want."),
]
PRACTICE = ["Ça va ?", "Très bien, merci.", "Où est la bibliothèque ?", "À bientôt !", "Ma sœur est très gentille.",
            "Je suis étudiant à l'université.", "Le garçon mange à la cafétéria.", "Il fait très froid en février.",
            "Mon frère préfère le théâtre.", "Nous allons à la fête."]

def section(p="kb", heading_level=3, practice=True):
    h = f"h{heading_level}"
    win = f"""<div id="{p}-win" data-os-panel="win">
<{h}>Add the keyboard (one time)</{h}>
<ol class="steps">
<li>Open <b>Start › Settings › Time &amp; language › Language &amp; region</b>. (Windows 10: <b>Settings › Time &amp; Language › Language</b>.)</li>
<li>Next to <b>English (United States)</b>, choose <b>…</b> and then <b>Language options</b>. (Windows 10: select it and choose <b>Options</b>.)</li>
<li>Under <b>Keyboards</b>, choose <b>Add a keyboard</b>, then <b>United States-International</b>.</li>
</ol>
<{h}>Switch keyboards</{h}>
<p>Press <kbd>Windows</kbd> + <kbd>Space</kbd>, or click <b>ENG</b> on the taskbar and choose <b>INTL</b>. Your letters stay in the same places.</p>
<{h}>Where the keys are</{h}>
{K._kb(WIN_ROWS, "win", WIN_MOVED)}
<p class="kb-legend"><span style="background:var(--gold-lt);border:1px solid var(--gold)"></span>Keys you press first. Nothing appears until you press the letter.</p>
{K._table(WIN_TABLE, "French characters on Windows")}
</div>"""
    mac = f"""<div id="{p}-mac" data-os-panel="mac" hidden>
<{h}>No setup needed</{h}>
<p>Your Mac's regular keyboard can type every French character with the <kbd>Option</kbd> key.</p>
<{h}>Where the keys are</{h}>
{K._kb(K.MAC_ROWS, "mac", opt=MAC_OPT)}
<p class="kb-legend"><span style="background:var(--gold-lt);border:1px solid var(--gold)"></span>Keys you use with <kbd>Option</kbd>.</p>
{K._table(MAC_TABLE, "French characters on a Mac")}
</div>"""
    prac = ""
    if practice:
        prac = f"""<{h}>Practice</{h}>
<div class="practice" id="{p}-practice">
<p class="count" id="{p}-count"></p>
<p class="target" lang="fr" id="{p}-target"></p>
<label for="{p}-input">Type the sentence exactly, with accents and punctuation:</label>
<input id="{p}-input" type="text" lang="fr" autocomplete="off" autocapitalize="off" spellcheck="false">
<p class="fb" id="{p}-fb" aria-live="polite"></p>
<div class="row"><button type="button" class="linkbtn" id="{p}-next">Next sentence</button></div>
</div>"""
    return f"""<div class="kbwrap" data-kb="{p}">
<div class="os-switch" role="group" aria-label="Your computer">
<button type="button" data-os="win" aria-pressed="true">Windows</button><button type="button" data-os="mac" aria-pressed="false">Mac</button>
</div>
<p class="note">On a phone or iPad: press and hold a letter to choose its accent.</p>
{win}
{mac}
{prac}
</div>"""

def _hints():
    w, m = {}, {}
    for v, keys in {"a": "grave", "e": "grave", "u": "grave"}.items():
        ch = {"a": "à", "e": "è", "u": "ù"}[v]
        w[ch] = [f"` then {v}", [keys, v]]; m[ch] = [f"Option + `, then {v}", ["optL", "grave", v]]
    for v, ch in zip("aeiou", "âêîôû"):
        w[ch] = [f"Shift + 6, then {v}", ["shiftL", "6", v]]; m[ch] = [f"Option + i, then {v}", ["optL", "i", v]]
    for v, ch in zip("eiu", "ëïü"):
        w[ch] = [f"Shift + ', then {v}", ["shiftL", "quote", v]]; m[ch] = [f"Option + u, then {v}", ["optL", "u", v]]
    w["é"] = ["' then e", ["quote", "e"]]; m["é"] = ["Option + e, then e", ["optL", "e"]]
    w["É"] = ["' then Shift + E", ["quote", "shiftL", "e"]]; m["É"] = ["Option + e, then Shift + E", ["optL", "e", "shiftL"]]
    w["À"] = ["` then Shift + A", ["grave", "shiftL", "a"]]; m["À"] = ["Option + `, then Shift + A", ["optL", "grave", "shiftL", "a"]]
    w["ç"] = ["' then c", ["quote", "c"]]; m["ç"] = ["Option + c", ["optL", "c"]]
    w["Ç"] = ["' then Shift + C", ["quote", "shiftL", "c"]]; m["Ç"] = ["Option + Shift + C", ["optL", "shiftL", "c"]]
    w["œ"] = ["Right Alt + k", ["altgr", "k"]]; m["œ"] = ["Option + q", ["optL", "q"]]
    w["'"] = ["' then Space", ["quote", "space"]]
    return {"win": w, "mac": m}

def js():
    src = re.sub(r"var HINT=\{.*?\n\};", lambda _: "var HINT=" + json.dumps(_hints(), ensure_ascii=False) + ";", K.JS, flags=re.S)
    return src.replace("¡Perfecto! That matches exactly.", "Parfait ! That matches exactly.").replace("__PRACTICE__", json.dumps(PRACTICE, ensure_ascii=False))
