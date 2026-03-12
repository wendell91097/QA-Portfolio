import json
import os
import re
from collections import Counter
from html import escape


# ── GAME CONFIG ────────────────────────────────────────────────────────────────
# tier: "AAA" | "AA" | "indie"
GAME_CONFIG = {
    "ds3":            {"label": "Dark Souls III",           "css_class": "game-ds3",        "tier": "AAA"},
    "eldenring":      {"label": "Elden Ring",               "css_class": "game-eldenring",  "tier": "AAA"},
    "fallout4":       {"label": "Fallout 4",                "css_class": "game-fallout4",   "tier": "AAA"},
    "fallout76":      {"label": "Fallout 76",               "css_class": "game-fallout76",  "tier": "AAA"},
    "spiderman":      {"label": "Spider-Man Remastered",    "css_class": "game-spiderman",  "tier": "AAA"},
    "rdr1":           {"label": "RDR Remastered",           "css_class": "game-rdr1",       "tier": "AAA"},
    "rdr2":           {"label": "Red Dead Redemption 2",    "css_class": "game-rdr2",       "tier": "AAA"},
    "witcher3":       {"label": "The Witcher III",          "css_class": "game-witcher3",   "tier": "AAA"},
    "wolf":           {"label": "Wolfenstein II",           "css_class": "game-wolf",       "tier": "AAA"},
    "cp77":           {"label": "Cyberpunk 2077",           "css_class": "game-cp77",       "tier": "AAA"},
    "gtav":           {"label": "GTA V",                    "css_class": "game-gtav",       "tier": "AAA"},
    "dqxi":           {"label": "Dragon Quest XI",          "css_class": "game-dqxi",       "tier": "AAA"},
    "the_invincible": {"label": "The Invincible",           "css_class": "game-invincible", "tier": "AA"},
    "dave_diver":     {"label": "Dave the Diver",           "css_class": "game-dave-diver", "tier": "indie"},
    "days_gone":      {"label": "Days Gone",                "css_class": "game-days-gone",  "tier": "AAA"},
}

# ── SEVERITY CONFIG ────────────────────────────────────────────────────────────
SEVERITY_CONFIG = {
    "critical": {"label": "Critical", "css_class": "sev-critical", "dot_var": "--critical"},
    "major":    {"label": "Major",    "css_class": "sev-major",    "dot_var": "--major"},
    "minor":    {"label": "Minor",    "css_class": "sev-minor",    "dot_var": "--minor"},
    "visual":   {"label": "Visual",   "css_class": "sev-visual",   "dot_var": "--visual"},
}

# ── TYPE CONFIG ────────────────────────────────────────────────────────────────
TYPE_CONFIG = {
    "animation": {"label": "Animation / Model"},
    "ai":        {"label": "AI / Pathing"},
    "collision": {"label": "Collision / Physics"},
    "physics":   {"label": "Physics"},
    "rendering": {"label": "Rendering / LOD"},
    "spawning":  {"label": "Spawning / Placement"},
}

# ── RISK LEVEL CONFIG (Case Studies) ──────────────────────────────────────────
RISK_CONFIG = {
    "High":         {"css_class": "risk-high"},
    "Moderate":     {"css_class": "risk-moderate"},
    "Low":          {"css_class": "risk-low"},
    "Low-Moderate": {"css_class": "risk-low-moderate"},
    "Strength":     {"css_class": "risk-strength"},
}


# ── CONCEPT STAGE CONFIG ──────────────────────────────────────────────────────
CONCEPT_STAGE_CONFIG = {
    "shipped":   {"label": "Shipped",         "css_class": "gc-stage-shipped"},
    "prototype": {"label": "Prototype-Ready", "css_class": "gc-stage-prototype"},
    "specced":   {"label": "Specced",         "css_class": "gc-stage-specced"},
    "concept":   {"label": "Concept",         "css_class": "gc-stage-concept"},
}

# ── COLOR MAP (for concept section cards) ─────────────────────────────────────
COLOR_MAP = {
    "blue":   {"bg": "rgba(77,171,247,0.07)",   "border": "rgba(77,171,247,0.2)",   "color": "var(--blue)"},
    "red":    {"bg": "rgba(255,77,77,0.07)",    "border": "rgba(255,77,77,0.2)",    "color": "var(--red)"},
    "green":  {"bg": "rgba(6,214,160,0.07)",    "border": "rgba(6,214,160,0.2)",    "color": "var(--green)"},
    "orange": {"bg": "rgba(255,140,66,0.07)",   "border": "rgba(255,140,66,0.2)",   "color": "var(--orange)"},
    "purple": {"bg": "rgba(180,100,255,0.07)",  "border": "rgba(180,100,255,0.2)",  "color": "#c87fff"},
    "accent": {"bg": "rgba(232,255,71,0.05)",   "border": "rgba(232,255,71,0.15)",  "color": "var(--accent)"},
    "white":  {"bg": "rgba(220,220,220,0.05)",  "border": "rgba(220,220,220,0.2)",  "color": "#d0d0d0"},
    "spring": {"bg": "rgba(255,180,200,0.07)",  "border": "rgba(255,180,200,0.25)", "color": "#ffb0c8"},
    "winter": {"bg": "rgba(160,200,255,0.06)",  "border": "rgba(160,200,255,0.18)", "color": "#a0c8ff"},
}


# ── HTML GENERATORS — BUG REPORTS ─────────────────────────────────────────────

def make_video_embed(bug: dict) -> str:
    url  = bug.get("video_url", "").strip()
    text = bug.get("video_text", "").strip()

    if url:
        embed_url = url
        if "youtube.com/watch?v=" in url:
            vid_id    = url.split("watch?v=")[-1].split("&")[0]
            embed_url = f"https://www.youtube.com/embed/{vid_id}"
        elif "youtu.be/" in url:
            vid_id    = url.split("youtu.be/")[-1].split("?")[0]
            embed_url = f"https://www.youtube.com/embed/{vid_id}"

        return f"""
          <div class="video-wrapper">
            <iframe
              src="{escape(embed_url)}"
              title="Bug clip #{escape(bug['id'])}"
              frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowfullscreen>
            </iframe>
          </div>"""

    # No URL — show status note as plain text, or generic pending message
    placeholder_body = text if text else "Clip pending upload"
    return f"""
          <div class="video-placeholder">
            <div class="video-icon">&#9654;</div>
            <span style="color:var(--text-dim); font-size:11px; line-height:1.7; text-align:center; max-width:320px;">{escape(placeholder_body)}</span>
          </div>"""


def make_repro_steps(steps: list) -> str:
    items = ""
    for i, step in enumerate(steps, 1):
        num    = str(i).zfill(2)
        items += f"""
                <li class="repro-step">
                  <span class="step-num">{num}</span>
                  <span>{escape(step)}</span>
                </li>"""
    return f'<ul class="repro-steps">{items}\n              </ul>'


def make_tags(tags: list) -> str:
    chips = "".join(f'<span class="chip">{escape(t)}</span>' for t in tags)
    return f'<div class="detail-chips" style="margin-top:12px">{chips}</div>'


def make_bug_card(bug: dict) -> str:
    game_key   = bug.get("game", "unknown")
    game_cfg   = GAME_CONFIG.get(game_key, {"label": bug.get("game_name", game_key), "css_class": "game-default"})
    sev_key    = bug.get("severity", "minor")
    sev_cfg    = SEVERITY_CONFIG.get(sev_key, {"label": sev_key.title(), "css_class": "sev-minor"})
    type_key   = bug.get("type", "")
    anim_delay = (int(bug.get("id", "1")) % 8 + 1) * 0.05

    return f"""
      <div class="bug-card" data-game="{escape(game_key)}" data-severity="{escape(sev_key)}" data-type="{escape(type_key)}" onclick="toggleCard(this)" style="animation-delay:{anim_delay:.2f}s">
        <div class="bug-card-header">
          <div class="bug-id">#{escape(bug['id'])}</div>
          <div class="game-tag {game_cfg['css_class']}">{escape(game_cfg['label'])}</div>
          <div class="bug-title-text">{escape(bug.get('title', ''))}</div>
          <div class="bug-type">{escape(bug.get('type_display', type_key.title()))}</div>
          <div class="severity-badge {sev_cfg['css_class']}">{sev_cfg['label']}</div>
        </div>
        <div class="bug-detail">
          <div class="detail-grid">
            <div>
              <div class="detail-section-title">Description</div>
              <p class="detail-text">{escape(bug.get('description', ''))}</p>
              {make_tags(bug.get('tags', []))}
            </div>
            <div>
              <div class="detail-section-title">Reproduction Steps</div>
              {make_repro_steps(bug.get('reproduction_steps', []))}
            </div>
          </div>
          <div class="detail-section-title">Clip</div>
          {make_video_embed(bug)}
        </div>
      </div>"""


# ── HTML GENERATORS — CASE STUDIES ────────────────────────────────────────────

def make_bullet_list(text: str) -> str:
    if not text or not text.strip():
        return '<ul class="finding-bullets"></ul>'
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    items     = "".join(f"<li>{s}</li>" for s in sentences)
    return f'<ul class="finding-bullets">{items}</ul>'


def make_finding_row(finding: dict) -> str:
    risk     = finding.get("risk_level", "Low")
    risk_cfg = RISK_CONFIG.get(risk, {"css_class": "risk-low"})
    rec_html = ""
    if finding.get("recommendation"):
        rec_html = f"""
                    <div style="margin-top:12px">
                      <div class="finding-label">Recommendation</div>
                      {make_bullet_list(finding.get('recommendation', ''))}
                    </div>"""
    fwd_risk_html = ""
    if finding.get("forward_risk"):
        fwd_risk_html = f"""
                  <div class="finding-col">
                    <div class="finding-label">Forward Risk</div>
                    {make_bullet_list(finding.get('forward_risk', ''))}
                    {rec_html}
                  </div>"""
    else:
        fwd_risk_html = f"""
                  <div class="finding-col">
                    {rec_html}
                  </div>"""

    return f"""
              <div class="finding-row" onclick="event.stopPropagation(); this.classList.toggle('finding-expanded')">
                <div class="finding-header">
                  <span class="finding-category">{escape(finding.get('category', ''))}</span>
                  <span class="finding-impact">{escape(finding.get('impact_area', ''))}</span>
                  <span class="risk-badge {risk_cfg['css_class']}">{escape(risk)}</span>
                </div>
                <div class="finding-body">
                  <div class="finding-col">
                    <div class="finding-label">Analysis</div>
                    {make_bullet_list(finding.get('analysis', ''))}
                  </div>{fwd_risk_html}
                </div>
              </div>"""


def make_case_study_card(cs: dict) -> str:
    cs_id          = cs.get("id", "")
    findings       = cs.get("findings", [])
    findings_html  = "".join(make_finding_row(f) for f in findings)
    high_count     = sum(1 for f in findings if f.get("risk_level") == "High")
    mod_count      = sum(1 for f in findings if f.get("risk_level") == "Moderate")
    strength_count = sum(1 for f in findings if f.get("risk_level") == "Strength")

    strength_badge = ""
    if strength_count:
        strength_badge = f'<span class="risk-badge risk-strength">{strength_count} Strength</span>'

    card_id = f' id="{escape(cs_id.lower())}"' if cs_id else ""

    return f"""
      <div class="cs-card"{card_id} onclick="toggleCsCard(this)">
        <div class="cs-card-header">
          <div class="bug-id">{escape(cs_id)}</div>
          <div class="cs-classification">{escape(cs.get('classification', ''))}</div>
          <div class="cs-title">{escape(cs.get('title', ''))}</div>
          <div class="cs-meta">
            <span class="risk-badge risk-high">{high_count} High</span>
            <span class="risk-badge risk-moderate">{mod_count} Moderate</span>
            {strength_badge}
          </div>
        </div>
        <div class="cs-detail">
          <div class="cs-meta-grid">
            <div class="cs-meta-item">
              <div class="finding-label">Scope</div>
              <p class="detail-text">{escape(cs.get('scope', ''))}</p>
            </div>
            <div class="cs-meta-item">
              <div class="finding-label">Objective</div>
              <p class="detail-text">{escape(cs.get('objective', ''))}</p>
            </div>
          </div>

          <div class="detail-section-title" style="margin-top:20px">Executive Summary</div>
          <p class="detail-text" style="margin-bottom:20px">{escape(cs.get('executive_summary', ''))}</p>

          <div class="detail-section-title">Findings</div>
          <div class="findings-list">
{findings_html}
          </div>

          <div class="cs-footer-grid">
            <div>
              <div class="finding-label" style="margin-top:20px">Conclusion</div>
              <p class="detail-text">{escape(cs.get('conclusion', ''))}</p>
            </div>
            <div>
              <div class="finding-label" style="margin-top:20px">Methodology Note</div>
              <p class="detail-text" style="font-style:italic; color:var(--text-dim)">{escape(cs.get('professional_statement', ''))}</p>
            </div>
          </div>
        </div>
      </div>"""


# ── HTML GENERATORS — GAME CONCEPTS ───────────────────────────────────────────

def _card_html(item: dict) -> str:
    """Render a single colored card for concept sections."""
    col = COLOR_MAP.get(item.get("color", "blue"), COLOR_MAP["blue"])
    return (
        f'<div style="background:{col["bg"]}; border:1px solid {col["border"]}; '
        f'border-radius:4px; padding:10px 12px;">'
        f'<div style="font-size:10px; font-weight:700; color:{col["color"]}; '
        f'text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">'
        f'{escape(item["label"])}</div>'
        f'<p style="font-size:12px; color:var(--text-mid); line-height:1.7;">'
        f'{escape(item["text"])}</p></div>'
    )


def render_section(section: dict) -> str:
    s_type = section.get("type", "bullets")
    full_w = section.get("full_width", False)
    span   = ' style="grid-column: 1 / -1"' if full_w else ""
    label  = f'<div class="finding-label">{escape(section["label"])}</div>'

    if s_type == "bullets":
        items = "".join(f"<li>{escape(i)}</li>" for i in section.get("items", []))
        note  = (
            f'<p style="font-size:11px; color:var(--text-dim); line-height:1.7; '
            f'margin-top:10px; font-style:italic;">{escape(section["note"])}</p>'
            if section.get("note") else ""
        )
        body = f'<ul class="finding-bullets">{items}</ul>{note}'

    elif s_type == "cards":
        cols       = section.get("columns", 2)
        cards_html = "".join(_card_html(i) for i in section.get("items", []))
        if cols == 1:
            container = (
                f'<div style="display:flex; flex-direction:column; gap:8px; '
                f'margin-top:4px;">{cards_html}</div>'
            )
        else:
            col_css   = " ".join(["1fr"] * cols)
            container = (
                f'<div style="display:grid; grid-template-columns:{col_css}; '
                f'gap:8px; margin-top:4px;">{cards_html}</div>'
            )
        trailing = ""
        if section.get("trailing_bullets"):
            t_items  = "".join(f"<li>{escape(b)}</li>" for b in section["trailing_bullets"])
            trailing = f'<ul class="finding-bullets" style="margin-top:10px;">{t_items}</ul>'
        note = (
            f'<p style="font-size:11px; color:var(--text-dim); line-height:1.7; '
            f'margin-top:10px; font-style:italic;">{escape(section["note"])}</p>'
            if section.get("note") else ""
        )
        body = container + trailing + note

    elif s_type == "roster":
        featured_html = "".join(_card_html(i) for i in section.get("featured", []))
        featured_grid = (
            f'<div style="display:grid; grid-template-columns:1fr 1fr; '
            f'gap:8px; margin-top:4px;">{featured_html}</div>'
        )
        roster_items_html = "".join(f"<li>{escape(r)}</li>" for r in section.get("roster_items", []))
        roster_ul    = f'<ul class="finding-bullets">{roster_items_html}</ul>'
        rl           = escape(section.get("roster_label", "The Fuller Roster"))
        roster_block = (
            f'<div style="margin-top:8px;">'
            f'<div class="finding-label" style="margin-bottom:6px;">{rl} '
            f'<button class="gc-roster-toggle" '
            f'onclick="event.stopPropagation(); toggleRoster(this)" '
            f'aria-expanded="false">&#9658; show</button></div>'
            f'<div class="gc-roster-body" style="display:none">{roster_ul}</div>'
            f'</div>'
        )
        body = featured_grid + roster_block

    elif s_type == "two_halves":
        halves_html = "".join(_card_html(h) for h in section.get("halves", []))
        stacked = (
            f'<div style="display:flex; flex-direction:column; gap:10px; '
            f'margin-top:4px;">{halves_html}</div>'
        )
        note = (
            f'<p style="font-size:11px; color:var(--text-dim); line-height:1.7; '
            f'font-style:italic; padding-left:2px;">{escape(section["note"])}</p>'
            if section.get("note") else ""
        )
        body = stacked + note

    elif s_type == "grid_rows":
        rows = ""
        for item in section.get("items", []):
            col   = COLOR_MAP.get(item.get("color", "green"), COLOR_MAP["green"])
            rows += (
                f'<div style="background:{col["bg"]}; border:1px solid {col["border"]}; '
                f'border-radius:4px; padding:8px 12px; display:flex; '
                f'align-items:baseline; gap:10px;">'
                f'<div style="font-size:10px; font-weight:700; color:{col["color"]}; '
                f'text-transform:uppercase; letter-spacing:0.1em; white-space:nowrap; '
                f'min-width:110px;">{escape(item["label"])}</div>'
                f'<p style="font-size:11px; color:var(--text-mid); line-height:1.5; '
                f'margin:0;">{escape(item["text"])}</p></div>'
            )
        note = (
            f'<p style="font-size:11px; color:var(--text-dim); line-height:1.7; '
            f'margin-top:10px; font-style:italic;">{escape(section["note"])}</p>'
            if section.get("note") else ""
        )
        body = (
            f'<div style="display:flex; flex-direction:column; gap:6px; '
            f'margin-top:4px;">{rows}</div>'
        ) + note

    elif s_type == "companions":
        spec_label = escape(section.get("specialists_label", "Specialists"))
        crew_label = escape(section.get("crew_label", "Crew"))
        spec_items = "".join(
            f'<li><strong>{escape(s["name"])}</strong>'
            f'<div style="padding-left:10px; margin-top:2px; color:var(--text-dim); '
            f'font-size:11px; line-height:1.6;">{escape(s["text"])}</div></li>'
            for s in section.get("specialists", [])
        )
        crew_items = "".join(
            f'<li><strong>{escape(c["name"])}</strong>'
            f'<div style="padding-left:10px; margin-top:2px; color:var(--text-dim); '
            f'font-size:11px; line-height:1.6;">{escape(c["text"])}</div></li>'
            for c in section.get("crew", [])
        )
        body = (
            f'<div style="display:grid; grid-template-columns:1fr 1fr; '
            f'gap:16px; margin-top:4px;">'
            f'<div><div class="finding-label" style="margin-bottom:6px; font-size:8px;">'
            f'{spec_label}</div>'
            f'<ul class="finding-bullets">{spec_items}</ul></div>'
            f'<div><div class="finding-label" style="margin-bottom:6px; font-size:8px;">'
            f'{crew_label}</div>'
            f'<ul class="finding-bullets">{crew_items}</ul></div>'
            f'</div>'
        )

    else:
        body = ""

    return f'<div class="gc-doc-section"{span}>{label}{body}</div>'


def make_concept_card(concept: dict) -> str:
    concept_id = concept["id"]
    index      = concept["index"]
    stage      = concept["stage"]
    title      = concept["title"]
    subtitle   = concept["subtitle"]
    pitch      = concept["pitch"]
    vibe       = concept["vibe"]
    delay      = concept.get("animation_delay", 0.05)
    stage_cfg  = CONCEPT_STAGE_CONFIG.get(stage, {"label": stage.title(), "css_class": "gc-stage-concept"})

    links_html = ""
    if concept.get("links"):
        links_inner = ""
        for lnk in concept["links"]:
            prim_cls    = " gc-link-primary" if lnk.get("primary") else ""
            links_inner += (
                f'<a class="gc-link-btn{prim_cls}" href="{escape(lnk["url"])}" '
                f'target="_blank" onclick="event.stopPropagation()">'
                f'{escape(lnk["label"])}</a>'
            )
        links_html = f'<div class="gc-links">{links_inner}</div>'

    sections_html = "\n".join(render_section(s) for s in concept.get("sections", []))

    return f"""
      <div class="gc-doc" id="{escape(concept_id)}" data-stage="{escape(stage)}" onclick="toggleGcCard(this)" style="animation-delay:{delay:.2f}s">
        <div class="gc-doc-header">
          <div class="gc-doc-col-id"><div class="gc-index">{escape(index)}</div><div class="gc-expand-hint">&#9658; expand</div></div>
          <div class="gc-doc-col-main"><div class="gc-title">{escape(title)}</div><div class="gc-subtitle">{escape(subtitle)}</div></div>
          <div class="gc-doc-col-meta"><span class="gc-stage-badge {stage_cfg['css_class']}">{escape(stage_cfg['label'])}</span></div>
        </div>
        <div class="gc-doc-body">
          <div class="gc-doc-pitch">{escape(pitch)}</div>
          {links_html}
          <div class="gc-doc-grid">
{sections_html}
          </div>
          <div class="gc-vibe">{escape(vibe)}</div>
        </div>
      </div>"""


# ── HTML GENERATORS — SIDEBAR ──────────────────────────────────────────────────

def make_sidebar_html(bugs: list, case_studies: list, concepts: list) -> str:
    game_counts = Counter(b["game"] for b in bugs)
    sev_counts  = Counter(b["severity"] for b in bugs)
    type_counts = Counter(b["type"] for b in bugs)
    total       = len(bugs)

    # Bug filters — game
    game_btns = ""
    for game_key, cfg in GAME_CONFIG.items():
        count = game_counts.get(game_key, 0)
        if count == 0:
            continue
        game_btns += f"""
        <button class="filter-btn" onclick="filterBugs('{game_key}', this)">
          <span>{escape(cfg['label'])}</span>
          <span class="filter-count">{count}</span>
        </button>"""

    # Bug filters — severity
    sev_btns = ""
    for sev_key, cfg in SEVERITY_CONFIG.items():
        count = sev_counts.get(sev_key, 0)
        if count == 0:
            continue
        sev_btns += f"""
        <button class="filter-btn" onclick="filterBugs('{sev_key}', this)">
          <span><span class="severity-dot" style="background:var({cfg['dot_var']})"></span>{cfg['label']}</span>
          <span class="filter-count">{count}</span>
        </button>"""

    # Bug filters — type
    type_btns = ""
    for type_key, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        label     = TYPE_CONFIG.get(type_key, {}).get("label", type_key.title())
        type_btns += f"""
        <button class="filter-btn" onclick="filterBugs('{type_key}', this)">
          {escape(label)}
          <span class="filter-count">{count}</span>
        </button>"""

    # Concepts sidebar — stage filters + jump links
    stage_counts_c = Counter(c["stage"] for c in concepts)
    total_c        = len(concepts)

    stage_btns = ""
    for stage_key in ["shipped", "prototype", "specced", "concept"]:
        count = stage_counts_c.get(stage_key, 0)
        if count == 0:
            continue
        cfg        = CONCEPT_STAGE_CONFIG[stage_key]
        stage_btns += f"""
        <button class="filter-btn" onclick="filterConcepts('{stage_key}', this)">
          {escape(cfg['label'])} <span class="filter-count">{count}</span>
        </button>"""

    concept_jumps = ""
    for c in concepts:
        concept_jumps += f"""
        <button class="filter-btn" onclick="jumpTo('{escape(c['id'])}')">{escape(c['title'])}</button>"""

    # Case studies — jump links + aggregate risk summary
    cs_jump_btns = ""
    for cs in case_studies:
        cs_id    = cs.get("id", "")
        cs_game  = cs.get("game", cs.get("title", cs_id))
        cs_jump_btns += f"""
        <button class="filter-btn" onclick="jumpTo('{escape(cs_id.lower())}')">{escape(cs_id)} &mdash; {escape(cs_game)}</button>"""

    all_findings   = [f for cs in case_studies for f in cs.get("findings", [])]
    agg_high       = sum(1 for f in all_findings if f.get("risk_level") == "High")
    agg_mod        = sum(1 for f in all_findings if f.get("risk_level") == "Moderate")
    agg_strength   = sum(1 for f in all_findings if f.get("risk_level") == "Strength")

    cs_risk_summary = f"""
      <div class="sidebar-section">
        <div class="sidebar-label">Risk Summary</div>
        <div style="padding:4px 0; display:flex; flex-direction:column; gap:6px;">
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px;">
            <span style="color:var(--text-dim)">High Risk</span>
            <span class="risk-badge risk-high" style="font-size:9px; padding:2px 7px;">{agg_high}</span>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px;">
            <span style="color:var(--text-dim)">Moderate Risk</span>
            <span class="risk-badge risk-moderate" style="font-size:9px; padding:2px 7px;">{agg_mod}</span>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:11px;">
            <span style="color:var(--text-dim)">Strength</span>
            <span class="risk-badge risk-strength" style="font-size:9px; padding:2px 7px;">{agg_strength}</span>
          </div>
        </div>
      </div>""" if case_studies else ""

    return f"""  <aside class="sidebar">

    <!-- BUG REPORTS SIDEBAR -->
    <div class="sidebar-panel" id="sidebar-bugs">
      <div class="sidebar-section">
        <div class="sidebar-label">Filter by Game</div>
        <button class="filter-btn active" onclick="filterBugs('all', this)">
          All Bugs <span class="filter-count">{total}</span>
        </button>{game_btns}
      </div>

      <div class="sidebar-section">
        <div class="sidebar-label">Filter by Severity</div>{sev_btns}
      </div>

      <div class="sidebar-section">
        <div class="sidebar-label">Filter by Type</div>{type_btns}
      </div>
    </div>

    <!-- GAME CONCEPTS SIDEBAR -->
    <div class="sidebar-panel hidden" id="sidebar-game-concepts">
      <div class="sidebar-section">
        <div class="sidebar-label">Filter by Stage</div>
        <button class="filter-btn active" onclick="filterConcepts('all', this)">
          All Concepts <span class="filter-count">{total_c}</span>
        </button>{stage_btns}
      </div>
      <div class="sidebar-section">
        <div class="sidebar-label">Jump To</div>{concept_jumps}
      </div>
    </div>

    <!-- CASE STUDIES SIDEBAR -->
    <div class="sidebar-panel hidden" id="sidebar-case-studies">
      <div class="sidebar-section">
        <div class="sidebar-label">Evaluations</div>{cs_jump_btns}
      </div>
      {cs_risk_summary}
    </div>

  </aside>"""


def make_stats_bar(bugs: list) -> str:
    total_bugs   = len(bugs)
    total_titles = len({b["game"] for b in bugs})

    return f"""<div class="stats-bar">
  <div class="stat-item">
    <div class="stat-value">{total_bugs}</div>
    <div class="stat-label">Documented Bugs</div>
  </div>
  <div class="stat-item">
    <div class="stat-value">{total_titles}</div>
    <div class="stat-label">Titles Tested</div>
  </div>
  <div class="stat-item">
    <div class="stat-value">1,300+</div>
    <div class="stat-label">Hrs User Testing</div>
  </div>
  <div class="stat-item">
    <a href="https://sovereigndev.itch.io/wordsmith" target="_blank" style="text-decoration:none; color:inherit; display:contents;">
      <div class="stat-value" style="cursor:pointer;">1</div>
      <div class="stat-label" style="cursor:pointer; text-decoration:underline; text-decoration-color:rgba(232,255,71,0.4);">Shipped Title</div>
    </a>
  </div>
  <div class="open-to-work">
    <span class="status-dot"></span>
    Available &mdash; Remote
  </div>
</div>"""


def make_filter_js(bugs: list) -> str:
    game_keys = list(set(b["game"] for b in bugs))
    sev_keys  = list(SEVERITY_CONFIG.keys())
    type_keys = list(set(b["type"] for b in bugs))

    game_list = json.dumps(game_keys)
    sev_list  = json.dumps(sev_keys)
    type_list = json.dumps(type_keys)

    return f"""
  function toggleCard(card) {{
    if (event.target.closest('.bug-detail')) return;
    const wasExpanded = card.classList.contains('expanded');
    document.querySelectorAll('.bug-card').forEach(c => c.classList.remove('expanded'));
    if (!wasExpanded) card.classList.add('expanded');
  }}

  function toggleCsCard(card) {{
    if (event.target.closest('.cs-detail')) return;
    const wasExpanded = card.classList.contains('expanded');
    document.querySelectorAll('.cs-card').forEach(c => c.classList.remove('expanded'));
    if (!wasExpanded) card.classList.add('expanded');
  }}

  function filterBugs(filter, btn) {{
    document.querySelectorAll('#sidebar-bugs .filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const gameKeys = {game_list};
    const sevKeys  = {sev_list};
    const typeKeys = {type_list};

    const cards = document.querySelectorAll('.bug-card');
    let visible = 0;

    cards.forEach(card => {{
      const game     = card.dataset.game;
      const severity = card.dataset.severity;
      const type     = card.dataset.type;

      let show = false;
      if (filter === 'all')               show = true;
      else if (gameKeys.includes(filter)) show = game === filter;
      else if (sevKeys.includes(filter))  show = severity === filter;
      else if (typeKeys.includes(filter)) show = type === filter;

      card.classList.toggle('hidden', !show);
      if (show) visible++;
    }});

    document.getElementById('count').textContent = visible;
  }}

  function toggleGcCard(card) {{
    if (event.target.closest('.gc-doc-body')) return;
    const wasExpanded = card.classList.contains('gc-expanded');
    document.querySelectorAll('.gc-doc').forEach(c => c.classList.remove('gc-expanded'));
    if (!wasExpanded) card.classList.add('gc-expanded');
  }}

  function filterConcepts(stage, btn) {{
    document.querySelectorAll('#sidebar-game-concepts .filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.gc-doc').forEach(card => {{
      const show = stage === 'all' || card.dataset.stage === stage;
      card.classList.toggle('hidden', !show);
    }});
  }}

  function jumpTo(id) {{
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }}

  function toggleRoster(btn) {{
    const body = btn.closest('.gc-doc-section').querySelector('.gc-roster-body');
    if (!body) return;
    const open = body.style.display !== 'none';
    body.style.display = open ? 'none' : 'block';
    btn.setAttribute('aria-expanded', String(!open));
    btn.textContent = (!open ? '&#9660; hide' : '&#9658; show');
    btn.innerHTML   = !open ? '&#9660; hide' : '&#9658; show';
  }}

  function switchTab(tab) {{
    document.querySelectorAll('.tab-btn').forEach(b => {{
      b.classList.toggle('active', b.dataset.tab === tab);
    }});
    document.querySelectorAll('.tab-panel').forEach(p => {{
      p.classList.toggle('hidden', p.id !== 'panel-' + tab);
    }});
    document.querySelectorAll('.sidebar-panel').forEach(p => p.classList.add('hidden'));
    const sp = document.getElementById('sidebar-' + tab);
    if (sp) sp.classList.remove('hidden');
  }}
"""


# ── CSS BLOCK ──────────────────────────────────────────────────────────────────
CSS = """
  :root {
    --bg: #0a0b0d;
    --bg2: #0f1114;
    --bg3: #151719;
    --panel: #1a1d21;
    --border: #2a2d32;
    --border-bright: #3a3d44;
    --text: #e2e4e8;
    --text-dim: #6b7280;
    --text-mid: #c4c8d0;
    --accent: #e8ff47;
    --accent-dim: rgba(232, 255, 71, 0.12);
    --accent-glow: rgba(232, 255, 71, 0.04);
    --red: #ff4d4d;
    --orange: #ff8c42;
    --yellow: #ffd166;
    --green: #06d6a0;
    --blue: #4dabf7;
    --critical: #ff4d4d;
    --major: #ff8c42;
    --minor: #ffd166;
    --visual: #4dabf7;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'JetBrains Mono', monospace;
    min-height: 100vh;
    overflow-x: hidden;
  }

  body::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: repeating-linear-gradient(
      0deg, transparent, transparent 2px,
      rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 1000;
  }

  /* HEADER */
  header {
    border-bottom: 1px solid var(--border);
    padding: 0 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 60px;
    position: sticky;
    top: 0;
    background: rgba(10, 11, 13, 0.95);
    backdrop-filter: blur(12px);
    z-index: 100;
  }
  .header-left { display: flex; align-items: center; gap: 20px; }
  .logo-mark {
    width: 28px; height: 28px;
    border: 2px solid var(--accent);
    display: flex; align-items: center; justify-content: center;
    font-size: 11px; font-weight: 700;
    color: var(--accent); letter-spacing: -0.5px;
  }
  .header-name {
    font-family: 'Syne', sans-serif;
    font-weight: 800; font-size: 14px;
    letter-spacing: 0.05em; color: var(--text);
  }
  .header-role {
    font-size: 11px; color: var(--text-dim);
    border-left: 1px solid var(--border); padding-left: 20px;
  }
  .header-right { display: flex; align-items: center; gap: 24px; }
  .header-contact {
    font-size: 11px; color: var(--text-dim);
    text-decoration: none; transition: color 0.2s;
  }
  .header-contact:hover { color: var(--accent); }
  .status-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: var(--green); box-shadow: 0 0 8px var(--green);
    animation: pulse 2s infinite; display: inline-block; margin-right: 6px;
  }
  @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

  /* STATS BAR */
  .stats-bar {
    border-bottom: 1px solid var(--border);
    padding: 0 40px; display: flex; align-items: stretch;
    height: 80px; background: var(--bg2);
  }
  .stat-item {
    display: flex; flex-direction: column; justify-content: center;
    padding: 0 32px 0 0; margin-right: 32px;
    border-right: 1px solid var(--border);
    align-items: flex-start;
  }
  .stat-item:last-child { border-right: none; }
  .stat-value {
    font-family: 'Syne', sans-serif;
    font-weight: 800; font-size: 26px; color: var(--accent); line-height: 1;
    font-variant-numeric: lining-nums tabular-nums;
    font-feature-settings: "lnum" 1, "tnum" 1;
  }
  .stat-label {
    font-size: 10px; color: var(--text-dim);
    text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px;
  }
  .open-to-work {
    margin-left: auto; display: flex; align-items: center; gap: 8px;
    font-size: 11px; color: var(--green); font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase;
  }

  /* LAYOUT */
  .main {
    display: grid;
    grid-template-columns: 220px 1fr;
    min-height: calc(100vh - 140px);
  }

  /* SIDEBAR */
  .sidebar {
    border-right: 1px solid var(--border);
    padding: 24px 0;
    position: sticky; top: 60px;
    height: calc(100vh - 140px);
    overflow-y: auto; background: var(--bg2);
  }
  .sidebar-section { padding: 0 20px; margin-bottom: 28px; }
  .sidebar-label {
    font-size: 9px; text-transform: uppercase;
    letter-spacing: 0.15em; color: var(--text-dim);
    margin-bottom: 10px; padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }
  .filter-btn {
    display: flex; align-items: center; justify-content: space-between;
    width: 100%; padding: 7px 10px;
    background: none; border: none; border-radius: 4px;
    color: var(--text-mid); font-family: 'JetBrains Mono', monospace;
    font-size: 12px; cursor: pointer; transition: all 0.15s;
    text-align: left; margin-bottom: 2px;
  }
  .filter-btn:hover { background: var(--panel); color: var(--text); }
  .filter-btn.active { background: var(--accent-dim); color: var(--accent); }
  .filter-count {
    font-size: 10px; background: var(--panel);
    padding: 2px 6px; border-radius: 10px; color: var(--text-dim);
  }
  .filter-btn.active .filter-count {
    background: rgba(232,255,71,0.2); color: var(--accent);
  }
  .severity-dot {
    width: 8px; height: 8px; border-radius: 50%;
    display: inline-block; margin-right: 8px;
  }

  /* TABS */
  .tab-bar {
    display: flex; gap: 0; border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
  }
  .tab-btn {
    padding: 10px 20px; background: none; border: none;
    border-bottom: 2px solid transparent; margin-bottom: -1px;
    color: var(--text-dim); font-family: 'JetBrains Mono', monospace;
    font-size: 12px; cursor: pointer; transition: all 0.15s;
    text-transform: uppercase; letter-spacing: 0.08em;
  }
  .tab-btn:hover { color: var(--text); }
  .tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }
  .tab-panel.hidden { display: none; }

  /* CONTENT */
  .content { padding: 28px 36px; }
  .content-header {
    display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 20px;
  }
  .content-title {
    font-family: 'Syne', sans-serif; font-size: 13px;
    font-weight: 700; color: var(--text-dim);
    text-transform: uppercase; letter-spacing: 0.1em;
  }
  .result-count { font-size: 11px; color: var(--text-dim); }
  .result-count span { color: var(--accent); }

  /* BUG CARDS */
  .bug-list { display: flex; flex-direction: column; gap: 2px; }
  .bug-card {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 6px; overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
    cursor: pointer;
    animation: slideIn 0.3s ease both;
  }
  .bug-card:hover { border-color: var(--border-bright); transform: translateX(3px); }
  .bug-card.expanded { border-color: var(--accent); }
  @keyframes slideIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .bug-card-header {
    display: grid;
    grid-template-columns: 36px 130px 1fr 140px 80px;
    align-items: center; padding: 14px 18px; gap: 16px;
  }
  .bug-id { font-size: 10px; color: var(--text-dim); letter-spacing: 0.05em; }
  .game-tag {
    font-size: 10px; font-weight: 600; padding: 3px 8px;
    border-radius: 3px; text-transform: uppercase; letter-spacing: 0.06em;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .bug-title-text {
    font-size: 13px; color: var(--text); font-weight: 400;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .bug-type { font-size: 10px; color: var(--text-dim); text-align: right; white-space: nowrap; }
  .severity-badge {
    font-size: 10px; font-weight: 700; padding: 3px 10px;
    border-radius: 3px; text-align: center; text-transform: uppercase;
    letter-spacing: 0.08em; justify-self: end;
  }

  /* SEVERITY BADGES */
  .sev-critical { background: rgba(255,77,77,0.15);   color: var(--critical); border: 1px solid rgba(255,77,77,0.3); }
  .sev-major    { background: rgba(255,140,66,0.15);  color: var(--major);    border: 1px solid rgba(255,140,66,0.3); }
  .sev-minor    { background: rgba(255,209,102,0.15); color: var(--minor);    border: 1px solid rgba(255,209,102,0.3); }
  .sev-visual   { background: rgba(77,171,247,0.15);  color: var(--visual);   border: 1px solid rgba(77,171,247,0.3); }

  /* GAME TAG COLORS */
  .game-ds3       { background: rgba(180,30,30,0.15);   color: #cc3333; }
  .game-eldenring { background: rgba(255,215,0,0.1);    color: #ffd700; }
  .game-fallout4  { background: rgba(144,238,144,0.12); color: #90ee90; }
  .game-fallout76 { background: rgba(0,180,255,0.1);    color: #00b4ff; }
  .game-spiderman { background: rgba(220,50,220,0.1);   color: #e060e0; }
  .game-rdr1      { background: rgba(139,90,43,0.25);   color: #c4965a; }
  .game-rdr2      { background: rgba(30,80,140,0.2);    color: #5b9bd5; }
  .game-witcher3  { background: rgba(255,165,0,0.1);    color: #ffb347; }
  .game-wolf      { background: rgba(200,200,200,0.08); color: #aaaaaa; }
  .game-cp77      { background: rgba(252,238,9,0.1);    color: #fcee09; }
  .game-default   { background: rgba(156,163,175,0.1);  color: #9ca3af; }
  .game-gtav      { background: rgba(0,210,150,0.1);    color: #00d296; }
  .game-dqxi      { background: rgba(100,160,255,0.12); color: #6aa0ff; }
  .game-invincible{ background: rgba(180,100,255,0.1);  color: #c87fff; }
  .game-dave-diver{ background: rgba(0,200,220,0.1);    color: #00c8dc; }
  .game-days-gone { background: rgba(180,120,40,0.15);  color: #c8902a; }

  /* EXPANDED DETAIL — BUG */
  .bug-detail {
    display: none; border-top: 1px solid var(--border);
    padding: 20px 18px 24px; background: var(--bg3);
  }
  .bug-card.expanded .bug-detail { display: block; }
  .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
  .detail-section-title {
    font-size: 9px; text-transform: uppercase; letter-spacing: 0.15em;
    color: var(--text-dim); margin-bottom: 10px;
    display: flex; align-items: center; gap: 8px;
  }
  .detail-section-title::after {
    content: ''; flex: 1; height: 1px; background: var(--border);
  }
  .repro-steps { list-style: none; display: flex; flex-direction: column; gap: 6px; }
  .repro-step { display: flex; gap: 12px; font-size: 12px; color: var(--text-mid); line-height: 1.5; }
  .step-num { color: var(--accent); font-weight: 700; font-size: 10px; min-width: 16px; padding-top: 2px; }
  .detail-text { font-size: 12px; color: var(--text-mid); line-height: 1.8; }

  /* FINDING BULLETS */
  .finding-bullets {
    list-style: none; padding: 0; margin: 0;
    display: flex; flex-direction: column; gap: 7px;
  }
  .finding-bullets li {
    font-size: 12px; color: var(--text-mid); line-height: 1.7;
    display: flex; gap: 10px; align-items: baseline;
  }
  .finding-bullets li::before {
    content: "\\25B8"; color: var(--accent); font-size: 9px;
    flex-shrink: 0; margin-top: 2px;
  }
  .detail-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
  .chip {
    font-size: 10px; padding: 3px 9px; border-radius: 2px;
    background: var(--panel); border: 1px solid var(--border); color: var(--text-dim);
  }

  /* VIDEO */
  .video-placeholder {
    background: var(--bg); border: 1px dashed var(--border-bright);
    border-radius: 4px; height: 160px;
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 8px;
    color: var(--text-dim); font-size: 11px;
  }
  .video-icon {
    width: 32px; height: 32px; border: 1.5px solid var(--border-bright);
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
  }
  .video-wrapper { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 4px; }
  .video-wrapper iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }

  /* CASE STUDY CARDS */
  .cs-list { display: flex; flex-direction: column; gap: 2px; }
  .cs-card {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 6px; overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
    cursor: pointer;
    animation: slideIn 0.3s ease both;
  }
  .cs-card:hover { border-color: var(--border-bright); transform: translateX(3px); }
  .cs-card.expanded { border-color: var(--accent); }

  .cs-card-header {
    display: grid;
    grid-template-columns: 52px 180px 1fr auto;
    align-items: center; padding: 14px 18px; gap: 16px;
  }
  .cs-classification {
    font-size: 10px; color: var(--text-dim);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .cs-title {
    font-size: 13px; color: var(--text); font-weight: 400;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .cs-meta { display: flex; gap: 6px; }

  .cs-detail {
    display: none; border-top: 1px solid var(--border);
    padding: 20px 18px 24px; background: var(--bg3);
  }
  .cs-card.expanded .cs-detail { display: block; }

  .cs-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .cs-meta-item {}
  .cs-footer-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

  /* FINDINGS */
  .findings-list { display: flex; flex-direction: column; gap: 2px; margin-bottom: 4px; }
  .finding-row {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 4px; overflow: hidden;
    cursor: pointer; transition: border-color 0.15s;
  }
  .finding-row:hover { border-color: var(--border-bright); }
  .finding-header {
    display: grid; grid-template-columns: 1fr 1fr 100px;
    align-items: center; padding: 10px 14px; gap: 12px;
  }
  .finding-category { font-size: 12px; color: var(--text); font-weight: 600; }
  .finding-impact { font-size: 11px; color: var(--text-dim); text-align: right; }
  .finding-body {
    display: none; border-top: 1px solid var(--border);
    padding: 14px; background: var(--bg);
    grid-template-columns: 1fr 1fr; gap: 16px;
  }
  .finding-expanded .finding-body { display: grid; }
  .finding-col {}
  .finding-label {
    font-size: 9px; text-transform: uppercase; letter-spacing: 0.12em;
    color: var(--text-dim); margin-bottom: 6px;
  }

  /* RISK BADGES */
  .risk-badge {
    font-size: 10px; font-weight: 700; padding: 3px 10px;
    border-radius: 3px; text-align: center; text-transform: uppercase;
    letter-spacing: 0.08em; white-space: nowrap; justify-self: end;
  }
  .risk-high          { background: rgba(255,77,77,0.15);    color: var(--critical); border: 1px solid rgba(255,77,77,0.3); }
  .risk-moderate      { background: rgba(255,140,66,0.15);   color: var(--major);    border: 1px solid rgba(255,140,66,0.3); }
  .risk-low           { background: rgba(77,171,247,0.15);   color: var(--visual);   border: 1px solid rgba(77,171,247,0.3); }
  .risk-low-moderate  { background: rgba(255,209,102,0.15);  color: var(--minor);    border: 1px solid rgba(255,209,102,0.3); }
  .risk-strength      { background: rgba(6,214,160,0.12);    color: var(--green);    border: 1px solid rgba(6,214,160,0.3); }

  /* ABOUT */
  .about-panel { margin-top: 36px; border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
  .about-header {
    background: var(--panel); padding: 12px 18px;
    font-size: 9px; text-transform: uppercase;
    letter-spacing: 0.15em; color: var(--text-dim);
    border-bottom: 1px solid var(--border);
  }
  .about-body {
    padding: 20px 18px; display: grid;
    grid-template-columns: 1fr 1fr 1fr; gap: 20px; background: var(--bg3);
  }
  .about-col-title { font-size: 10px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-dim); margin-bottom: 10px; }
  .about-col p { font-size: 12px; color: var(--text-mid); line-height: 1.7; }
  .skill-list { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }
  .skill-list-single { display: flex; flex-direction: column; gap: 4px; }
  .skill-item { font-size: 11px; color: var(--text-mid); display: flex; align-items: center; gap: 8px; }
  .skill-list .skill-item::before,
  .skill-list-single .skill-item::before { content: '\\25B8'; color: var(--accent); font-size: 9px; }

  /* SCROLLBAR */
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg); }
  ::-webkit-scrollbar-thumb { background: var(--border-bright); border-radius: 2px; }

  /* FOOTER */
  footer {
    border-top: 1px solid var(--border); padding: 16px 40px;
    display: flex; align-items: center; justify-content: space-between;
    font-size: 10px; color: var(--text-dim); background: var(--bg2);
  }

  .hidden { display: none !important; }

  /* GAME CONCEPT DOCS */
  .gc-list { display: flex; flex-direction: column; gap: 2px; padding-bottom: 40px; }
  .gc-doc {
    background: var(--panel); border: 1px solid var(--border);
    border-radius: 6px; overflow: hidden;
    cursor: pointer; transition: border-color 0.2s, transform 0.15s;
    animation: slideIn 0.3s ease both;
  }
  .gc-doc:hover { border-color: var(--border-bright); transform: translateX(3px); }
  .gc-doc.gc-expanded { border-color: var(--accent); }
  .gc-doc-header {
    display: grid; grid-template-columns: 68px 1fr 160px;
    align-items: center; padding: 14px 18px; gap: 16px;
  }
  .gc-doc-col-id { display: flex; flex-direction: column; gap: 4px; }
  .gc-index { font-size: 10px; color: var(--text-dim); letter-spacing: 0.08em; }
  .gc-expand-hint { font-size: 9px; color: var(--text-dim); opacity: 0.5; transition: opacity 0.15s; }
  .gc-doc:hover .gc-expand-hint { opacity: 1; color: var(--accent); }
  .gc-doc.gc-expanded .gc-expand-hint { opacity: 0; }
  .gc-doc-col-main { display: flex; flex-direction: column; gap: 4px; }
  .gc-title { font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 13px; color: var(--text); letter-spacing: 0.02em; }
  .gc-subtitle { font-size: 10px; color: var(--text-dim); letter-spacing: 0.04em; }
  .gc-doc-col-meta { display: flex; flex-direction: column; gap: 6px; align-items: flex-end; }
  .gc-stage-badge {
    font-size: 9px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.12em; padding: 3px 8px; border-radius: 3px; white-space: nowrap;
  }
  .gc-stage-concept   { background: rgba(77,171,247,0.12);  color: var(--visual); border: 1px solid rgba(77,171,247,0.25); }
  .gc-stage-specced   { background: rgba(255,209,102,0.12); color: var(--minor);  border: 1px solid rgba(255,209,102,0.25); }
  .gc-stage-prototype { background: rgba(6,214,160,0.12);   color: var(--green);  border: 1px solid rgba(6,214,160,0.25); }
  .gc-stage-shipped   { background: rgba(255,165,0,0.15);   color: #ffaa33;       border: 1px solid rgba(255,165,0,0.35); }
  .gc-doc-body {
    display: none; border-top: 1px solid var(--border);
    padding: 20px 18px 24px; background: var(--bg3);
  }
  .gc-doc.gc-expanded .gc-doc-body { display: block; }
  .gc-doc-pitch {
    font-size: 13px; color: var(--text); line-height: 1.8; margin-bottom: 20px;
    font-style: italic; border-left: 2px solid var(--border-bright); padding-left: 14px;
  }
  .gc-doc-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
  .gc-doc-section { display: flex; flex-direction: column; gap: 8px; }
  .gc-links { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
  .gc-link-btn {
    font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;
    padding: 5px 12px; border-radius: 3px; text-decoration: none;
    border: 1px solid var(--border-bright); color: var(--text-dim);
    transition: color 0.15s, border-color 0.15s;
  }
  .gc-link-btn:hover { color: var(--accent); border-color: var(--accent); }
  .gc-link-btn.gc-link-primary { color: var(--accent); border-color: rgba(232,255,71,0.4); }
  .gc-link-btn.gc-link-primary:hover { border-color: var(--accent); }
  .gc-roster-toggle {
    font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;
    background: none; border: 1px solid var(--border-bright); color: var(--text-dim);
    padding: 2px 8px; border-radius: 3px; cursor: pointer; margin-left: 8px;
    vertical-align: middle; transition: color 0.15s, border-color 0.15s;
  }
  .gc-roster-toggle:hover { color: var(--accent); border-color: var(--accent); }
  .gc-vibe {
    font-size: 12px; color: var(--accent); opacity: 0.9;
    border-top: 1px solid var(--border); padding-top: 14px; line-height: 1.7; font-style: italic;
  }
  .gc-concepts-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
  .gc-concepts-note { font-size: 11px; color: var(--text-dim); font-style: italic; }
"""


# ── MAIN BUILD FUNCTION ────────────────────────────────────────────────────────

def build_dashboard(bugs_json_path: str, case_studies_json_path: str, concepts_json_path: str, output_path: str) -> None:
    with open(bugs_json_path, "r", encoding="utf-8") as f:
        bugs = json.load(f)

    case_studies = []
    if os.path.exists(case_studies_json_path):
        with open(case_studies_json_path, "r", encoding="utf-8") as f:
            case_studies = json.load(f)
        print(f"  Loaded {len(case_studies)} case studies from {case_studies_json_path}")
    else:
        print(f"  No case_studies.json found at {case_studies_json_path} — skipping section.")

    concepts = []
    if os.path.exists(concepts_json_path):
        with open(concepts_json_path, "r", encoding="utf-8") as f:
            concepts = json.load(f)
        print(f"  Loaded {len(concepts)} game concepts from {concepts_json_path}")
    else:
        print(f"  No concepts.json found at {concepts_json_path} — skipping section.")

    print(f"  Loaded {len(bugs)} bug reports from {bugs_json_path}")

    stats_bar  = make_stats_bar(bugs)
    sidebar    = make_sidebar_html(bugs, case_studies, concepts)
    bug_cards  = "\n".join(make_bug_card(b) for b in bugs)
    filter_js  = make_filter_js(bugs)
    total_bugs = len(bugs)

    cs_cards       = "\n".join(make_case_study_card(cs) for cs in case_studies)
    cs_count       = len(case_studies)
    concepts_html  = "\n".join(make_concept_card(c) for c in concepts)
    total_concepts = len(concepts)

    # Titles Tested list (unique games in bug order)
    all_games, seen = [], set()
    for b in bugs:
        gk = b["game"]
        if gk not in seen:
            seen.add(gk)
            all_games.append(GAME_CONFIG.get(gk, {}).get("label", b.get("game_name", gk)))

    titles_html = "\n".join(
        f'            <div class="skill-item">{escape(g)}</div>' for g in all_games
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wendell Lancaster &mdash; QA Portfolio &amp; Game Design</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>

<!-- HEADER -->
<header>
  <div class="header-left">
    <div class="logo-mark">WL</div>
    <div class="header-name">WENDELL LANCASTER</div>
    <div class="header-role">QA Tester &nbsp;&middot;&nbsp; Game Developer &nbsp;&middot;&nbsp; Designer</div>
  </div>
  <div class="header-right">
    <a href="mailto:wendell91097@gmail.com" class="header-contact">wendell91097@gmail.com</a>

    <a href="https://sovereigndev.itch.io" target="_blank" class="header-contact">sovereigndev.itch.io</a>
    <div style="font-size:11px; color: var(--green);">
      <span class="status-dot"></span>Open to Work
    </div>
  </div>
</header>

<!-- STATS BAR -->
{stats_bar}

<!-- MAIN -->
<div class="main">

{sidebar}

  <!-- CONTENT -->
  <div class="content">

    <!-- TABS -->
    <div class="tab-bar">
      <button class="tab-btn active" data-tab="bugs" onclick="switchTab('bugs')">// Bug Reports</button>
      <button class="tab-btn" data-tab="game-concepts" onclick="switchTab('game-concepts')">// Game Concepts <span style="font-size:10px; opacity:0.6">({total_concepts})</span></button>
      <button class="tab-btn" data-tab="case-studies" onclick="switchTab('case-studies')">// Case Studies <span style="font-size:10px; opacity:0.6">({cs_count})</span></button>
    </div>

    <!-- BUG REPORTS PANEL -->
    <div class="tab-panel" id="panel-bugs">
      <div class="content-header">
        <div class="result-count">Showing <span id="count">{total_bugs}</span> of {total_bugs} reports</div>
      </div>
      <div class="bug-list" id="bugList">
{bug_cards}
      </div>
    </div>

    <!-- CASE STUDIES PANEL -->
    <div class="tab-panel hidden" id="panel-case-studies">
      <div class="content-header">
        <div class="result-count"><span>{cs_count}</span> evaluation{'s' if cs_count != 1 else ''}</div>
      </div>
      <div class="cs-list">
{cs_cards}
      </div>
    </div>

    <!-- GAME CONCEPTS PANEL -->
    <div class="tab-panel hidden" id="panel-game-concepts">
      <div class="gc-concepts-header">
        <div class="content-title">// Game Concepts</div>
        <div class="gc-concepts-note">Click any concept to expand full design document</div>
      </div>
      <div class="gc-list">
{concepts_html}
      </div>
    </div>

        <!-- ABOUT PANEL -->
    <div class="about-panel">
      <div class="about-header">// About This Portfolio &amp; Design Work</div>
      <div class="about-body">
        <div class="about-col">
          <div class="about-col-title">Background</div>
          <p>Independent QA tester and game developer based in the Greater Boston Metro. Shipped WordSmith on Itch.io (Godot), completed 1,300+ hours of paid user testing, and self-directed bug documentation across 15 titles. Open to remote entry-level QA roles.</p>
        </div>
        <div class="about-col">
          <div class="about-col-title">QA Skills</div>
          <div class="skill-list-single">
            <div class="skill-item">Bug documentation &amp; reproduction steps</div>
            <div class="skill-item">Defect classification &amp; severity rating</div>
            <div class="skill-item">Screen capture &amp; video evidence</div>
            <div class="skill-item">Edge case &amp; boundary testing</div>
            <div class="skill-item">Cross-title regression awareness</div>
          </div>
        </div>
        <div class="about-col">
          <div class="about-col-title">Titles Tested</div>
          <div class="skill-list">
{titles_html}
          </div>
        </div>
      </div>
    </div>

  </div><!-- /content -->
</div><!-- /main -->

<footer>
  <div>Wendell Lancaster &mdash; QA Portfolio &amp; Game Design // Built with precision</div>
  <div>Boston, MA &nbsp;&middot;&nbsp; wendell91097@gmail.com</div>
</footer>

<script>
{filter_js}
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Output written to {output_path}")
    print(f"  {total_bugs} bugs | {cs_count} case studies | {total_concepts} game concepts")


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    build_dashboard(
        bugs_json_path        = os.path.join(base, "bugs.json"),
        case_studies_json_path= os.path.join(base, "case_studies.json"),
        concepts_json_path    = os.path.join(base, "concepts.json"),
        output_path           = os.path.join(base, "index.html"),
    )
