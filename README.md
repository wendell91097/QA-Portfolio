# Wendell Lancaster — QA Portfolio & Game Design

**Live site:** https://wendell91097.github.io/QA-Portfolio/

QA tester, game developer, designer. Greater Boston Metro. Open to remote entry-level QA roles.

---

## What This Is

A self-maintained QA portfolio. Bug reports, case studies, and game design documents — all real, all mine, all pointing back at actual work rather than invented demos. The site is fully generated from structured data: editing any JSON file and running one script rebuilds the entire thing.

The game concepts section documents how I think before I build. Immortal Coil is the thesis statement. WordSmith is the proof.

---

## Repository Structure

```
/
├── bugs.json           # Bug report records
├── case_studies.json   # QA evaluation records
├── concepts.json       # Game design documents
├── updatedata.py       # Build script — generates index.html from all three JSON files
├── index.html          # Generated output — do not edit directly
└── README.md
```

---

## Data Schemas

### `bugs.json`

An array of bug report objects.

```json
{
  "id": "42",
  "game": "eldenring",
  "title": "Short description of the bug",
  "type": "animation",
  "type_display": "Animation / Model",
  "severity": "major",
  "description": "What is broken and why it matters.",
  "reproduction_steps": [
    "Step one",
    "Step two",
    "Step three"
  ],
  "tags": ["optional", "keyword", "tags"],
  "video_url": "https://youtu.be/XXXXXXXXXXX",
  "video_text": "Shown if no video URL is present"
}
```

**Valid `game` keys** are defined in `GAME_CONFIG` at the top of `updatedata.py`. Currently: `ds3`, `eldenring`, `fallout4`, `fallout76`, `spiderman`, `rdr1`, `rdr2`, `witcher3`, `wolf`, `cp77`, `gtav`, `dqxi`, `the_invincible`, `dave_diver`, `days_gone`. To add a new game, add an entry to `GAME_CONFIG` with a `label`, `css_class`, and `tier` (`"AAA"`, `"AA"`, or `"indie"`), plus a matching CSS rule in the `CSS` block.

**Valid `severity` values:** `critical`, `major`, `minor`, `visual`

**Valid `type` values:** `animation`, `ai`, `collision`, `physics`, `rendering`, `spawning`

---

### `case_studies.json`

An array of QA evaluation records.

```json
{
  "id": "CS-001",
  "game": "Game Title",
  "classification": "Category of evaluation",
  "title": "Full descriptive title",
  "scope": "What was tested.",
  "objective": "What the evaluation was trying to determine.",
  "executive_summary": "High-level overview of findings.",
  "findings": [
    {
      "category": "Finding category",
      "impact_area": "Where this affects the player experience",
      "risk_level": "High",
      "analysis": "Detailed breakdown of what was observed.",
      "forward_risk": "What happens if this goes unaddressed.",
      "recommendation": "What should be done about it."
    }
  ],
  "conclusion": "Final assessment.",
  "professional_statement": "Methodology note."
}
```

**Valid `risk_level` values:** `High`, `Moderate`, `Low`, `Low-Moderate`, `Strength`

`forward_risk` and `recommendation` are optional per finding. `Strength` findings document things working well.

---

### `concepts.json`

An array of game design documents. Each concept renders as an expandable card in the `// Game Concepts` tab.

```json
{
  "id": "gc-001",
  "index": "GC-001",
  "stage": "shipped",
  "animation_delay": 0.02,
  "title": "WordSmith",
  "subtitle": "Word Puzzle · Letter Grid · Pure Systems",
  "pitch": "The one-paragraph hook shown in the collapsed card header.",
  "links": [
    { "label": "▼ Play on itch.io", "url": "https://...", "primary": true },
    { "label": "▶ Gameplay Video", "url": "https://..." }
  ],
  "sections": [ ... ],
  "vibe": "The closing paragraph — design rationale and editorial voice."
}
```

**Valid `stage` values:** `shipped`, `prototype`, `specced`, `concept`

`links` is optional. Only shipped or playable concepts need it.

#### Section types

Each entry in `sections` has a `label`, a `type`, and type-specific fields. Sections render in a two-column grid by default; add `"full_width": true` to span both columns.

**`bullets`** — a simple bullet list:
```json
{
  "label": "Core Loop",
  "type": "bullets",
  "items": ["Point one.", "Point two."],
  "note": "Optional italic note rendered below the list."
}
```

**`cards`** — colored info cards in a grid:
```json
{
  "label": "Thematic DNA",
  "type": "cards",
  "columns": 1,
  "items": [
    { "label": "Card Title", "color": "red", "text": "Card body text." }
  ],
  "trailing_bullets": ["Optional bullets rendered below the card grid."],
  "note": "Optional italic note."
}
```

Valid `color` values: `blue`, `red`, `green`, `orange`, `purple`, `accent`, `white`, `spring`, `winter`

**`roster`** — a featured 2×2 card grid with a collapsible extended list below:
```json
{
  "label": "The Guests Who Matter Most",
  "type": "roster",
  "full_width": true,
  "featured": [
    { "label": "Character Name", "color": "red", "text": "Description." }
  ],
  "roster_label": "The Fuller Roster",
  "roster_items": ["Additional character or item descriptions."]
}
```

**`two_halves`** — two stacked cards with a note below (used for binary design splits):
```json
{
  "label": "The Two Halves",
  "type": "two_halves",
  "halves": [
    { "label": "Half One", "color": "green", "text": "Description." },
    { "label": "Half Two", "color": "accent", "text": "Description." }
  ],
  "note": "Italic note below both halves."
}
```

**`grid_rows`** — horizontal label + text rows, used for lists with strong visual labels (biomes, factions, etc.):
```json
{
  "label": "Biomes & Progression",
  "type": "grid_rows",
  "items": [
    { "label": "Home Forest", "color": "green", "text": "Short description." }
  ],
  "note": "Optional italic note."
}
```

**`companions`** — two-column layout for specialists vs. crew (or any named two-group companion list):
```json
{
  "label": "Animal Companions",
  "type": "companions",
  "full_width": true,
  "specialists_label": "Specialists — permanent, passive world changes",
  "specialists": [
    { "name": "Deer", "text": "Clears bramble." }
  ],
  "crew_label": "Crew — deployed daily",
  "crew": [
    { "name": "Rabbit", "text": "Watering." }
  ]
}
```

---

## Build Process

```bash
python updatedata.py
```

Reads `bugs.json`, `case_studies.json`, and `concepts.json` from the same directory. Generates the complete `index.html` — inline CSS, JS, sidebar filters, all card components.

**Do not hand-edit `index.html`.** It will be overwritten on the next build.

The stats bar values (hours tested, shipped title count) are hardcoded in `make_stats_bar()` and need manual updates.

---

## Notes for LLMs

- All frontend lives in `updatedata.py` as Python string templates. CSS, JS, and HTML are generated by a single script.
- `GAME_CONFIG`, `SEVERITY_CONFIG`, `TYPE_CONFIG`, `RISK_CONFIG`, `CONCEPT_STAGE_CONFIG`, and `COLOR_MAP` at the top of the file are the single source of truth for valid values. Sidebar filters and card styling are derived from these automatically.
- `make_concept_card()` is the entry point for rendering a concept. It delegates to `render_section()`, which dispatches on `section["type"]`. Adding a new section type means adding a branch in `render_section()` and nothing else.
- `make_video_embed()` handles both `youtube.com/watch?v=` and `youtu.be/` shortlinks. If no URL is present, it renders a placeholder using `video_text`.
- The filter JS is generated from the live dataset at build time. Valid keys are injected so client-side filtering is always in sync with the data.

---

## Contact

wendell91097@gmail.com · [sovereigndev.itch.io](https://sovereigndev.itch.io)
