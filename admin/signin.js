/* Lab console sign-in (2026-11-23, Daniel: "When they open the lab console they should log in", a sign-in button at the
   top, and levels that are easy to tell apart). Loaded by every console page (Tutorials with data-optional).

   One passcode per person type, checked by the Lab's Worker (labs/event-requests/worker.js, /plan):
     Editor: Daniel's editing passcode (PLAN_EDIT_PASSCODE). Saves the shared Semester plan; with his GitHub key he
             also saves events and lab instructions.
     Viewer: the coordinators' passcode (PLAN_PASSCODE). Sees everything, can try things; nothing they do is saved
             for others.
   Until PLAN_EDIT_PASSCODE is set, the coordinators' passcode counts as Editor (the Worker says so).

   What it is and isn't: the pages are public files, so this is a front door, not a lock. What must stay private is
   locked elsewhere: the shared plan by the Worker's passcode check, event requests and saving by GitHub keys.
   Stored in this browser only: the passcode and the level (CLAUDE.md rule 11: no data in the page). Names come from the
   Worker (each person's own passcode, Settings › People), never typed in. Sign out forgets both and the GitHub key. */
(() => {
  'use strict';
  const WORKER = 'https://lab-requests.junnynoh.workers.dev/plan?meta=1';
  /* Tutorials loads this with data-optional: lab assistants use it without signing in, so no sign-in screen there;
     a signed-in coordinator still gets the same console menu. Links are built from this file's folder (admin/). */
  const ME = document.currentScript, OPTIONAL = !!(ME && ME.hasAttribute('data-optional'));
  const BASE = ME && ME.src ? new URL('.', ME.src).href : '';
  const AREAS = [['console.html', 'Events', 'events'], ['semester.html', 'Semester plan', 'semester'], ['student-view.html', 'Student view', 'student'], ['faculty.html', 'Faculty view', 'faculty'], ['tutorials/index.html', 'Tutorials', 'tutorials']];
  const here = () => { const u = location.pathname; return (AREAS.find(a => u.endsWith('/' + a[0]) || (a[0] === 'tutorials/index.html' && /\/tutorials\/(index\.html)?$/.test(u))) || [])[0] || (u.endsWith('/settings.html') ? 'settings.html' : ''); };
  const K = { pass: 'labConsolePass', role: 'labConsoleRole', name: 'labConsoleMe', token: 'labConsoleToken', email: 'labConsoleEmail', personal: 'labConsolePersonal', username: 'labConsoleUser', session: 'labConsoleSession' };
  const get = k => { try { return localStorage.getItem(k) || ''; } catch (e) { return ''; } };
  const set = (k, v) => { try { v ? localStorage.setItem(k, v) : localStorage.removeItem(k); } catch (e) {} };
  const ICON = {   // drawn, so they show on every computer (an emoji can turn into an empty box)
    edit: '<svg width="13" height="13" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M11 2.5l2.5 2.5L6 12.5H3.5V10z"/></svg>',
    faculty: '<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M8 4C6.5 2.8 4.5 2.5 1.5 2.8v9.7c3-.3 5 0 6.5 1.2 1.5-1.2 3.5-1.5 6.5-1.2V2.8C11.5 2.5 9.5 2.8 8 4zM8 4v9.7"/></svg>',
    view: '<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M1.5 8s2.4-4.5 6.5-4.5S14.5 8 14.5 8 12.1 12.5 8 12.5 1.5 8 1.5 8z"/><circle cx="8" cy="8" r="2"/></svg>' };
  const svg = d => `<svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`;
  const AICON = {
    events: svg('<rect x="3" y="4" width="14" height="13" rx="2"/><path d="M3 8h14M7 2.5v3M13 2.5v3M10 10.5l1 2 2.2.3-1.6 1.5.4 2.2-2-1.1-2 1.1.4-2.2-1.6-1.5 2.2-.3z"/>'),
    semester: svg('<rect x="3" y="4" width="14" height="13" rx="2"/><path d="M3 8h14M7 2.5v3M13 2.5v3M6.5 11h2M11.5 11h2M6.5 14h2"/>'),
    student: svg('<rect x="2.5" y="3.5" width="15" height="10" rx="1.5"/><path d="M7 17h6M10 13.5V17"/>'),
    faculty: svg('<path d="M10 5C8.2 3.6 5.8 3.3 2.5 3.6v11.2c3.3-.3 5.7 0 7.5 1.4 1.8-1.4 4.2-1.7 7.5-1.4V3.6C14.2 3.3 11.8 3.6 10 5zM10 5v11.2"/>'),
    tutorials: svg('<circle cx="10" cy="10" r="7.5"/><path d="M7.8 7.8a2.3 2.3 0 1 1 3.2 2.1c-.6.3-1 .8-1 1.5v.4M10 14.6v.1"/>'),
    settings: svg('<circle cx="10" cy="10" r="6.7" stroke-width="2.6" stroke-dasharray="2.1 2.11"/><circle cx="10" cy="10" r="4.4"/><circle cx="10" cy="10" r="1.6"/>'),
    out: svg('<path d="M8 4H4.5A1.5 1.5 0 0 0 3 5.5v9A1.5 1.5 0 0 0 4.5 16H8M12.5 13.5 16 10l-3.5-3.5M16 10H7.5"/>') };
  const pill = r => `<span class="lab-lvl ${r}">${ICON[r]}${LEVEL[r].label}</span>`;
  const lvl = r => (r === 'view' || r === 'faculty') ? r : 'edit';
  /* faculty see only the Faculty page; the coordinators' areas send them there */
  const FACULTY_PAGE = document.documentElement.dataset.area === 'faculty', SETTINGS_PAGE = document.documentElement.dataset.area === 'settings';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const LEVEL = {
    edit: { label: 'Editor', note: 'You can save changes for everyone.' },
    view: { label: 'Viewer', note: 'You can look and try things. Only the Lab coordinator saves.' },
    faculty: { label: 'Faculty', note: 'Read only: your courses’ labs, due dates and proposals.' }
  };

  const css = document.createElement('style');
  css.textContent = `
.lab-lvl { display: inline-flex; align-items: center; gap: 5px; padding: 2px 9px; border-radius: 999px; font-weight: 700; font-size: 12.5px; line-height: 1.4; letter-spacing: .02em; white-space: nowrap; flex: none; }
.lab-lvl.edit { background: #B08D3F; color: #1F2937; }
.lab-lvl.faculty { background: var(--surface, #fff); color: var(--accent, #1A3A6B); border: 2px solid var(--accent, #1A3A6B); }
.lab-lvl.view { background: var(--chip, #EEF0F3); color: var(--text, #1F2937); border: 1px dashed var(--sub, #5A6472); }
/* the console menu (2026-11-23, Daniel: "clean and aesthetic", no shifting between areas): the same width, title,
   account card and area list on every page; only each area's own menu below it changes */
html.lc .shell { grid-template-columns: 264px minmax(0, 1fr) !important; }
html.lc .rail { padding: 18px 14px !important; gap: 14px !important; }
html.lc .rail > .brand, html.lc .rail > nav.areas, html.lc .rail > #areas { display: none !important; }
.lc-top { display: grid; gap: 12px; font-size: 15px; line-height: 1.4; font-family: "DM Sans", "Segoe UI", Arial, sans-serif; }
html.lc .rail nav.lc-nav { display: block !important; margin: 0 !important; padding: 0 !important; width: auto !important; border: 0 !important; background: none !important; }
.lc-top ul, .lc-top li, .lc-top p, .lc-top section { margin: 0; }
.lc-brand { display: block; padding: 0 8px; text-decoration: none; color: var(--text, #1F2937); }
.lc-brand small { display: block; line-height: 1.4; font-size: 12px; letter-spacing: .1em; text-transform: uppercase; color: var(--sub, #5A6472); }
.lc-brand b { display: block; font: 700 22px/1.2 "Source Serif 4", Georgia, serif; }
.lc-me { border: 1px solid var(--line, #DCDDD8); background: var(--surface, #fff); border-radius: 12px; padding: 10px; display: grid; gap: 8px; }
.lc-me .who { display: flex; align-items: center; gap: 8px; min-width: 0; }
.lc-me .who b { font-size: 14px; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lc-me .acts { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.lc-me .acts.one { grid-template-columns: 1fr; }
.lc-btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 34px; padding: 0 10px; border-radius: 8px; border: 1px solid var(--line, #DCDDD8); background: var(--bg, #F7F7F5); color: var(--text, #1F2937); font-weight: 600; font-size: 13px; line-height: 1; font-family: inherit; text-decoration: none; cursor: pointer; white-space: nowrap; }
.lc-btn:hover { border-color: var(--sub, #5A6472); }
.lc-btn[aria-current="page"] { background: var(--accent, #1A3A6B); color: var(--accent-ink, #fff); border-color: var(--accent, #1A3A6B); }
.lc-btn.pri { background: var(--accent, #1A3A6B); color: var(--accent-ink, #fff); border-color: var(--accent, #1A3A6B); }
.lc-me .uname { margin: 0; font-size: 12.5px; color: var(--sub, #5A6472); display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.lc-me .uname button { border: 0; background: none; padding: 0; color: var(--text, #1F2937); text-decoration: underline; font: inherit; cursor: pointer; }
.lc-me .lab-note { margin: 0; font-size: 12.5px; color: var(--sub, #5A6472); }
.lc-me form { display: grid; gap: 6px; }
.lc-me form input { min-height: 34px; padding: 6px 8px; border: 1px solid var(--line, #DCDDD8); border-radius: 8px; font: inherit; background: var(--bg, #F7F7F5); color: inherit; }
.lc-areas { list-style: none; margin: 0; padding: 0; display: grid; gap: 2px; }
.lc-areas a { display: flex; align-items: center; gap: 10px; height: 38px; padding: 0 10px; border-radius: 9px; text-decoration: none; color: var(--text, #1F2937); font-weight: 600; font-size: 15px; }
.lc-areas a:hover { background: var(--chip, #EEF0F3); }
.lc-areas a[aria-current="page"] { background: var(--accent, #1A3A6B); color: var(--accent-ink, #fff); }
.lc-areas svg { flex: none; opacity: .85; }
.lc-rule { height: 1px; background: var(--line, #DCDDD8); margin: 2px 4px 0; border: 0; }
html.lc .rail-foot { display: grid !important; gap: 8px !important; padding: 0 4px !important; margin-top: auto; }
html.lc .rail-foot > .btn, html.lc .rail-foot > a.btn, html.lc .rail-foot > button { width: 100%; justify-content: center; }
@media (max-width: 860px) {
  html.lc .shell { grid-template-columns: 1fr !important; }
  html.lc .rail { position: static !important; height: auto !important; display: flex !important; flex-direction: column !important; border-right: 0 !important; border-bottom: 1px solid var(--line, #DCDDD8); padding: 12px 16px !important; gap: 10px !important; }
  .lc-top { grid-template-columns: minmax(0, 1fr) auto; align-items: center; gap: 10px; }
  .lc-brand b { font-size: 19px; }
  .lc-me { grid-column: 1 / -1; display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 8px; }
  .lc-me .who { flex: 1 1 140px; }
  .lc-me .acts { display: flex; gap: 6px; }
  .lc-me .uname { flex: 1 1 100%; order: 3; }
  .lc-me .lab-note { display: none; }
  .lc-me form { flex: 1 1 100%; order: 4; }
  html.lc .rail > * { align-self: stretch; width: auto; max-width: 100%; margin-left: 0; margin-right: 0; }
  html.lc .rail-foot { grid-template-columns: 1fr 1fr; }
  html.lc .rail nav.lc-nav { grid-column: 1 / -1; min-width: 0; }
  .lc-areas { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 2px; }
  .lc-areas a { height: 36px; border: 1px solid var(--line, #DCDDD8); white-space: nowrap; flex: none; }
  .lc-rule { display: none; }
}
html[data-level="view"] [data-editor-only] { display: none !important; }
/* Viewers never upload: every file picker and drop zone in every console area is hidden for them */
html[data-level="view"] input[type="file"], html[data-level="view"] .drop, html[data-level="view"] label:has(> input[type="file"]), html[data-level="view"] label:has(+ input[type="file"]) { display: none !important; }
#labGate { position: fixed; inset: 0; z-index: 1000; display: grid; place-items: center; padding: 16px; background: var(--bg, #F7F7F5); overflow: auto; }
#labGate .box { width: min(440px, 100%); background: var(--surface, #fff); color: var(--text, #1F2937); border: 1px solid var(--line, #DCDDD8); border-radius: 16px; padding: 26px 24px; box-shadow: 0 10px 40px rgba(20,30,50,.12); }
#labGate small { display: block; font-size: 13px; letter-spacing: .08em; text-transform: uppercase; color: var(--sub, #5A6472); }
#labGate h1 { font: 700 26px/1.2 "Source Serif 4", Georgia, serif; margin: 2px 0 6px; }
#labGate p { margin: 0 0 14px; color: var(--sub, #5A6472); }
#labGate label { display: grid; gap: 4px; font-weight: 600; margin: 0 0 12px; }
#labGate input { min-height: 44px; padding: 8px 12px; border: 1px solid var(--line, #DCDDD8); border-radius: 8px; font: inherit; background: var(--bg, #F7F7F5); color: inherit; }
#labGate button { width: 100%; min-height: 46px; border: 0; border-radius: 10px; background: var(--accent, #1A3A6B); color: var(--accent-ink, #fff); font-weight: 700; font-size: 16px; font-family: inherit; cursor: pointer; }
#labGate .opt { font-weight: 400; color: var(--sub, #5A6472); font-size: 14px; }
#labGate .msg { min-height: 1.4em; margin: 10px 0 0; font-weight: 600; color: var(--bad, #A12A2A); }
#labGate .levels { display: grid; gap: 6px; margin: 16px 0 0; padding: 12px 0 0; border-top: 1px solid var(--line, #DCDDD8); font-size: 14px; color: var(--sub, #5A6472); }
#labGate .levels div { display: flex; gap: 8px; align-items: baseline; }
html.lab-gated body > :not(#labGate) { visibility: hidden; }`;
  document.head.appendChild(css);

  // the name comes from the Worker: a person's own passcode is who they are (Settings › People). Nobody types a name.
  /* Security (2026-11-25, labs/SECURITY.md): the browser keeps a signed 14-day session from the Worker, never the passcode.
     state.pass is "signed in" (the session, or an old stored passcode until it's traded in on the next visit). */
  const state = { pass: get(K.session) || get(K.pass), role: get(K.role), name: get(K.name), email: get(K.email) };
  // every call to the Worker sends both: a person locked to their email needs it with the passcode (Settings › People)
  // (the email header only when there is one: a Worker without the email lock would refuse the request otherwise)
  window.labHeaders = () => get(K.session) ? { 'X-Lab-Session': get(K.session) } : { 'X-Lab-Pass': get(K.pass), ...(get(K.email) ? { 'X-Lab-Email': get(K.email) } : {}) };
  /* GitHub through the Lab (2026-11-23, Daniel: "rewire the github so it goes through cloudflare"). An Editor's saves
     and reads of the two Lab repositories go to the Worker's /gh (its own GitHub key; signed with the person's name)
     whenever the Worker can reach them, so nobody needs a GitHub key in the browser. The pages keep their GitHub calls
     as they were and use window.LAB_GH_KEY as their key; this rewrites those calls to the Worker. A page with its own
     GitHub key and a Worker that can't reach a repository yet keeps using the key, as before. */
  const W_BASE = WORKER.replace('/plan?meta=1', '');
  window.LAB_GH_KEY = 'lab-console-through-worker';
  const nativeFetch = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    const m = url.match(/^https:\/\/api\.github\.com\/repos\/junnynoh-tech\/(language-lab-events|lab-event-requests)([/?].*)?$/);
    if (m) {
      const h = new Headers(init.headers || {});
      if (h.get('Authorization') === 'Bearer ' + window.LAB_GH_KEY) {
        h.delete('Authorization'); Object.entries(window.labHeaders()).forEach(([k, v]) => h.set(k, v));
        return nativeFetch(`${W_BASE}/gh/${m[1]}${m[2] || ''}`, { ...init, headers: h });
      }
    }
    return nativeFetch(input, init);
  };
  let ghStatusP = null;
  window.labGH = {
    status() {   // { repos: { name: { read, write } }, actions, expires } or null (not an Editor, or the Worker isn't updated)
      if (!ghStatusP) ghStatusP = (get(K.role) === 'edit' && state.pass)
        ? nativeFetch(`${W_BASE}/gh-status`, { cache: 'no-store', headers: window.labHeaders() }).then(r => r.ok ? r.json() : null).catch(() => null)
        : Promise.resolve(null);
      return ghStatusP;
    },
    async can(repo) { const s = await this.status(); return !!(s && s.repos && s.repos[repo] && s.repos[repo].write); }
  };
  // before anything shows: hide the page until signed in, and send faculty straight to their page
  if (!OPTIONAL && (!state.pass || (state.role === 'faculty' && !FACULTY_PAGE) || (SETTINGS_PAGE && state.role !== 'edit'))) document.documentElement.classList.add('lab-gated');
  if (OPTIONAL) document.documentElement.classList.remove('lab-gated');
  if (!OPTIONAL && state.pass && state.role === 'faculty' && !FACULTY_PAGE) location.replace(BASE + 'faculty.html');
  const apply = () => { document.documentElement.dataset.level = state.pass ? (state.role || 'edit') : 'none'; window.LAB_AUTH = { ...state }; };

  /* trade a passcode (and email or username) for a session; a Worker without sessions yet: keep the old way */
  async function signIn(pass, email) {
    let r;
    try { r = await nativeFetch(W_BASE + '/session', { method: 'POST', cache: 'no-store', headers: { 'X-Lab-Pass': pass, ...(email ? { 'X-Lab-Email': email } : {}) } }); }
    catch (e) { return { legacy: true, ...(await check({ 'X-Lab-Pass': pass, ...(email ? { 'X-Lab-Email': email } : {}) })) }; }
    if (r.status === 404) return { legacy: true, ...(await check({ 'X-Lab-Pass': pass, ...(email ? { 'X-Lab-Email': email } : {}) })) };
    const d = await r.json().catch(() => ({}));
    if (r.status === 429) throw new Error(d.error || 'Too many wrong passcodes. Wait 15 minutes, then try again.');
    if (r.status === 401) throw new Error('That email or username and passcode didn’t work together. Check both and try again.');
    if (r.ok && !d.session) return { legacy: true, ...(await check({ 'X-Lab-Pass': pass, ...(email ? { 'X-Lab-Email': email } : {}) })) };   // a Worker without sessions
    if (!r.ok) throw new Error(`Sign-in didn’t answer (${r.status}). Try again in a minute.`);
    return { session: d.session, role: lvl(d.role), name: String(d.name || '').slice(0, 80), personal: !!d.personal, username: String(d.username || '') };
  }
  function keep(x, email) {   // what this browser remembers after signing in (never the passcode once the Worker gives sessions)
    set(K.session, x.session || ''); set(K.pass, x.legacy ? x.pass : ''); set(K.personal, x.personal ? '1' : ''); set(K.username, x.username);
    set(K.role, x.role); set(K.name, x.name); set(K.email, email);
  }
  async function check(headers = window.labHeaders()) {   // → { role, name, … }; throws with a message people can act on
    let r; const email = headers['X-Lab-Email'];
    try { r = await nativeFetch(WORKER, { cache: 'no-store', headers }); }
    catch (e) { throw new Error(email ? 'Signing in with an email isn’t switched on yet (the Lab’s Worker needs its update). Leave the email empty if you have a shared passcode, or tell Daniel.' : 'The sign-in check couldn’t be reached. Check the internet connection and try again.'); }
    if (r.status === 401) throw new Error('That email or username and passcode didn’t work together. Check both and try again.');
    if (r.status === 429) throw new Error('Too many wrong passcodes. Wait 15 minutes, then try again.');
    if (r.status === 404 || r.status === 503) throw new Error('Sign-in isn’t switched on yet. Tell Daniel.');
    if (!r.ok) throw new Error(`The sign-in check didn’t answer (${r.status}). Try again in a minute.`);
    const d = await r.json().catch(() => ({}));
    return { role: lvl(d.role), name: String(d.name || '').slice(0, 80), personal: !!d.personal, username: String(d.username || '') };
  }

  /* the same top of the menu on every page: title, who you are (+ Settings for Editors, Sign out), the areas */
  function badge() {
    const rail = document.querySelector('.rail'); if (!rail) return;
    document.documentElement.classList.add('lc');
    document.getElementById('labAcct')?.remove();
    let top = document.getElementById('lcTop');
    if (!top) { top = document.createElement('div'); top.id = 'lcTop'; top.className = 'lc-top'; rail.prepend(top); }
    const r = lvl(state.role), L = LEVEL[r], cur = here(), editor = r === 'edit', personal = !!get(K.personal), u = get(K.username);
    const areas = r === 'faculty' ? [] : AREAS;
    top.innerHTML = `<a class="lc-brand" href="${BASE}${r === 'faculty' ? 'faculty.html' : 'console.html'}"><small>Language Lab</small><b>Lab console</b></a>`
      + `<section class="lc-me" aria-label="Signed in"><div class="who">${pill(r)}<b title="${esc(state.name)}">${esc(state.name || 'Signed in')}</b></div>`
      + `<p class="lab-note">${L.note}</p>`
      + (personal ? `<p class="uname">${u ? `Username: <b>${esc(u)}</b>` : 'No username yet.'}<button type="button" id="labUser">${u ? 'Change' : 'Set one'}</button></p>` : '')
      + `<div class="acts${editor ? '' : ' one'}">${editor ? `<a class="lc-btn" href="${BASE}settings.html"${cur === 'settings.html' ? ' aria-current="page"' : ''}>${AICON.settings}Settings</a>` : ''}<button type="button" class="lc-btn" id="labSignOut">${AICON.out}Sign out</button></div>`
      + `<form id="labUserForm" hidden novalidate></form></section>`
      + (areas.length ? `<nav class="lc-nav" aria-label="Console areas"><ul class="lc-areas">${areas.map(([f, l, k]) => `<li><a href="${BASE}${f}"${cur === f ? ' aria-current="page"' : ''}>${AICON[k]}${l}</a></li>`).join('')}</ul></nav><hr class="lc-rule">` : '');
    top.querySelector('#labSignOut').onclick = signOut;
    const ub = top.querySelector('#labUser'); if (ub) ub.onclick = () => userForm(top.querySelector('.lc-me'));
  }

  /* pick your own username (Daniel, 2026-11-23: "easier access"): then sign in with it instead of the email */
  function userForm(box) {
    const f = box.querySelector('#labUserForm'); f.hidden = false;
    f.innerHTML = `<label style="display:grid;gap:4px;font-weight:600;font-size:13px">Username<input id="labUserIn" value="${esc(get(K.username))}" autocapitalize="none" spellcheck="false" maxlength="30" style="min-height:36px;padding:6px 8px;border:1px solid var(--line,#DCDDD8);border-radius:8px;font:inherit;background:var(--bg,#F7F7F5);color:inherit"></label>`
      + `<p class="lab-note" style="margin:4px 0">3 to 30 letters or numbers; dot, dash and underscore are fine.</p><div class="acts"><button type="submit" class="lc-btn pri">Save</button><button type="button" class="lc-btn" id="labUserX">Cancel</button></div><p class="lab-note" id="labUserMsg" role="status" style="font-weight:600"></p>`;
    const inp = f.querySelector('#labUserIn'); inp.focus();
    f.querySelector('#labUserX').onclick = () => { f.hidden = true; f.innerHTML = ''; document.getElementById('labUser')?.focus(); };
    f.onsubmit = async e => {
      e.preventDefault(); const u = inp.value.trim().toLowerCase(), msg = f.querySelector('#labUserMsg');
      if (u && !/^[a-z0-9][a-z0-9._-]{2,29}$/.test(u)) { msg.textContent = 'Use 3 to 30 letters or numbers (dot, dash, underscore).'; inp.focus(); return; }
      msg.textContent = 'Saving…';
      try {
        const r = await fetch(WORKER.replace('/plan?meta=1', '/me'), { method: 'POST', headers: { ...window.labHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify({ username: u }) });
        const d = await r.json().catch(() => ({})); if (!r.ok) throw new Error(d.error || `Couldn’t save (${r.status}).`);
        set(K.username, d.person.username); badge(); const b = document.getElementById('labUser'); if (b) b.focus();
        const n = document.createElement('p'); n.className = 'lab-note'; n.setAttribute('role', 'status'); n.style.fontWeight = '600';
        n.textContent = u ? `Saved. Next time, sign in with “${u}” and your passcode.` : 'Username removed. Sign in with your email.'; document.querySelector('#lcTop .lc-me').appendChild(n);
      } catch (err) { msg.textContent = err.message; }
    };
  }

  function gate(message) {
    document.documentElement.classList.add('lab-gated');
    let g = document.getElementById('labGate');
    if (!g) { g = document.createElement('div'); g.id = 'labGate'; document.body.appendChild(g); }
    g.innerHTML = `<form class="box" novalidate aria-labelledby="labGateH"><small>Language Lab</small><h1 id="labGateH">Sign in to the Lab console</h1>
<p>Use the passcode the Language Lab sent you. This computer remembers you until you sign out.</p>
<label>UNG email or username <input id="labGateEmail" type="text" inputmode="email" autocapitalize="none" autocomplete="username" spellcheck="false" placeholder="name@ung.edu or your username" value="${esc(state.email)}"></label>
<label>Passcode <input id="labGatePass" type="password" autocomplete="current-password" spellcheck="false"></label>
<button type="submit">Sign in</button><p class="msg" id="labGateMsg" role="alert">${esc(message || '')}</p>
<div class="levels" aria-label="The two levels"><div>${pill('edit')}<span>saves changes for everyone (the Lab coordinator).</span></div>
<div>${pill('view')}<span>sees everything and can try things; nothing is saved for others.</span></div>
<div>${pill('faculty')}<span>a quick reference for professors: labs, due dates and proposals.</span></div></div></form>`;
    const f = g.querySelector('form'), msg = g.querySelector('#labGateMsg');
    setTimeout(() => (state.email ? g.querySelector('#labGatePass') : g.querySelector('#labGateEmail')).focus(), 30);
    f.onsubmit = async e => {
      e.preventDefault();
      const pass = g.querySelector('#labGatePass').value.trim(), email = g.querySelector('#labGateEmail').value.trim().toLowerCase();
      if (email && (email.includes('@') ? !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) : !/^[a-z0-9][a-z0-9._-]{2,29}$/.test(email))) { msg.textContent = 'That email or username doesn’t look right.'; g.querySelector('#labGateEmail').focus(); return; }
      if (!pass) { msg.textContent = 'Type the passcode.'; g.querySelector('#labGatePass').focus(); return; }
      const btn = f.querySelector('button'); btn.disabled = true; btn.textContent = 'Checking…'; msg.textContent = '';
      try {
        const x = await signIn(pass, email); keep({ ...x, pass }, email);
        location.reload();   // each page starts from the signed-in state (the Semester plan opens the shared plan)
      } catch (err) { msg.textContent = err.message; btn.disabled = false; btn.textContent = 'Sign in'; }
    };
  }

  function signOut() {
    if (!confirm('Sign out of the Lab console on this computer?\n\nThis computer forgets your email and passcode (and the GitHub key, if one was saved). Sign in again with the passcode any time.')) return;
    [K.session, K.pass, K.role, K.token, K.email, K.name, K.personal, K.username].forEach(k => set(k, ''));
    location.reload();
  }

  const route = () => {   // → true when this page isn't for this level (and it's leaving)
    if (OPTIONAL) return false;
    if (state.role === 'faculty' && !FACULTY_PAGE) { location.replace(BASE + 'faculty.html'); return true; }
    if (SETTINGS_PAGE && state.role !== 'edit') { location.replace(BASE + 'console.html'); return true; }
    if (FACULTY_PAGE && state.role !== 'faculty') document.querySelectorAll('[data-coord-only]').forEach(e => e.hidden = false);
    return false;
  };
  const start = async () => {
    apply();
    if (!state.pass) return OPTIONAL ? undefined : gate();
    if (get(K.pass) && !get(K.session)) {   // a passcode kept by an older version: trade it for a session and forget it
      try { const x = await signIn(get(K.pass), get(K.email)); if (!x.legacy) { keep(x, get(K.email)); state.pass = x.session; } } catch (e) {}
    }
    if (route()) return;
    document.documentElement.classList.remove('lab-gated');
    badge();
    check().then(({ role, name, personal, username }) => {   // the level or name can change (Settings › People): keep them current
      if (name !== state.name) { state.name = name; set(K.name, name); apply(); badge(); }
      if (username !== get(K.username) || (personal ? '1' : '') !== get(K.personal)) { set(K.username, username); set(K.personal, personal ? '1' : ''); badge(); }
      if (role !== state.role) { state.role = role; set(K.role, role); apply(); if (route()) return; badge(); document.dispatchEvent(new CustomEvent('labauth', { detail: { ...state } })); }
    }).catch(err => { if (/didn’t work/.test(err.message) && !OPTIONAL) { [K.session, K.pass, K.role].forEach(k => set(k, '')); state.pass = ''; apply(); gate('Your sign-in ended (two weeks passed, or your passcode or level changed). Sign in again.'); } });
  };
  apply();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
