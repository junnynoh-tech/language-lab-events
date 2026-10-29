#!/usr/bin/env bash
# Publish labs/language-lab-events to GitHub Pages (first time: creates the public repo).
# Run from the TeachingOS root:  bash labs/language-lab-events/publish.sh
set -e
cd "$(dirname "$0")"
GH=~/.local/bin/gh
if [ ! -d .git ]; then
  git init -q -b main
  git add -A
  git -c user.name="junnynoh-tech" -c user.email="junnynoh-tech@users.noreply.github.com" commit -q -m "Language Lab events: carousel, details, Event Reflection sheets, SPAN 1001 class page"
  $GH repo create junnynoh-tech/language-lab-events --public --source . --push --description "UNG Language Lab events: student pages and extra-credit handouts"
  $GH api -X POST repos/junnynoh-tech/language-lab-events/pages -f "source[branch]=main" -f "source[path]=/" >/dev/null
else
  git add -A
  git -c user.name="junnynoh-tech" -c user.email="junnynoh-tech@users.noreply.github.com" commit -q -m "Update events" || true
  git push -q
fi
echo "Live in about a minute: https://junnynoh-tech.github.io/language-lab-events/"
