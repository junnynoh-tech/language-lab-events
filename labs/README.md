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
