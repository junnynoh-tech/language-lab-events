# Lab instructions (Student view)

The student pages for each course's labs: the LAB folder description, the announcement, Lab 0, the Guidelines Quiz and mini-quiz descriptions, and every lab page. Built from the files here into `../instructions/<course>/`.

**To change something:** Lab console › Student view › pick the course › **Edit**. Each part opens its own form in the website editor (Pages CMS): Requirements, Labs, Section types, Course settings, Policy. Save there. GitHub rebuilds the pages in about two minutes (`.github/workflows/labs.yml`).

| File | What it holds | Edited in |
|---|---|---|
| `registry.json` | Languages, courses, status, lab type, theme, due day and time | Student view (theme), editor › Labs · Courses |
| `types.json` | Lab types: Bongo video, TalkAbroad with workshops, Global Passport (planned) | here |
| `themes.json` | Page colors and header patterns, checked for contrast at build | editor › Labs · Themes |
| `shared/policy.json` | Policy every course shares | editor › Labs · Policy |
| `shared/lab-due-dates.json` | The Semester plan's export (Lab calendar › Share) | Student view › Due dates › Upload |
| `shared/campuses.json` | Each campus's Language Lab contact | here |
| `courses/<code>/course.json` | One course's instructions, in the editor's shape | editor › `<COURSE>` · … |
| `courses/<code>/vocab.json`, `quiz-facts.json` | Word lists; question counts and points only (no questions or answers) | here |
| `engine/` | Copy of TeachingOS `labs/lab-builder` (don't edit here) | `build_labs.py --sync-engine` |

Status `approved` courses are built; `proposal` courses (FREN 1002) only link to their proposal until the faculty approve them. To move one in: `python3 labs/build_labs.py --import <code> <TeachingOS source folder>`, set its status to `approved` in `registry.json`, and add it to a language in `registry.json`.

Nothing here is about students: no names, rosters or grades. Quiz questions and answer keys stay in D2L and TeachingOS.

## Editing on the page (console › Student view › a course › Edit)

The Edit tab shows the real student page, built in the browser by this same engine (Pyodide runs `preview.py` in a
worker). Text that comes from `course.json` or `shared/policy.json` is clickable: type over it, press Enter, and the
page rebuilds around it in about a second. Boxes (a tip, a question, a rule) get ↑ ↓ + ✕. Save commits only the
changed parts and stops if someone else changed the same part. Text from the shared policy shows a "Shared Lab
policy: every course changes" warning while you type.

Not clickable, by design: fixed wording from the engine, the due day and time (registry, faculty-approved), ids,
modes, links and pictures, and French quiz words. Those are in **All settings (forms)**.

`python3 labs/preview.py --test` proves the tagging changes nothing: a tagged build with the tags removed is
byte-for-byte the normal build, for every approved course. The GitHub Action runs it after each build. If a new
engine field breaks it, add the field name to `SKIP` in `preview.py`.
