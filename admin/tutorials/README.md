# Language Lab Tutorials hub

One page (`index.html`) for lab assistants and coordinators. It holds no content: it reads `tutorials.json` and the
tutorial files that file lists. **To swap a tutorial, replace its file.**

| File | What it is |
|---|---|
| `index.html` | The hub. Home = the "Can't solve it? Email" rule, the path every question takes, *Who does what* (built from every tutorial's `tasks`), and the tutorial cards. |
| `tutorials.json` | The list and order of tutorials, groups, roles, campus emails, the home flowchart. |
| `t/*.json` or `t/*.tex` | One tutorial each. |
| `templates/` | A JSON and a LaTeX starting point with every feature in use. |
| `sync_rubric.py` | Copies the speaking rubric from `labs/lab-builder/policy.json` into `t/grading.json`. Run after any rubric change. |
| `language-lab-tutorial-hub-v4.md` | The original draft the tutorials were rewritten from (kept for reference). |

## Add, swap or remove a tutorial
1. Copy `templates/tutorial-template.json` (or `.tex`) to `t/<id>.json`, write it.
2. Add `"t/<id>.json"` to `tutorials` in `tutorials.json` where it belongs in the order.
3. Removing one: take it out of that list. Replacing one: overwrite its file (same `id` keeps links working).

Try a file before you upload it: drag it onto the open hub. It replaces the tutorial with the same `id` (or is added)
for that session only.

## What a tutorial holds
- `roles`: who's involved, `student`, `la`, `lc`, `dept`. A tutorial whose roles are only `lc`/`dept` shows as
  *Coordinator only* to lab assistants.
- `tasks`: `{ "la": [...], "lc": [...], "dept": [...] }`, short lines. These build the home *Who does what* board.
- `flow` (optional): swimlanes. `lanes` is a list of roles; each node has `id`, `lane`, `type`
  (`start`, `step`, `decision`, `end`, `email`), `text`, `next` (ids, or `{ "to": id, "label": "Yes" }`) and an
  optional `go` (`"#section-id"` in this tutorial, or another tutorial's id). The hub draws it; nothing to lay out.
  Two placement hints when a lane gets busy: `"side": true` puts a node in a second column of its lane (good for
  a "No" branch), `"beside": true` keeps it on its parent's row (an arrow straight across).
  A Visio chart instead: in Visio, File > Save As > SVG, put it in `flows/`, and write
  `"flow": { "image": "flows/name.svg", "alt": "what it shows" }`.
- `sections`: each has `id`, `role` (`all` or a role), `title`, and any of `text`, `steps` (numbered), `list`,
  `table` (`head`, `rows`), `script` (what to say), `note`. Text takes `**bold**`, `*italic*`, `` `code` ``,
  `[text](link)`, and `{email}` (the chosen campus's Lab email), `{campus}`, `{dept}`.
- Sections for another role fold shut for whoever picked a role (I am: Assistant / Coordinator), so each person
  sees their own part first and still sees where the hand-off goes.

## Email replies (replies.json)

The hub's **Email replies** page (`#/replies`) reads `replies.json`, named by `"replies"` in `tutorials.json`. Each reply has `id`, `group`, `who` (`la` any lab assistant, `lc` coordinator only), `title`, `when` (the situation), `subject`, `body` (one string per paragraph; `\n` for line breaks, `- ` or `1. ` for lists), optional `note` (shown to staff, never copied) and `go` (a tutorial id, or `id/section`). `{email}` and `{campus}` fill from the campus picker; `[square brackets]` are blanks the sender fills in and are highlighted. The `signature` is added to every reply. **Copy reply** copies the subject and body as plain text. Link a reply from any tutorial with `[text](#/replies/<id>)`. Replies never ask for a 900 number, and they never advise on courses: that goes to the advisor or the department.

## Where it lives
- **D2L Lab Hub** (lab assistants + coordinators): upload this whole folder (`index.html`, `tutorials.json`, `t/`,
  plus `flows/` if used). Relative paths only, so a course copy keeps working.
- **Opened from this computer**: browsers block reading the neighbor files from a `file://` page, so the hub asks
  for the folder (**Open files…**, Edge/Chrome) or a drag of the folder.
- Not on the public GitHub site: tutorials describe internal accounts and admin steps.


**Home (2026-11-20).** This folder is the only copy: the Lab console's Tutorials tab, live at https://junnynoh-tech.github.io/language-lab-events/admin/tutorials/ . Lab assistants get that one link (D2L Lab Hub link, desk-computer bookmark). Edit here, or in the website editor (Pages CMS, **Tutorials** and **Email replies** tabs), which saves straight to GitHub; run `publish.sh` to pull those edits back. The site is public: the role switch only changes what's shown, so nothing here may hold student data or passwords. In the files, every flow `next` is `{to, label}` and table rows are `{cells: [...]}` so the editor can show them.
## Rules the content follows
- Email is the end point. Anything not settled on the spot (desk or phone) becomes an email to the campus Lab.
- Lab policy (rubric, late labs, excused absences) comes from `labs/lab-builder/policy.json`. Don't restate it
  differently here; run `sync_rubric.py` and edit `t/late-labs.json` in the same pass as any policy change.
- American English, no em dashes; run `scripts/prescreen.py` before uploading.
