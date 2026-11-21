"""French look and wording, applied to the finished page text so the Spanish pages stay untouched.
Only courses with "locale": "fr" in their source JSON use this."""
import re
FLAGS = '''var flags=[["France",["#0055a4","#ffffff","#ef4135"],"#b9d3f0"],["Belgique",["#2d2926","#fdda24","#ef3340"],"#fdda24"],["Côte d'Ivoire",["#f77f00","#ffffff","#009e60"],"#ffc27a"],
   ["Sénégal",["#00853f","#fdef42","#e31b23"],"#fdef42"],["Luxembourg",["#ed2939","#ffffff","#00a1de"],"#b9d3f0"],["Mali",["#14b53a","#fcd116","#ce1126"],"#fcd116"],
   ["Guinée",["#ce1126","#fcd116","#009460"],"#fcd116"],["Tchad",["#002664","#fecb00","#c60c30"],"#fecb00"],["Haïti",["#00209f","#ffffff","#d21034"],"#b9d3f0"],["Québec",["#003da5","#ffffff","#003da5"],"#b9d3f0"]];'''
PAIRS = [
 ('lang="es"', 'lang="fr"'), ("u.lang='es-MX'", "u.lang='fr-FR'"), ("Flag of España", "Flag of France"), (">España<", ">France<"),
 ("family=Fraunces:wght@700;900", "family=Playfair+Display:wght@700;900"), ("'Fraunces'", "'Playfair Display'"),
 ("--navy:#002147;--navy-2:#0b2f5c;--blue:#005fa3;--sky:#9cc9ee;--red:#c8102e;--gold:#b8952a;--gold-dk:#7a5d14;--gold-lt:#fdf6e3;", "--navy:#132C52;--navy-2:#1A3A6B;--blue:#1f5fa8;--sky:#b9d3f0;--red:#c8102e;--gold:#c8102e;--gold-dk:#a11528;--gold-lt:#fdf0f2;"),
 ("background:#c8102e;transition:background .9s ease;}.flag i:nth-child(2){background:#b8952a;}", "background:#0055a4;transition:background .9s ease;}.flag i:nth-child(2){background:#ffffff;}.flag i:nth-child(3){background:#ef4135;}"),
 ('SPAN <span class="c">', 'FREN <span class="c">'), (">Spanish<", ">Français<"), ("Set up your Spanish keyboard first: LAB folder description › <b>Quizzes &amp; accents</b>.", "Set up French accents first: LAB folder description › <b>Accents</b>."),
 (' Set up Spanish accents before your first quiz: see <a href="#quizzes" data-goto="quizzes">Quizzes &amp; accents</a>.', ' Set up French accents before you start: see <a href="#quizzes" data-goto="quizzes">Accents</a>.'),
 ("Set up Spanish accents on your computer. Steps are in the <b>Quizzes &amp; accents</b> tab.", "Set up French accents on your computer. Steps are in the <b>Accents</b> tab."),
 ("<li>For each lab, take the <b>Lab Mini-Quiz</b>. It's part of the lab grade.</li>\n", ""), ("<li>Then record the <b>Lab Bongo</b> assignment. Its instructions are inside Bongo.</li>", "<li>For each lab, record the <b>Lab Bongo</b> assignment. Its instructions are inside Bongo.</li>"),
 ("<li>For each lab: take the <b>Mini-Quiz</b>, then record the <b>Bongo</b> assignment.</li>", "<li>For each lab: open the <b>Bongo</b> assignment and record your video.</li>"),
 ("¡Bienvenidos al Language Lab!", "Bienvenue au Language Lab !"), ("¡Buen semestre!", "Bon semestre !"), ('<h3>Quizzes</h3>', '<h3>Lab 0 and accents</h3>'),
 ("On Windows, check that the taskbar says <b>ESP</b>. Setup steps are in <a href=\"#quizzes\" data-goto=\"quizzes\">Quizzes &amp; accents</a>.", "On Windows, check that the taskbar says <b>INTL</b>. Setup steps are in <a href=\"#quizzes\" data-goto=\"quizzes\">Accents</a>."),
 ("<li>A quiz video or audio clip won't play? Reload the page in Chrome, then try Incognito.</li>", ""),
 ("<small>Before quizzes</small>Quizzes &amp; accents", "<small>Before Lab 1</small>Accents"), ("<h2>Quizzes &amp; accents</h2>", "<h2>Accents</h2>"), ("Quizzes &amp; accents", "Accents"),
 (" If they aren&#x27;t, Task Completion drops to 2 of 5 points.", ""), (" If they aren't, Task Completion drops to 2 of 5 points.", ""),
 ("Mac keyboard. Option plus e, n, u, 1, or Shift and question mark make the Spanish characters.", "Mac keyboard. Option plus e, grave accent, i, u, c, or q makes the French characters."),
 ("Windows keyboard. Keys that differ", "Windows keyboard. Keys that differ"), ("Your slides must be visible for the whole video.", "Your slides must be visible for the whole video."),
 ("<li>The Language Lab doesn't extend a deadline for a technology problem, even one reported before 11:59 PM.</li>", ""), ("<li>The Language Lab doesn't extend a deadline for a technology problem, even one reported before the due time.</li>", ""),
 ("Contacting the Lab doesn't extend the deadline.", "The Lab is open Monday to Friday, 8 AM to 5 PM, so don't wait for the evening of the due date."),
 ("body{font-family:'DM Sans'", "body{font-variant-numeric:lining-nums;font-family:'DM Sans'"),
 ('class="kb" role="img"', 'class="kb" tabindex="0" role="img"'),
 ("the gold Record in the Lab tab", "the red Record in the Lab tab"),
 ("Every lab quiz and Bongo assignment gets two release conditions", "Every Bongo assignment gets two release conditions"),
 (".wbar .w3{background:var(--green);}", ".wbar .w3{background:var(--green);} .wbar .w4{background:var(--navy-2);}"),
]
def loc(s, extra=None):
    s = s.replace("⌥ ", "").replace(" ⌥", "").replace("⌥", "")
    s = re.sub(r"var flags=\[\[.*?\]\];", lambda _: FLAGS, s, count=1, flags=re.S)
    s = s.replace("Spanish-speaking countries", "French-speaking countries").replace("// España first", "// France first")
    s = re.sub(r'<div class="box"><h3>Mini-quizzes</h3>.*?</ul></div>\s*', "", s, flags=re.S)
    for a, b in PAIRS + [tuple(x) for x in (extra or [])]:
        s = s.replace(a, b)
    return s
