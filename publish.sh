#!/usr/bin/env bash
# Publish the Language Lab events site to GitHub Pages.   bash labs/language-lab-events/publish.sh
# 1. sync: the student pages, events.json and rubrics from the Lab Hub copy (what the Event Generator exports),
#          and the flyers from labs/flyers-*/;  2. build every class page (labs/class-pages/build.py);  3. commit + push.
# First run only: creates the public repo junnynoh-tech/language-lab-events and turns on Pages.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; LABS="$(dirname "$HERE")"; HUB="$LABS/lab-assistant-training-d2l/lab-hub/events"
cp "$HUB/visual/event-carousel.html" "$HUB/visual/event-details.html" "$HERE/visual/"
cp "$HUB/current/events.json" "$HERE/current/"
mkdir -p "$HERE/current/rubrics"; cp "$HUB/current/rubrics/"*.json "$HERE/current/rubrics/" 2>/dev/null || true
cp "$LABS/class-pages/themes.json" "$HUB/current/themes.json"; cp "$LABS/class-pages/themes.json" "$HERE/current/themes.json"   # event backgrounds (one source: class-pages/themes.json)
mkdir -p "$HERE/current/prizes"; cp "$HUB/current/prizes/"* "$HERE/current/prizes/" 2>/dev/null || true
for f in "$LABS"/flyers-*/*.jpg; do [ -e "$f" ] && cp "$f" "$HERE/current/"; done
if ! python3 "$LABS/check_music.py" "$HUB/current/events.json"; then   # every event's YouTube links must still play
  [ -n "$SKIP_MUSIC_CHECK" ] || { echo "Fix the music links above in the Event Generator (or SKIP_MUSIC_CHECK=1 bash publish.sh)"; exit 1; }
fi
python3 "$LABS/class-pages/build.py"
cd "$HERE"
GH=~/.local/bin/gh
if [ ! -d .git ]; then
  git init -q -b main; git add -A
  git -c user.name="junnynoh-tech" -c user.email="junnynoh-tech@users.noreply.github.com" commit -q -m "Language Lab events site"
  $GH repo create junnynoh-tech/language-lab-events --public --source . --push --description "UNG Language Lab events: student pages and extra-credit handouts"
  $GH api -X POST repos/junnynoh-tech/language-lab-events/pages -f "source[branch]=main" -f "source[path]=/" >/dev/null
else
  git add -A
  git -c user.name="junnynoh-tech" -c user.email="junnynoh-tech@users.noreply.github.com" commit -q -m "Update events" || echo "Nothing new to publish."
  git push -q
fi
echo "Live in about a minute: https://junnynoh-tech.github.io/language-lab-events/"
