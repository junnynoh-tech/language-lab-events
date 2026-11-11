#!/usr/bin/env bash
# Publish the Language Lab events site to GitHub Pages.   bash labs/language-lab-events/publish.sh
# Since 2026-11-07 the website editor (Pages CMS) is where events, flyers, forms, tasks, competitions and music are edited.
# 1. pull GitHub's edits; sync_sources.py copies them back to the Lab Hub copy (stops if both sides changed)
# 2. student pages + rubrics + prizes + themes go out from this computer; library/ and flyers/ come back from GitHub
# 3. tidy_site.py: event codes by date (earliest = gvl-1), every flyer -> flyers/<code>.webp
# 4. music check, class pages, commit + push
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; LABS="$(dirname "$HERE")"; HUB="$LABS/lab-assistant-training-d2l/lab-hub/events"
[ -d "$HERE/.git" ] && { git -C "$HERE" pull -q --ff-only || { echo "GitHub has changes that conflict with this folder. Sort that out first."; exit 1; }; }
python3 "$HERE/sync_sources.py"
cp "$HUB/visual/event-carousel.html" "$HUB/visual/event-details.html" "$HERE/visual/"
cp "$HUB/current/events.json" "$HERE/current/"
mkdir -p "$HERE/current/rubrics"; cp "$HUB/current/rubrics/"*.json "$HERE/current/rubrics/" 2>/dev/null || true
cp "$LABS/class-pages/themes.json" "$HUB/current/themes.json"; cp "$LABS/class-pages/themes.json" "$HERE/current/themes.json"
mkdir -p "$HERE/current/prizes"; cp -n "$HUB/current/prizes/"* "$HERE/current/prizes/" 2>/dev/null || true
mkdir -p "$HERE/current/music"; cp -n "$HUB/current/music/"* "$HERE/current/music/" 2>/dev/null || true
python3 "$HERE/tidy_site.py"
# GitHub's copy is the source for these: bring them back to the Lab Hub (D2L) copy
cp "$HERE/current/events.json" "$HUB/current/events.json"
for d in library flyers prizes music; do rm -rf "$HUB/current/$d"; cp -r "$HERE/current/$d" "$HUB/current/$d"; done
if ! python3 "$LABS/check_music.py" "$HERE/current/events.json"; then
  [ -n "$SKIP_MUSIC_CHECK" ] || { echo "Fix the music above in the website editor's Music tab (or SKIP_MUSIC_CHECK=1 bash publish.sh)"; exit 1; }
fi
D2L_BEFORE="$(cd "$LABS/class-pages/out" 2>/dev/null && md5sum */*.html 2>/dev/null)"
python3 "$LABS/class-pages/build.py"
# files that live in D2L as uploaded copies don't update themselves (the GitHub-frame news items do): name the ones that changed
D2L_CHANGED="$(cd "$LABS/class-pages/out" && md5sum */*.html | grep -v -x -F "$D2L_BEFORE" | awk '{print $2}' | grep -v '/news-item.html$' || true)"
[ -n "$D2L_CHANGED" ] && { echo "Re-upload to D2L (changed): "; echo "$D2L_CHANGED" | sed 's|^|  labs/class-pages/out/|'; echo "  (or use the GitHub-frame news item, news-item.html, which updates by itself)"; }
cd "$HERE"
git add -A
git -c user.name="junnynoh-tech" -c user.email="junnynoh-tech@users.noreply.github.com" commit -q -m "Update events" || echo "Nothing new to publish."
git push -q
python3 "$HERE/sync_sources.py" --mark
echo "Live in about a minute: https://junnynoh-tech.github.io/language-lab-events/"
