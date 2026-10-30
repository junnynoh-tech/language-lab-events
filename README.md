# UNG Language Lab events

Student pages for Language Lab events, built by the Language Lab Event Planner (`labs/event-generator.html` in TeachingOS).

| Page | URL path |
|---|---|
| Events carousel (all classes) | `/` → `visual/event-carousel.html` |
| Event details, rules, rubric | `visual/event-details.html?id=…` |
| Event Reflection sheet (any class) | `reflection/` |
| SPAN 1001 (Noh): events, sheet, announcement | `span1001/`, `span1001/event-reflection.html`, `span1001/extra-credit.html` |

How it all fits, step by step: `labs/EVENTS_WORKFLOW.md` (and the map `labs/events-workflow-map.html`) in TeachingOS.

| Other classes (no extra credit) | `spanish/` |

Data: `current/events.json` (+ `current/rubrics/`, `current/prizes/`). To update: export from the planner into the Lab Hub copy, then run `publish.sh` (it syncs `visual/`, `current/` and the flyers, builds the class pages from `labs/class-pages/`, and pushes). In D2L, add a **Link** topic to the page with **Open as External Resource** (opens in a new tab, no "allow" prompt).

No student data is stored here.
