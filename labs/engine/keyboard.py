"""Spanish keyboard helper: setup steps for Windows and Mac, a keyboard diagram, and typing
practice. Used by the LAB folder description ("Quizzes & accents" tab) and by the standalone
keyboard tutorial page. Windows instructions use the Latin American keyboard, which Windows adds
with Español (México)."""
import html

def e(s): return html.escape(s, quote=True)

# Windows, Latin American layout. (key id, label on a US keyboard, Spanish output, Shift output)
WIN_ROWS = [
    [("grave", "`", "", ""), ("1", "1", "1", "!"), ("2", "2", "2", '"'), ("3", "3", "3", "#"), ("4", "4", "4", "$"), ("5", "5", "5", "%"),
     ("6", "6", "6", "&"), ("7", "7", "7", "/"), ("8", "8", "8", "("), ("9", "9", "9", ")"), ("0", "0", "0", "="),
     ("minus", "-", "'", "?"), ("equal", "=", "¿", "¡"), ("bksp", "Backspace", "⌫", "")],
    [("tab", "Tab", "Tab", "")] + [(c, c.upper(), c, "") for c in "qwertyuiop"] +
    [("bracketL", "[", "´", "¨"), ("bracketR", "]", "", ""), ("bslash", "\\", "", "")],
    [("caps", "Caps", "Caps", "")] + [(c, c.upper(), c, "") for c in "asdfghjkl"] +
    [("semicolon", ";", "ñ", "Ñ"), ("quote", "'", "", ""), ("enter", "Enter", "Enter", "")],
    [("shiftL", "Shift", "Shift", "")] + [(c, c.upper(), c, "") for c in "zxcvbnm"] +
    [("comma", ",", ",", ";"), ("period", ".", ".", ":"), ("slash", "/", "-", "_"), ("shiftR", "Shift", "Shift", "")],
    [("ctrl", "Ctrl", "Ctrl", ""), ("win", "Win", "Win", ""), ("alt", "Alt", "Alt", ""), ("space", "Space", "", ""), ("altgr", "Alt Gr", "Alt Gr", ""), ("ctrlR", "Ctrl", "Ctrl", "")],
]
WIN_MOVED = {"minus", "equal", "bracketL", "semicolon", "slash", "comma", "period", "2"}

# Mac, U.S. layout (no setup). Option combos shown on the keys that make Spanish characters.
MAC_ROWS = [
    [("grave", "`", "`", "~")] + [(str(i), str(i), str(i), s) for i, s in zip(range(1, 10), "!@#$%^&*(")] +
    [("0", "0", "0", ")"), ("minus", "-", "-", "_"), ("equal", "=", "=", "+"), ("bksp", "delete", "⌫", "")],
    [("tab", "tab", "tab", "")] + [(c, c.upper(), c, "") for c in "qwertyuiop"] + [("bracketL", "[", "[", "{"), ("bracketR", "]", "]", "}"), ("bslash", "\\", "\\", "|")],
    [("caps", "caps", "caps", "")] + [(c, c.upper(), c, "") for c in "asdfghjkl"] + [("semicolon", ";", ";", ":"), ("quote", "'", "'", '"'), ("enter", "return", "return", "")],
    [("shiftL", "shift", "shift", "")] + [(c, c.upper(), c, "") for c in "zxcvbnm"] + [("comma", ",", ",", "<"), ("period", ".", ".", ">"), ("slash", "/", "/", "?"), ("shiftR", "shift", "shift", "")],
    [("fn", "fn", "fn", ""), ("ctrl", "control", "control", ""), ("optL", "option", "option ⌥", ""), ("cmd", "command", "⌘", ""), ("space", "space", "", ""), ("cmdR", "command", "⌘", ""), ("optR", "option", "option ⌥", "")],
]
MAC_OPT = {"e": "´", "n": "˜", "u": "¨", "1": "¡", "slash": "¿"}

WIN_TABLE = [
    ("á é í ó ú", "Press <kbd>´</kbd> (the key right of P), then the vowel."),
    ("Á É Í Ó Ú", "Press <kbd>´</kbd>, then <kbd>Shift</kbd> + the vowel."),
    ("ü", "Press <kbd>Shift</kbd> + <kbd>´</kbd>, then <kbd>u</kbd>."),
    ("ñ / Ñ", "The key right of L (where ; is). Add <kbd>Shift</kbd> for Ñ."),
    ("¿", "The key two to the right of 0 (where = is)."),
    ("¡", "<kbd>Shift</kbd> + that same key."),
    ("?", "<kbd>Shift</kbd> + the key right of 0 (where - is)."),
    ("! &nbsp; \"", "<kbd>Shift</kbd> + <kbd>1</kbd> &nbsp;·&nbsp; <kbd>Shift</kbd> + <kbd>2</kbd>"),
    ("- &nbsp; ; &nbsp; :", "The key where / is &nbsp;·&nbsp; <kbd>Shift</kbd> + <kbd>,</kbd> &nbsp;·&nbsp; <kbd>Shift</kbd> + <kbd>.</kbd>"),
]
MAC_TABLE = [
    ("á é í ó ú", "Press <kbd>Option</kbd> + <kbd>e</kbd>, let go, then the vowel."),
    ("Á É Í Ó Ú", "<kbd>Option</kbd> + <kbd>e</kbd>, then <kbd>Shift</kbd> + the vowel."),
    ("ñ / Ñ", "<kbd>Option</kbd> + <kbd>n</kbd>, then <kbd>n</kbd> (or <kbd>Shift</kbd> + <kbd>n</kbd>)."),
    ("ü", "<kbd>Option</kbd> + <kbd>u</kbd>, then <kbd>u</kbd>."),
    ("¿", "<kbd>Option</kbd> + <kbd>Shift</kbd> + <kbd>?</kbd>"),
    ("¡", "<kbd>Option</kbd> + <kbd>1</kbd>"),
    ("Any accent", "Or press and hold the letter, then pick the number of the accent you want."),
]

PRACTICE = ["¿Cómo te llamas?", "¡Mucho gusto!", "Soy de México.", "Estudio español.", "¿Qué hora es?",
            "Él es mi compañero.", "¿Dónde está la biblioteca?", "Hay dieciséis estudiantes.",
            "Mi papá es muy simpático.", "¡Adiós! Nos vemos mañana."]

CSS = """
.os-switch{display:inline-flex;border:1.5px solid var(--navy);border-radius:999px;overflow:hidden;margin:0 0 14px;}
.os-switch button{font:inherit;font-weight:700;padding:8px 22px;min-height:44px;border:none;background:var(--white);color:var(--navy);cursor:pointer;}
.os-switch button[aria-pressed="true"]{background:var(--navy);color:#fff;}
.kb{display:flex;flex-direction:column;gap:4px;background:#e9eef5;border:1px solid var(--line-2);border-radius:12px;padding:10px;margin:8px 0 6px;max-width:760px;overflow-x:auto;}
.kb-row{display:flex;gap:4px;}
.key{flex:1 0 40px;min-width:42px;height:54px;border-radius:6px;background:#fff;border:1px solid #b9c6d6;box-shadow:0 1px 0 #9fb3cc;position:relative;font-size:15px;line-height:1;color:var(--ink);}
.key .o{position:absolute;left:7px;bottom:7px;font-weight:700;font-size:17px;}
.key .s{position:absolute;left:7px;top:5px;font-size:14px;color:var(--muted);}
.key .us{position:absolute;right:5px;bottom:6px;font-size:14px;color:#5b6b7f;}
.key.w15{flex-basis:62px;} .key.w2{flex-basis:80px;} .key.w25{flex-basis:96px;} .key.sp{flex:6 0 200px;}
.key.mod .o{font-size:14px;font-weight:600;color:var(--muted);}
.key.moved{background:var(--gold-lt);border-color:var(--gold);}
.key.blank{background:#f3f5f8;}
.key.hl{background:var(--navy);border-color:var(--navy);}
.key.hl .o,.key.hl .s,.key.hl .us{color:#fff;}
.kb-legend{font-size:.92rem;color:var(--muted);margin:0 0 10px;}
.kb-legend span{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:-2px;margin:0 4px 0 10px;}
kbd{font:600 .9em 'DM Sans',Arial,sans-serif;background:var(--white);border:1px solid var(--line-2);border-bottom-width:2px;border-radius:5px;padding:1px 6px;white-space:nowrap;}
.practice{background:var(--white);border:1.5px solid var(--navy);border-radius:12px;padding:14px 18px;margin:10px 0;}
.practice .target{font-family:'Fraunces',Georgia,serif;font-size:1.5rem;font-weight:700;color:var(--navy);margin:2px 0 8px;}
.practice input{width:100%;max-width:520px;font:inherit;font-size:1.15rem;padding:9px 12px;border:1.5px solid var(--line-2);border-radius:8px;min-height:48px;}
.practice input:focus-visible{outline:3px solid var(--gold);outline-offset:1px;}
.practice .fb{min-height:52px;margin:8px 0;font-weight:600;}
.practice .fb.ok{color:var(--green);} .practice .fb.hint{color:var(--navy);}
.practice .row{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
.practice .count{color:var(--muted);font-size:.92rem;}
@media print{.practice,.os-switch{display:none!important;}}
"""

def _kb(rows, os_name, moved=frozenset(), opt=None):
    wide = {"bksp": "w2", "tab": "w15", "bslash": "w15", "caps": "w2", "enter": "w2", "shiftL": "w25", "shiftR": "w25",
            "ctrl": "w15", "ctrlR": "w15", "alt": "w15", "altgr": "w15", "win": "w15", "fn": "", "cmd": "w15", "cmdR": "w15",
            "optL": "w15", "optR": "w15", "space": "sp"}
    out = []
    for row in rows:
        keys = []
        for kid, us, o, s in row:
            cls = ["key", wide.get(kid, "")]
            is_mod = len(us) > 1 and kid not in ("bksp",)
            if is_mod: cls.append("mod")
            if kid in moved: cls.append("moved")
            if not o and kid != "space": cls.append("blank")
            inner = f'<span class="o">{e(o)}</span>' if o else ""
            if s: inner += f'<span class="s">{e(s)}</span>'
            if opt and kid in opt:
                cls.append("moved"); inner += f'<span class="us">⌥ {e(opt[kid])}</span>'
            elif kid in moved and len(us) == 1 and us != o:
                inner += f'<span class="us">{e(us)}</span>'
            keys.append(f'<span class="{" ".join(c for c in cls if c)}" data-k="{kid}">{inner}</span>')
        out.append('<div class="kb-row">' + "".join(keys) + "</div>")
    label = ("Windows Latin American keyboard. Keys that change: ´ is right of P, ñ is right of L, ¿ and ¡ are two keys right of 0, "
             "' and ? are right of 0, and - is where / is." if os_name == "win" else
             "Mac keyboard. Option plus e, n, u, 1, or Shift and question mark make the Spanish characters.")
    return f'<div class="kb" role="img" aria-label="{e(label)}" data-os="{os_name}">' + "".join(out) + "</div>"

def _table(rows, cap):
    trs = "".join(f'<tr><td lang="es">{c}</td><td>{h}</td></tr>' for c, h in rows)
    return f'<table class="kbtable"><caption class="sr">{cap}</caption><thead><tr><th scope="col">To type</th><th scope="col">Press</th></tr></thead><tbody>{trs}</tbody></table>'

def section(p="kb", heading_level=3, practice=True):
    """The OS switch, setup, diagram, key table and (optionally) practice. p = id prefix."""
    h = f"h{heading_level}"
    win = f"""<div id="{p}-win" data-os-panel="win">
<{h}>Set up the Spanish keyboard (one time)</{h}>
<ol class="steps">
<li>Open <b>Start › Settings › Time &amp; language › Language &amp; region</b>. (Windows 10: <b>Settings › Time &amp; Language › Language</b>.)</li>
<li>Next to <b>Preferred languages</b>, click <b>Add a language</b>.</li>
<li>Search for <b lang="es">Español (México)</b>, select it, and click <b>Next</b>.</li>
<li><b>Uncheck</b> “Set as my Windows display language,” then click <b>Install</b>. Windows adds the <b>Latin American</b> keyboard.</li>
</ol>
<{h}>Switch keyboards</{h}>
<p>Press <kbd>Windows</kbd> + <kbd>Space</kbd>, or click <b>ENG</b> on the taskbar and choose <b>ESP</b>. Switch back to ENG for English.</p>
<{h}>Where the keys are</{h}>
{_kb(WIN_ROWS, "win", WIN_MOVED)}
<p class="kb-legend"><span style="background:var(--gold-lt);border:1px solid var(--gold)"></span>Keys that type something different with the Spanish keyboard. The small gray mark is what's printed on your key.</p>
{_table(WIN_TABLE, 'Spanish characters on Windows')}
</div>"""
    mac = f"""<div id="{p}-mac" data-os-panel="mac" hidden>
<{h}>No setup needed</{h}>
<p>Your Mac's regular keyboard can type every Spanish character with the <kbd>Option</kbd> key.</p>
<{h}>Where the keys are</{h}>
{_kb(MAC_ROWS, "mac", opt=MAC_OPT)}
<p class="kb-legend"><span style="background:var(--gold-lt);border:1px solid var(--gold)"></span>Keys you use with <kbd>Option</kbd>.</p>
{_table(MAC_TABLE, 'Spanish characters on a Mac')}
</div>"""
    prac = ""
    if practice:
        prac = f"""<{h}>Practice</{h}>
<div class="practice" id="{p}-practice">
<p class="count" id="{p}-count"></p>
<p class="target" lang="es" id="{p}-target"></p>
<label for="{p}-input">Type the sentence exactly, with accents and punctuation:</label>
<input id="{p}-input" type="text" lang="es" autocomplete="off" autocapitalize="off" spellcheck="false">
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

JS = r"""
(function(){
var HINT={
 win:{'á':['´ then a',['bracketL','a']],'é':['´ then e',['bracketL','e']],'í':['´ then i',['bracketL','i']],'ó':['´ then o',['bracketL','o']],'ú':['´ then u',['bracketL','u']],
  'Á':['´ then Shift + A',['bracketL','shiftL','a']],'É':['´ then Shift + E',['bracketL','shiftL','e']],'Í':['´ then Shift + I',['bracketL','shiftL','i']],'Ó':['´ then Shift + O',['bracketL','shiftL','o']],'Ú':['´ then Shift + U',['bracketL','shiftL','u']],
  'ü':['Shift + ´, then u',['shiftL','bracketL','u']],'ñ':['the ñ key (right of L)',['semicolon']],'Ñ':['Shift + ñ',['shiftL','semicolon']],
  '¿':['the ¿ key (two right of 0)',['equal']],'¡':['Shift + the ¿ key',['shiftL','equal']],'?':['Shift + the key right of 0',['shiftL','minus']],
  '!':['Shift + 1',['shiftL','1']],'"':['Shift + 2',['shiftL','2']],"'":['the key right of 0',['minus']],'-':['the key where / is',['slash']],
  ';':['Shift + comma',['shiftL','comma']],':':['Shift + period',['shiftL','period']]},
 mac:{'á':['Option + e, then a',['optL','e','a']],'é':['Option + e, then e',['optL','e']],'í':['Option + e, then i',['optL','e','i']],'ó':['Option + e, then o',['optL','e','o']],'ú':['Option + e, then u',['optL','e','u']],
  'Á':['Option + e, then Shift + A',['optL','e','shiftL','a']],'É':['Option + e, then Shift + E',['optL','e','shiftL']],'Í':['Option + e, then Shift + I',['optL','e','shiftL','i']],'Ó':['Option + e, then Shift + O',['optL','e','shiftL','o']],'Ú':['Option + e, then Shift + U',['optL','e','shiftL','u']],
  'ñ':['Option + n, then n',['optL','n']],'Ñ':['Option + n, then Shift + N',['optL','n','shiftL']],'ü':['Option + u, then u',['optL','u']],
  '¿':['Option + Shift + ?',['optL','shiftL','slash']],'¡':['Option + 1',['optL','1']]}
};
var PRACTICE=__PRACTICE__;
document.querySelectorAll('.kbwrap').forEach(function(w){
  var p=w.getAttribute('data-kb'), os='win';
  try{ if(/Mac|iPhone|iPad/.test(navigator.platform||navigator.userAgent)) os='mac'; var s=localStorage.getItem('kb-os'); if(s) os=s; }catch(e){}
  var btns=w.querySelectorAll('.os-switch button');
  function hl(keys){ w.querySelectorAll('.key.hl').forEach(function(k){k.classList.remove('hl');});
    (keys||[]).forEach(function(id){ var k=w.querySelector('[data-os-panel="'+os+'"] .key[data-k="'+id+'"]'); if(k) k.classList.add('hl'); }); }
  function setOS(o){ os=o; btns.forEach(function(b){b.setAttribute('aria-pressed', b.getAttribute('data-os')===o);});
    w.querySelectorAll('[data-os-panel]').forEach(function(d){d.hidden=d.getAttribute('data-os-panel')!==o;});
    try{localStorage.setItem('kb-os',o);}catch(e){} check(); }
  btns.forEach(function(b){b.addEventListener('click',function(){setOS(b.getAttribute('data-os'));});});
  var inp=document.getElementById(p+'-input'); if(!inp){ setOS(os); return; }
  var tgt=document.getElementById(p+'-target'), fb=document.getElementById(p+'-fb'), cnt=document.getElementById(p+'-count'), nx=document.getElementById(p+'-next'), i=0;
  function load(){ tgt.textContent=PRACTICE[i]; cnt.textContent='Sentence '+(i+1)+' of '+PRACTICE.length; inp.value=''; fb.textContent=''; fb.className='fb'; hl([]); check(); }
  function check(){
    if(!inp) return; var t=PRACTICE[i], v=inp.value.normalize('NFC'), k=0;
    while(k<v.length && k<t.length && v[k]===t[k]) k++;
    if(v===t){ fb.textContent='¡Perfecto! That matches exactly.'; fb.className='fb ok'; hl([]); return; }
    var want = k<t.length ? t[k] : null, h = want && HINT[os][want];
    if(k<v.length){ fb.className='fb hint'; fb.textContent='Check character '+(k+1)+': it should be “'+(want||'(nothing)')+'”.'+(h?' To type it: '+h[0]+'.':''); hl(h?h[1]:[]); return; }
    if(h){ fb.className='fb hint'; fb.textContent='Next: “'+want+'”. '+h[0]+'.'; hl(h[1]); } else { fb.textContent=''; fb.className='fb'; hl([]); }
  }
  inp.addEventListener('input',check);
  nx.addEventListener('click',function(){ i=(i+1)%PRACTICE.length; load(); inp.focus(); });
  setOS(os); load();
});
})();
"""

def js():
    import json
    return JS.replace("__PRACTICE__", json.dumps(PRACTICE, ensure_ascii=False))

QUICK = """<details class="box kbquick"><summary><b>How do I type accents?</b></summary>
<p><b>Windows</b> (Spanish keyboard on, ESP in the taskbar): <kbd>´</kbd> (right of P), then the vowel. ñ is right of L. ¿ is two keys right of 0.</p>
<p><b>Mac:</b> <kbd>Option</kbd> + <kbd>e</kbd>, then the vowel. <kbd>Option</kbd> + <kbd>n</kbd>, then n for ñ. <kbd>Option</kbd> + <kbd>Shift</kbd> + <kbd>?</kbd> for ¿.</p>
<p>No Spanish keyboard yet? Use the <b>Accents</b> tab on the right edge of this page to copy and paste.</p>
</details>"""
