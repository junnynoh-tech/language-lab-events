/* Lab console sign-in (2026-11-23, Daniel: "When they open the lab console they should log in", a sign-in button at the
   top, and levels that are easy to tell apart). Loaded by console.html, semester.html and student-view.html.

   One passcode per person type, checked by the Lab's Worker (labs/event-requests/worker.js, /plan):
     Editor: Daniel's editing passcode (PLAN_EDIT_PASSCODE). Saves the shared Semester plan; with his GitHub key he
             also saves events and lab instructions.
     Viewer: the coordinators' passcode (PLAN_PASSCODE). Sees everything, can try things; nothing they do is saved
             for others.
   Until PLAN_EDIT_PASSCODE is set, the coordinators' passcode counts as Editor (the Worker says so).

   What it is and isn't: the pages are public files, so this is a front door, not a lock. What must stay private is
   locked elsewhere: the shared plan by the Worker's passcode check, event requests and saving by GitHub keys.
   Stored in this browser only: the passcode, the level and the name typed in (CLAUDE.md rule 11: no data in the page).
   Sign out forgets all three and the GitHub key. */
(() => {
  'use strict';
  const WORKER = 'https://lab-requests.junnynoh.workers.dev/plan?meta=1';
  const K = { pass: 'labConsolePass', role: 'labConsoleRole', name: 'labConsoleMe', token: 'labConsoleToken' };
  const get = k => { try { return localStorage.getItem(k) || ''; } catch (e) { return ''; } };
  const set = (k, v) => { try { v ? localStorage.setItem(k, v) : localStorage.removeItem(k); } catch (e) {} };
  const ICON = {   // drawn, so they show on every computer (an emoji can turn into an empty box)
    edit: '<svg width="13" height="13" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M11 2.5l2.5 2.5L6 12.5H3.5V10z"/></svg>',
    faculty: '<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M8 4C6.5 2.8 4.5 2.5 1.5 2.8v9.7c3-.3 5 0 6.5 1.2 1.5-1.2 3.5-1.5 6.5-1.2V2.8C11.5 2.5 9.5 2.8 8 4zM8 4v9.7"/></svg>',
    view: '<svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M1.5 8s2.4-4.5 6.5-4.5S14.5 8 14.5 8 12.1 12.5 8 12.5 1.5 8 1.5 8z"/><circle cx="8" cy="8" r="2"/></svg>' };
  const pill = r => `<span class="lab-lvl ${r}">${ICON[r]}${LEVEL[r].label}</span>`;
  const lvl = r => (r === 'view' || r === 'faculty') ? r : 'edit';
  /* faculty see only the Faculty page; the coordinators' areas send them there */
  const FACULTY_PAGE = document.documentElement.dataset.area === 'faculty';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const LEVEL = {
    edit: { label: 'Editor', note: 'You can save changes for everyone.' },
    view: { label: 'Viewer', note: 'You can look and try things. Only the Lab coordinator saves.' },
    faculty: { label: 'Faculty', note: 'Read only: your courses’ labs, due dates and proposals.' }
  };

  const css = document.createElement('style');
  css.textContent = `
.lab-acct { margin: 0 2px; padding: 10px 12px; border-radius: 12px; border: 1px solid var(--line, #DCDDD8); background: var(--surface, #fff); display: grid; gap: 6px; }
.lab-acct .who { display: flex; align-items: center; gap: 8px; min-width: 0; }
.lab-acct .who b { font-size: 14px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lab-lvl { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 999px; font-weight: 700; font-size: 13px; line-height: 1.3; letter-spacing: .02em; white-space: nowrap; }
.lab-lvl.edit { background: #B08D3F; color: #1F2937; }
.lab-lvl.faculty { background: var(--surface, #fff); color: var(--accent, #1A3A6B); border: 2px solid var(--accent, #1A3A6B); }
.lab-lvl.view { background: var(--chip, #EEF0F3); color: var(--text, #1F2937); border: 1px dashed var(--sub, #5A6472); }
.lab-acct .lab-note { margin: 0; font-size: 13px; color: var(--sub, #5A6472); line-height: 1.35; }
.lab-acct .row { display: flex; gap: 6px; flex-wrap: wrap; }
.lab-acct button { font-weight: 600; font-size: 13px; line-height: 1; font-family: inherit; padding: 7px 10px; min-height: 32px; border-radius: 8px; border: 1px solid var(--line, #DCDDD8); background: var(--bg, #F7F7F5); color: inherit; cursor: pointer; }
.lab-acct button.pri { background: var(--accent, #1A3A6B); color: var(--accent-ink, #fff); border-color: var(--accent, #1A3A6B); }
html[data-level="view"] [data-editor-only] { display: none !important; }
#labGate { position: fixed; inset: 0; z-index: 1000; display: grid; place-items: center; padding: 16px; background: var(--bg, #F7F7F5); overflow: auto; }
#labGate .box { width: min(440px, 100%); background: var(--surface, #fff); color: var(--text, #1F2937); border: 1px solid var(--line, #DCDDD8); border-radius: 16px; padding: 26px 24px; box-shadow: 0 10px 40px rgba(20,30,50,.12); }
#labGate small { display: block; font-size: 13px; letter-spacing: .08em; text-transform: uppercase; color: var(--sub, #5A6472); }
#labGate h1 { font: 700 26px/1.2 "Source Serif 4", Georgia, serif; margin: 2px 0 6px; }
#labGate p { margin: 0 0 14px; color: var(--sub, #5A6472); }
#labGate label { display: grid; gap: 4px; font-weight: 600; margin: 0 0 12px; }
#labGate input { min-height: 44px; padding: 8px 12px; border: 1px solid var(--line, #DCDDD8); border-radius: 8px; font: inherit; background: var(--bg, #F7F7F5); color: inherit; }
#labGate button { width: 100%; min-height: 46px; border: 0; border-radius: 10px; background: var(--accent, #1A3A6B); color: var(--accent-ink, #fff); font-weight: 700; font-size: 16px; font-family: inherit; cursor: pointer; }
#labGate .msg { min-height: 1.4em; margin: 10px 0 0; font-weight: 600; color: var(--bad, #A12A2A); }
#labGate .levels { display: grid; gap: 6px; margin: 16px 0 0; padding: 12px 0 0; border-top: 1px solid var(--line, #DCDDD8); font-size: 14px; color: var(--sub, #5A6472); }
#labGate .levels div { display: flex; gap: 8px; align-items: baseline; }
html.lab-gated body > :not(#labGate) { visibility: hidden; }`;
  document.head.appendChild(css);

  const state = { pass: get(K.pass), role: get(K.role), name: get(K.name) };
  // before anything shows: hide the page until signed in, and send faculty straight to their page
  if (!state.pass || (state.role === 'faculty' && !FACULTY_PAGE)) document.documentElement.classList.add('lab-gated');
  if (state.pass && state.role === 'faculty' && !FACULTY_PAGE) location.replace('faculty.html');
  const apply = () => { document.documentElement.dataset.level = state.pass ? (state.role || 'edit') : 'none'; window.LAB_AUTH = { ...state }; };

  async function check(pass) {   // → 'edit' | 'view'; throws with a message people can act on
    let r;
    try { r = await fetch(WORKER, { cache: 'no-store', headers: { 'X-Lab-Pass': pass } }); }
    catch (e) { throw new Error('The sign-in check couldn’t be reached. Check the internet connection and try again.'); }
    if (r.status === 401) throw new Error('That passcode didn’t work. Check it (capitals count) and try again.');
    if (r.status === 404 || r.status === 503) throw new Error('Sign-in isn’t switched on yet. Tell Daniel.');
    if (!r.ok) throw new Error(`The sign-in check didn’t answer (${r.status}). Try again in a minute.`);
    const d = await r.json().catch(() => ({}));
    return lvl(d.role);
  }

  function badge() {
    const rail = document.querySelector('.rail'); if (!rail) return;
    let box = document.getElementById('labAcct');
    if (!box) { box = document.createElement('section'); box.id = 'labAcct'; box.className = 'lab-acct'; box.setAttribute('aria-label', 'Signed in'); (rail.querySelector('.brand') || rail.firstChild).after(box); }
    const L = LEVEL[state.role] || LEVEL.edit;
    box.innerHTML = `<div class="who">${pill(lvl(state.role))}<b title="${esc(state.name)}">${esc(state.name || 'Signed in')}</b></div>`
      + `<p class="lab-note">${L.note}</p><div class="row"><button type="button" id="labSignOut">Sign out</button></div>`;
    box.querySelector('#labSignOut').onclick = signOut;
  }

  function gate(message) {
    document.documentElement.classList.add('lab-gated');
    let g = document.getElementById('labGate');
    if (!g) { g = document.createElement('div'); g.id = 'labGate'; document.body.appendChild(g); }
    g.innerHTML = `<form class="box" novalidate aria-labelledby="labGateH"><small>Language Lab</small><h1 id="labGateH">Sign in to the Lab console</h1>
<p>Use the passcode the Language Lab sent you. This computer remembers you until you sign out.</p>
<label>Your name <input id="labGateName" autocomplete="name" value="${esc(state.name)}" placeholder="First and last name"></label>
<label>Passcode <input id="labGatePass" type="password" autocomplete="current-password" spellcheck="false"></label>
<button type="submit">Sign in</button><p class="msg" id="labGateMsg" role="alert">${esc(message || '')}</p>
<div class="levels" aria-label="The two levels"><div>${pill('edit')}<span>saves changes for everyone (the Lab coordinator).</span></div>
<div>${pill('view')}<span>sees everything and can try things; nothing is saved for others.</span></div>
<div>${pill('faculty')}<span>a quick reference for professors: labs, due dates and proposals.</span></div></div></form>`;
    const f = g.querySelector('form'), msg = g.querySelector('#labGateMsg');
    setTimeout(() => (state.name ? g.querySelector('#labGatePass') : g.querySelector('#labGateName')).focus(), 30);
    f.onsubmit = async e => {
      e.preventDefault();
      const name = g.querySelector('#labGateName').value.trim(), pass = g.querySelector('#labGatePass').value.trim();
      if (!name) { msg.textContent = 'Type your name: it shows who saved what.'; g.querySelector('#labGateName').focus(); return; }
      if (!pass) { msg.textContent = 'Type the passcode.'; g.querySelector('#labGatePass').focus(); return; }
      const btn = f.querySelector('button'); btn.disabled = true; btn.textContent = 'Checking…'; msg.textContent = '';
      try {
        const role = await check(pass);
        set(K.pass, pass); set(K.role, role); set(K.name, name);
        location.reload();   // each page starts from the signed-in state (the Semester plan opens the shared plan)
      } catch (err) { msg.textContent = err.message; btn.disabled = false; btn.textContent = 'Sign in'; }
    };
  }

  function signOut() {
    if (!confirm('Sign out of the Lab console on this computer?\n\nThis computer forgets your passcode and name (and the GitHub key, if one was saved). Sign in again with the passcode any time.')) return;
    [K.pass, K.role, K.token].forEach(k => set(k, ''));
    location.reload();
  }

  const route = () => {   // → true when this page isn't for this level (and it's leaving)
    if (state.role === 'faculty' && !FACULTY_PAGE) { location.replace('faculty.html'); return true; }
    if (FACULTY_PAGE && state.role !== 'faculty') document.querySelectorAll('[data-coord-only]').forEach(e => e.hidden = false);
    return false;
  };
  const start = () => {
    apply();
    if (!state.pass) return gate();
    if (route()) return;
    document.documentElement.classList.remove('lab-gated');
    badge();
    check(state.pass).then(role => {   // the level can change (e.g. once the editing passcode is set): keep it current
      if (role !== state.role) { state.role = role; set(K.role, role); apply(); if (route()) return; badge(); document.dispatchEvent(new CustomEvent('labauth', { detail: { ...state } })); }
    }).catch(err => { if (/didn’t work/.test(err.message)) { set(K.pass, ''); set(K.role, ''); state.pass = ''; apply(); gate('Your passcode changed. Sign in with the new one.'); } });
  };
  apply();
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
