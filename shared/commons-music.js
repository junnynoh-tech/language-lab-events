/* Free music on Wikimedia Commons: ONE checker for the request form (request/) and the events console (admin/) (2026-11-11).
   A track passes when it has a free license (Public domain, CC0, CC BY, CC BY-SA; never NC/ND), an artist to credit,
   an MP3 that Commons serves (its own MP3 copy of an OGG/FLAC/WAV counts), and lasts 15 minutes or less.
   Change the rules here only; both pages load this file. */
(() => {
  const API = 'https://commons.wikimedia.org/w/api.php';
  const OK_LICENSE = /^(public domain|pd|cc0|cc-?zero|cc[- ]by(-sa)?([- ][\d.]+)?)$/i;
  const GENRES = ['Latin', 'World', 'Holiday', 'Lounge/relax', 'Jazz', 'Classical', 'African', 'Pop', 'Contemporary', 'Polka', 'Reggae', 'Ska'];
  const BLOCKED = /youtu\.?be|spotify|soundcloud|apple\.com|tiktok/i;   // copyrighted, and their terms forbid playing audio on our page
  const strip = h => { const d = document.createElement('div'); d.innerHTML = h || ''; return d.textContent.replace(/\s+/g, ' ').trim(); };
  const mmss = n => `${Math.floor(n / 60)}:${String(n % 60).padStart(2, '0')}`;
  function judge(p) {
    const ii = p.imageinfo?.[0], md = ii?.extmetadata || {}, lic = strip(md.LicenseShortName?.value) || '', title = (p.title || '').replace(/^File:/, '').replace(/\.[a-z0-9]+$/i, '');
    const r = { title: title.replace(/\s*\(ISRC[^)]*\)\s*$/, ''), page: ii?.descriptionurl || '', license: lic, artist: strip(md.Artist?.value).slice(0, 200), duration: Math.round(+(ii?.duration || p.videoinfo?.[0]?.duration || 0)), problems: [] };
    if (!ii) { r.problems.push('That file isn’t on Wikimedia Commons.'); return r; }
    if (!/^audio\/|^application\/ogg$|^video\/ogg$/.test(ii.mime)) r.problems.push('It isn’t an audio file.');
    if (!OK_LICENSE.test(lic.replace(/\s+/g, ' ').trim())) r.problems.push(`Its license (${lic || 'unknown'}) doesn’t let us play it freely. We take Public domain, CC0, CC BY and CC BY-SA.`);
    if (/-nc|-nd|noncommercial|noderiv/i.test(lic)) r.problems.push('“NC/ND” licenses aren’t allowed.');
    if (!r.artist) r.problems.push('It has no artist listed, so we can’t credit it.');
    if (r.duration > 900) r.problems.push('It’s over 15 minutes; pick a shorter track.');
    r.mp3 = ii.mime === 'audio/mpeg' ? ii.url.split('?')[0] : (p.videoinfo?.[0]?.derivatives || []).find(x => /audio\/mpeg/.test(x.type))?.src || '';
    if (!r.mp3) r.problems.push('Commons has no MP3 copy, so it won’t play in every browser.');
    return r;
  }
  async function query(extra) {
    const q = new URLSearchParams({ action: 'query', prop: 'imageinfo|videoinfo', iiprop: 'url|mime|size|extmetadata', iiextmetadatafilter: 'LicenseShortName|License|Artist', viprop: 'derivatives', format: 'json', origin: '*', ...extra });
    const d = await fetch(`${API}?${q}`).then(r => r.json());
    return Object.values(d.query?.pages || {}).map(judge);
  }
  /* the tracks in one style that pass, A–Z */
  const browse = genre => query({ generator: 'categorymembers', gcmtitle: `Category:${genre} music from Incompetech`, gcmtype: 'file', gcmlimit: '60' })
    .then(rows => rows.filter(r => !r.problems.length).sort((a, b) => a.title.localeCompare(b.title)));
  /* a pasted link -> { error } or the judged track */
  async function checkLink(link) {
    if (BLOCKED.test(link)) return { error: 'blocked' };
    const m = decodeURIComponent(link).match(/(?:File:|\/commons\/(?:transcoded\/)?[0-9a-f]\/[0-9a-f]{2}\/)([^/?#]+?\.(?:mp3|ogg|oga|flac|wav|opus))/i);
    if (!m) return { error: 'not-commons' };
    return (await query({ titles: 'File:' + m[1].replace(/_/g, ' ') }))[0];
  }
  window.CommonsMusic = { OK_LICENSE, GENRES, judge, query, browse, checkLink, mmss };
})();
