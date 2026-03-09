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


# ── HTML GENERATORS — SIDEBAR ──────────────────────────────────────────────────

def make_sidebar_html(bugs: list, case_studies: list) -> str:
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
          All Concepts <span class="filter-count">9</span>
        </button>
        <button class="filter-btn" onclick="filterConcepts('shipped', this)">
          Shipped <span class="filter-count">1</span>
        </button>
        <button class="filter-btn" onclick="filterConcepts('prototype', this)">
          Prototype-Ready <span class="filter-count">2</span>
        </button>
        <button class="filter-btn" onclick="filterConcepts('specced', this)">
          Specced <span class="filter-count">4</span>
        </button>
        <button class="filter-btn" onclick="filterConcepts('concept', this)">
          Concept <span class="filter-count">2</span>
        </button>
      </div>
      <div class="sidebar-section">
        <div class="sidebar-label">Jump To</div>
        <button class="filter-btn" onclick="jumpTo('gc-001')">WordSmith</button>
        <button class="filter-btn" onclick="jumpTo('gc-004')">Playground Noir</button>
        <button class="filter-btn" onclick="jumpTo('gc-002')">Immortal Coil</button>
        <button class="filter-btn" onclick="jumpTo('gc-003')">Manifest</button>
        <button class="filter-btn" onclick="jumpTo('gc-009')">Bear&#x27;s Blooming Forest</button>
        <button class="filter-btn" onclick="jumpTo('gc-005')">Swan Marriage Counselor</button>
        <button class="filter-btn" onclick="jumpTo('gc-008')">Warp Gun</button>
        <button class="filter-btn" onclick="jumpTo('gc-006')">Winter Storm</button>
        <button class="filter-btn" onclick="jumpTo('gc-007')">Conquistador Sim</button>
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

def build_dashboard(bugs_json_path: str, case_studies_json_path: str, output_path: str) -> None:
    with open(bugs_json_path, "r", encoding="utf-8") as f:
        bugs = json.load(f)

    case_studies = []
    if os.path.exists(case_studies_json_path):
        with open(case_studies_json_path, "r", encoding="utf-8") as f:
            case_studies = json.load(f)
        print(f"  Loaded {len(case_studies)} case studies from {case_studies_json_path}")
    else:
        print(f"  No case_studies.json found at {case_studies_json_path} — skipping section.")

    print(f"  Loaded {len(bugs)} bug reports from {bugs_json_path}")

    stats_bar  = make_stats_bar(bugs)
    sidebar    = make_sidebar_html(bugs, case_studies)
    bug_cards  = "\n".join(make_bug_card(b) for b in bugs)
    filter_js  = make_filter_js(bugs)
    total_bugs = len(bugs)

    cs_cards = "\n".join(make_case_study_card(cs) for cs in case_studies)
    cs_count = len(case_studies)

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
    <a href="tel:2282376193" class="header-contact">(228) 237-6193</a>
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
      <button class="tab-btn" data-tab="game-concepts" onclick="switchTab('game-concepts')">// Game Concepts <span style="font-size:10px; opacity:0.6">(9)</span></button>
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

        <!-- GC-001: WORDSMITH -->
        <div class="gc-doc" id="gc-001" data-stage="shipped" onclick="toggleGcCard(this)" style="animation-delay:0.02s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-001</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">WordSmith</div><div class="gc-subtitle">Word Puzzle &middot; Letter Grid &middot; Pure Systems</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-shipped">Shipped</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">A word-finding puzzle game with no story, no characters, and no win condition you didn&#x2019;t set yourself. Grid of letters, three game modes, two tools. Find words, clear tiles, keep the grid alive.</div>
            <div class="gc-links">
              <a class="gc-link-btn gc-link-primary" href="https://sovereigndev.itch.io/wordsmith" target="_blank" onclick="event.stopPropagation()">&#9660; Play on itch.io</a>
              <a class="gc-link-btn" href="https://youtu.be/MCcAFdG_dV4" target="_blank" onclick="event.stopPropagation()">&#9654; Gameplay Video</a>
            </div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section"><div class="finding-label">Core Loop</div><ul class="finding-bullets"><li>The player navigates a letter grid ranging from 4&times;4 to 8&times;8 and traces valid words in any direction (horizontal, vertical, diagonal) without reusing the same letter twice per word.</li><li>Valid words remove their letters from the grid. The tiles above cascade down to fill the gap, Tetris-style. New letters generate from the top to keep the grid full. The player never sees a half-empty board.</li><li>The Wordsmith hammer is a targeted tool: the player can use it to remove specific letters from the grid independently of word-making, creating space or breaking up bad distributions.</li><li>Shuffle resets the grid entirely when the current layout is unworkable.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Game Modes</div>
                <div style="display:flex; flex-direction:column; gap:8px; margin-top:4px;">
                  <div style="background:rgba(77,171,247,0.07); border:1px solid rgba(77,171,247,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--blue); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Classic</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">A set number of letters can be used before the round ends. The constraint is total throughput, not time. Rewards deliberate, high-value word selection over speed.</p>
                  </div>
                  <div style="background:rgba(255,77,77,0.07); border:1px solid rgba(255,77,77,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--red); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Timed</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">A player-set time limit. Same grid, different pressure. Rewards fast pattern recognition over optimization. The clock changes what kind of player wins.</p>
                  </div>
                  <div style="background:rgba(6,214,160,0.07); border:1px solid rgba(6,214,160,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--green); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Endless</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">No win condition, no loss condition. The grid runs indefinitely. Chill by design.</p>
                  </div>
                </div>
              </div>
              <div class="gc-doc-section"><div class="finding-label">Design Notes</div><ul class="finding-bullets"><li>Retro pixel art aesthetic throughout, with parallax backgrounds sourced from open licensed assets with attribution. Settings allow music, SFX, and background swaps from the start screen.</li><li>Built in Godot. Released August 22, 2024. Windows desktop download, no installation required.</li><li>The cascade mechanic changes the strategic calculus compared to static-grid word games: clearing a cluster of letters reshapes the board, which creates new adjacencies and new problems simultaneously.</li><li>The hammer gives the player agency over the board state without requiring a full shuffle. It adds meaningful tactical decision-making without complicating the core loop.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Influences</div><ul class="finding-bullets"><li>Boggle &mdash; directional letter adjacency as the core word-finding structure.</li><li>Bookworm (PopCap) &mdash; tiles cleared on valid word submission, board management as an emergent challenge.</li><li>Tetris &mdash; gravity-based cascade as the feedback mechanism for clearing; the board as a living system rather than a static puzzle.</li></ul></div>
            </div>
            <div class="gc-vibe">This is the one card on the slate where the design question is already answered. It shipped. The rest of the concepts are documented to show how I think; this one is here to show that the thinking goes somewhere.</div>
          </div>
        </div>

        <!-- GC-002: PLAYGROUND NOIR -->
        <div class="gc-doc" id="gc-004" data-stage="prototype" onclick="toggleGcCard(this)" style="animation-delay:0.05s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-004</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Playground Noir</div><div class="gc-subtitle">Mystery Visual Novel &middot; Kindergarten Ace Attorney &middot; Unreliable Witnesses</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-prototype">Prototype-Ready</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">The last cookie has been eaten. The daycare is in crisis. You are the investigator. Every witness is five years old, completely unreliable, and in the middle of something more important than your case.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section"><div class="finding-label">Core Premise</div><ul class="finding-bullets"><li>A mystery visual novel applying full noir investigation structure &mdash; evidence, cross-examination, witness contradiction &mdash; to playground-scale crimes.</li><li>Children do not stop their world for your questions. Testimony happens mid-activity: mid-jump, mid-drawing, mid-game. The investigator enters the child&#x2019;s frame, not the reverse. You want information from the Baseball Kid, you talk baseball first.</li><li>Simple motivations mean simple solutions. A child took the cookie because they were hungry. A child lied to protect their friend. The solution is always obvious in retrospect and always wholesome. The noir structure is borrowed; the darkness never is.</li><li>The specimen case: two kids have crumbs on their shirts. The answer: they shared it. Both guilty. Both innocent. The resolution is mandatory warmth.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">The Cast</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:4px;">
                  <div style="background:rgba(77,171,247,0.07); border:1px solid rgba(77,171,247,0.25); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--blue); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The &ldquo;Librarian&rdquo;</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.6;">Anxious about being correct. Remembers details with precision and loses context entirely. Will correct your phrasing mid-sentence. Mid-chapter of a book when you arrive.</p>
                  </div>
                  <div style="background:rgba(255,77,77,0.07); border:1px solid rgba(255,77,77,0.25); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--red); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The Dinosaur Kid</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.6;">Confident. Exaggerates scale automatically. Simple motivations: they did it because it seemed fun, or they were hungry. Currently stomping around making T-Rex sounds at no one in particular.</p>
                  </div>
                  <div style="background:rgba(6,214,160,0.07); border:1px solid rgba(6,214,160,0.25); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--green); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The Baseball Kid</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.6;">Perpetually mid-game in their head. Will not stop throwing an imaginary ball. Useful testimony only comes after you demonstrate baseline baseball knowledge. Worth it.</p>
                  </div>
                  <div style="background:rgba(180,100,255,0.07); border:1px solid rgba(180,100,255,0.25); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:#c87fff; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The Animal Friend</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.6;">Loves animals with total sincerity. Confabulates for their benefit &mdash; her version of events is whatever kept the animals safest. Currently giving a checkup to every stuffed animal she owns.</p>
                  </div>
                </div>
              </div>
              <div class="gc-doc-section"><div class="finding-label">Mechanics</div><ul class="finding-bullets"><li>Ace Attorney investigation and cross-examination loop adapted for a younger audience. The challenge isn&#x2019;t finding the guilty party &mdash; it&#x2019;s figuring out which truth is true, given that every witness is telling you their truth sincerely.</li><li>The play-along mechanic: some testimony is only unlocked by entering the witness&#x2019;s current activity. You cannot interrupt the Dinosaur Kid mid-hunt. You can join it.</li><li>Red herrings are structurally embedded: evidence that looks damning leads to a different, more innocent explanation. The guilt in this world is the kind that can be forgiven in the same afternoon.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Influences</div><ul class="finding-bullets"><li>Ace Attorney series &mdash; investigation loop, testimony contradiction, high drama applied to low stakes.</li><li>Professor Layton &mdash; episodic puzzle mysteries, gentle tone, standalone cases that work for mixed-age audiences.</li><li>Bluey &mdash; the comedy of treating children&#x2019;s problems with adult seriousness, without condescension. The children are the straight faces; the adult register is the joke.</li></ul></div>
            </div>
            <div class="gc-vibe">Ace Attorney is 22 years old and nobody has made a wholesome version for a younger audience. The unreliable witness system isn&#x2019;t a gimmick &mdash; it&#x2019;s the entire design. Children don&#x2019;t lie the way adults lie. They misremember, protect people they love, and confabulate completely. The play-along mechanic puts that at the center: you cannot extract testimony from a child who doesn&#x2019;t want to give it. You have to go where they are. That&#x2019;s the adult layer: the game is easy for a child to play because it asks nothing more than what children already know. For an adult, it&#x2019;s a mirror &mdash; a reminder that the best way to connect with a kid is not to get them to stop what they&#x2019;re doing, but to understand why they can&#x2019;t. That&#x2019;s the message underneath the mystery structure &mdash; aimed at the adult holding the controller. The game is a gentle reminder that children don&#x2019;t stop their world for you. The better move has always been to enter theirs.</div>
          </div>
        </div>

        <!-- GC-003: IMMORTAL COIL -->
        <div class="gc-doc" id="gc-002" data-stage="prototype" onclick="toggleGcCard(this)" style="animation-delay:0.08s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-002</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Immortal Coil</div><div class="gc-subtitle">Pattern-Recognition Combat &middot; Dystopian Arena Drama &middot; Transhumanist Horror</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-prototype">Prototype-Ready</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">All criminals are immortal. They fight in arenas year-round for public amusement. Win five championships and earn the only thing anyone in this society still wants: the right to die. The problem is that by the time you&#x2019;ve won five championships, the elite have made sure you don&#x2019;t want it anymore. You see it all through your own eyes &mdash; what&#x2019;s left of them.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section"><div class="finding-label">Core Premise</div><ul class="finding-bullets"><li>Immortality is not biological &mdash; it is infrastructural. When the body sustains brain death, the state restores the individual from a prior neural save state: a snapshot of the mind taken at regular intervals, patched over the corrupted data. Resurrection is a government process. You do not consent to it. You do not own your continuity.</li><li>Each restoration is lossy. Like a file recompressed too many times, fidelity degrades. Memories blur at the edges. Personality flattens. The mental deterioration the player feels across a run is not damage &mdash; it is accumulated restoration artifact. The machine keeps bringing you back. It keeps bringing back slightly less of you.</li><li>Three tiers: the underclass fights, the middle class watches but does not participate, the elite never sets foot in the arena. The arena is a management tool aimed at the bottom tier. The middle class watching the underclass fight keeps both groups pointed sideways instead of upward &mdash; Roman bread-and-circus logic applied to a transhumanist dystopia.</li><li>Fights run year-round. The main championship tournament is the marquee spectacle, but losers&#x2019; brackets, exhibition bouts, and consolation tournaments fill the calendar continuously. There is always something to watch. There is always someone losing.</li><li>Five championships is the official threshold for earned euthanasia. The number is arbitrary &mdash; bureaucratic tradition so old its origin is propaganda &mdash; but it doesn&#x2019;t matter, because the euthanasia was never real. A champion is too valuable to the system to release.</li><li>Instead, the elite make death seem terrible and life as a champion seem extraordinary. Prize wealth, status, comfort, celebrity &mdash; enough that most champions never invoke the clause. The few who do discover the offer was a lie dressed up as a right: mind-wipe, reprogramming, blackmail, torture, or worse &mdash; consciousness trapped in a dead signal, a fuzzier version of yourself fading slowly in a loop, no exit. There are no happy endings. There is only a signal degrading until there is nothing left to degrade.</li><li>The player is a convicted criminal entering unseeded at the bottom of the bracket. Bodies heal between bouts. Mental fidelity does not. Every augmentation makes you more competitive and less yourself &mdash; felt from the inside.</li><li>Roguelite structure: each run is a full tournament season. Augmentation combinations, opponent loadouts, and new attack patterns vary between runs. You learn the system across deaths. The tournament remembers you. You have to remember it faster.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Mechanics</div><ul class="finding-bullets"><li>First-person perspective, optionally VR. You look out through eyes that used to be yours. Your hands in front of you are chrome. You cannot look away from what you&#x2019;ve become.</li><li>Full ring mobility: sidestep, backpedal, close distance, cut angles. Footwork is tactical; positioning creates the windows the pattern system requires.</li><li>Punch-Out DNA: opponents run on readable, repeatable patterns. Cybernetic augmentations are the tell system: a HUD ping reading TARGET LOCKED, steam venting from a joint, an arm morphing into a new attack mode. The visual language is the gameplay.</li><li>Player augmentations unlock between bouts &mdash; each a genuine tradeoff. Better reach, faster counters, harder hits. Each one another step toward what you&#x2019;re fighting to escape.</li><li>Mental degradation modeled over time: early fights feel sharp. Later fights accumulate visual noise, flickering tells, HUD lag. The machine is winning even when you are.</li><li>End of fight rituals: mandatory, performed for the crowd, choreographed by the arena. The form of commemoration without the substance &mdash; a sacred gesture co-opted into spectacle. The player performs them whether they want to or not. Over time, what they mean to the player and what they mean to the crowd become two entirely different things.</li><li>Trophy system: a component stripped from a defeated opponent &mdash; a chrome piece, a lens, a joint casing. The only objects in the game that belong to the player rather than the system. Displayed in the fighter&#x2019;s cell. The one act of curation the arena cannot script.</li><li>Opponent relationships: fighters you&#x2019;ve beaten reappear across seasons. Fighters who have beaten you may carry a trophy from that encounter &mdash; something of yours, displayed in their own cell. Lose to someone and they own a piece of you. Beat them later and you can take it back, or leave it. The arena insists these are enemies. The trophies tell a different story.</li><li>Some opponents become something closer to rivals, then something closer to the only people who understand what this is. The relationship system is not social &mdash; it is purely environmental. You learn each other through the fight. There is no dialogue. There does not need to be.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Thematic DNA</div>
                <div style="display:flex; flex-direction:column; gap:8px; margin-top:4px;">
                  <div style="background:rgba(255,77,77,0.07); border:1px solid rgba(255,77,77,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--red); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The Complicity Trap</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Every augmentation is a vote for the system. The player is not a rebel &mdash; they are a product of the arena. Winning requires becoming what the arena needs you to be.</p>
                  </div>
                  <div style="background:rgba(180,100,255,0.07); border:1px solid rgba(180,100,255,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:#c87fff; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">First Person as Horror</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">You cannot cut away from the hands. The detachment from your own body is not a cutscene &mdash; it is the camera. Chrome where skin used to be, in every frame, for the whole game.</p>
                  </div>
                  <div style="background:rgba(77,171,247,0.07); border:1px solid rgba(77,171,247,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--blue); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The False Exit</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Immortality is a government service. The euthanasia clause exists to motivate fighters, not to be exercised. Champions who try to claim it find out what the state does to tools that try to retire: mind-wipe, reprogramming, or worse &mdash; consciousness isolated in a dead signal, a fuzzier version of yourself fading slowly with no exit. The offer was always a lie. Five championships was never the price of death. It was the price of finding that out.</p>
                  </div>
                  <div style="background:rgba(255,140,66,0.07); border:1px solid rgba(255,140,66,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--orange); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The Only Canvas Left</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">The arena permits one form of self-expression: the fight. Your augmentation choices are the only aesthetic decisions you&#x2019;re allowed. The opponent is the only relationship the system sanctions. Destruction of others is the sole creative act available. The trophies are the exception &mdash; the one thing the player curates that the system did not script. A cell full of chrome pieces from people you&#x2019;ve beaten, or been beaten by, is the closest thing to an autobiography this world allows.</p>
                  </div>
                  <div style="background:rgba(6,214,160,0.07); border:1px solid rgba(6,214,160,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--green); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The Resistance Has Always Existed</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">There is a faction that knows the truth: about the save-state infrastructure, the euthanasia clause, what the elite actually are. They have been here for generations. The system has always known about them. The system has always been fine with that. A rebellion that cannot reach the puppeteers, that cannot dismantle what no one fully controls anymore &mdash; that rebellion is not a threat. It is another spectacle. The most dangerous thing the player can discover is not how to fight the system. It is that the system anticipated that too.</p>
                  </div>
                </div>
              </div>
              <div class="gc-doc-section"><div class="finding-label">Influences</div><ul class="finding-bullets"><li>Punch-Out!! &mdash; pattern recognition as the entire design; opponents as puzzles with tells, not health bars to deplete.</li><li>Dark Souls &mdash; immortality as a curse; the hollow mechanic as a model for what repeated survival costs the self.</li><li>Disco Elysium &mdash; the collapse of a moral framework as both world-building and gameplay.</li><li>Rollerball (1975) &mdash; sport as systemic dehumanization; the crowd as the real antagonist.</li><li>Warhammer 40,000 &mdash; technology so ancient maintaining it has become religious ritual.</li><li>Cyberpunk 2077 / the Chrome aesthetic &mdash; transhumanism as ubiquity rather than novelty; a world where body modification is so normalized it has stopped being a choice and started being an expectation.</li><li>Neon Genesis Evangelion &mdash; the psychic cost of doing what the machine requires; the body as something that happens to you.</li></ul></div>
            </div>
            <div class="gc-vibe">The euthanasia clause is the game&#x2019;s central trap. You spend the whole run fighting toward something the system never intended to give you. By the time you&#x2019;ve won five championships, the elite have spent five runs making you too rich, too famous, and too degraded to want it. The trophies are the counter-argument the game makes quietly: the only objects that belong to the player, the only history the system cannot rewrite. Lose to someone and they own a piece of you. Beat them later and you decide what that means. The arena calls them enemies. The trophies call them the only people who know what you are. The bread-and-circus layer is what makes the world coherent: the middle class watches the underclass fight, which keeps both groups pointed sideways. No one looks up. The arena combat loop gives QA something concrete to test: does augmentation feel like a tradeoff or just a power increase? Does mental decay change how the player reads tells, or is it cosmetic? Do the opponent relationships actually shift how the player approaches a rematch, or are they just flavor? Those are real questions with testable answers. The first-person frame is not an aesthetic choice &mdash; it is the argument.</div>
          </div>
        </div>

        <!-- GC-004: MANIFEST -->
        <div class="gc-doc" id="gc-003" data-stage="specced" onclick="toggleGcCard(this)" style="animation-delay:0.11s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-003</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Manifest</div><div class="gc-subtitle">Branching Narrative &middot; Frontier Homestead &middot; You Shape What America Becomes</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-specced">Specced</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">You have staked a claim on the frontier. A homestead at the crossroads of everything America is becoming. Every week someone new comes through. Some are running from something. Some are running toward something worth dying for. Every choice compounds. The country being built around you will remember what you did here.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section" style="grid-column: 1 / -1"><div class="finding-label">Core Premise &amp; Choice Architecture</div><ul class="finding-bullets"><li>1850 to 1900. Fifty years. A visual choose-your-own-adventure spanning the full arc of the American frontier era, ending at the turn of the century. The player is a fixed point while half a century moves through them.</li><li>Choices establish reputation, close doors, open others, reshape the settlement over decades. Decisions made in the 1850s are still paying out in the 1890s. One wrong move and your entire herd of cattle is gone. A wrong guest sheltered at the wrong time and the Pinkertons know your name. The stakes are permanent and quiet until they aren&#x2019;t.</li><li>The newspaper mechanic starts slow: a single regional paper arrives monthly in the early years, carrying word of people who passed through. Some made it. Some are on wanted posters. Some names appear in obituaries with no next of kin listed. As decades pass, the papers multiply &mdash; the Denver Rocky Mountain News, the Chicago Tribune, the San Francisco Chronicle, the Atlanta Constitution, dispatches from New Orleans and St. Louis, occasional pages from Tijuana and Ciudad Ju&#xe1;rez carried by traders coming north. The homestead is not a waypoint on a one-way road west. It sits at a crossroads. People pass through heading every direction &mdash; north to the railroad camps, south across the border, east back to cities they left, west toward something they haven&#x2019;t named yet. By the 1890s the player is reading competing accounts of the same events from a dozen cities, and they know which version is true because they were there.</li><li>This was a deeply Christian nation. The moral vocabulary of the era is scripture: charity, sanctuary, bearing false witness, rendering unto Caesar. Turning someone away is not a neutral act.</li><li>The game can end early. Catastrophic choices compound into ruin &mdash; a lost herd, a burned homestead, a reputation that closes every door in the territory. It is possible to not make it to 1900. That is the point.</li></ul></div>
              <div class="gc-doc-section" style="grid-column: 1 / -1"><div class="finding-label">The Guests Who Matter Most</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:4px;">
                  <div style="background:rgba(255,77,77,0.07); border:1px solid rgba(255,77,77,0.25); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--red); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The Comanche</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Traveling under a name that is not his. His sister is missing. He needs one night&#x2019;s shelter and your silence. What do you do when the marshal comes asking the next morning?</p>
                  </div>
                  <div style="background:rgba(6,214,160,0.07); border:1px solid rgba(6,214,160,0.25); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--green); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The Conductor</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">A freed Black man, educated minister, moving people north. Route the Underground Railroad through your homestead and weeks later a rider comes at night with different intentions. Help enough people and the wrong people take notice.</p>
                  </div>
                  <div style="background:rgba(77,171,247,0.07); border:1px solid rgba(77,171,247,0.25); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--blue); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The Teacher</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Heading to a mining camp that does not know it needs her. Whether she makes it depends partly on what you tell her about the road ahead.</p>
                  </div>
                  <div style="background:rgba(220,220,220,0.05); border:1px solid rgba(220,220,220,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:#d0d0d0; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The Pastor</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Road-worn, theologically complicated, genuinely kind. He will tell you plainly what he thinks you are doing wrong with your life. He is usually right.</p>
                  </div>
                </div>
                <div style="margin-top:8px;"><div class="finding-label" style="margin-bottom:6px;">The Fuller Roster <button class="gc-roster-toggle" onclick="event.stopPropagation(); toggleRoster(this)" aria-expanded="false">&#9658; show</button></div><div class="gc-roster-body" style="display:none"><ul class="finding-bullets"><li>Outlaws and the lawmen hunting them &mdash; shelter and betrayal each carry a price, and the law is not always the more trustworthy of the two.</li><li>Chinese railroad laborers, Irish navvies, Scottish trappers, English land speculators &mdash; each carrying a different idea of what America is supposed to mean.</li><li>The missionary heading into territory everyone else is heading out of. The Army deserter. The Pinkerton who is not here by accident.</li><li>The Mexican family the law does not recognize as having rights to land they have worked for thirty years. The journalist writing the myth while it is still being made.</li></ul></div></div>
              </div>
              <div class="gc-doc-section" style="grid-column: 1 / -1"><div class="finding-label">Thematic DNA &amp; Influences</div><ul class="finding-bullets"><li>The title is not a historical reference. It is a design statement. Manifest Destiny as philosophy: the belief that will, applied with enough conviction, bends reality to match the picture in your head. The game is named after that idea because the game is that idea &mdash; fifty years of a single consciousness shaping what America becomes, one choice at a time. That is not a metaphor. That is the mechanic.</li><li>Manifest Destiny written in scripture and enacted in blood &mdash; the heroic and the self-interested arriving in no particular order.</li><li>Fallout 1 &amp; 2, Fallout: New Vegas &mdash; long-consequence choice architecture, faction reputation, a world that changes shape around your decisions.</li><li>Papers, Please, Red Dead Redemption 2, Deadwood (HBO).</li></ul></div>
            </div>
            <div class="gc-vibe">Fifty years is the right scope because it lets consequence breathe. A guest you helped in 1858 sends their daughter to your door in 1871. A reputation you built in the 1860s opens or closes the 1880s. The newspaper mechanic earns its complexity over time &mdash; what starts as a single monthly paper from one town becomes a chorus of competing accounts by the 1890s, and the player knows which version is true because they were there. Papers Please proved the threshold mechanic works. This is what happens when you build a whole life around it instead of a border checkpoint &mdash; and give it fifty years to settle. The title does all of that work in one word. To manifest something is to create reality from will &mdash; to bend the world to match the picture in your consciousness. That is exactly what the player does. That is exactly what the settlers believed they were doing. The game does not judge that. It just shows you what it costs and what it builds and lets the fifty years speak for themselves.</div>
          </div>
        </div>

        <!-- GC-005: BEAR'S BLOOMING FOREST -->
        <div class="gc-doc" id="gc-009" data-stage="specced" onclick="toggleGcCard(this)" style="animation-delay:0.14s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-009</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Bear&#x2019;s Blooming Forest</div><div class="gc-subtitle">Cozy Exploration &middot; Botanical Terraforming &middot; A Little Bear and a Very Large Plan</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-specced">Specced</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">Little Bear has a plan. The forest could be so full of flowers that the bees build a hive the size of a village, and the honey would just come to him. No fishing. No waiting. Just flowers, and then honey. He&#x2019;s going to need a lot of flowers. He should probably be back for dinner.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section">
                <div class="finding-label">The Two Halves</div>
                <div style="display:flex; flex-direction:column; gap:10px; margin-top:4px;">
                  <div style="background:rgba(6,214,160,0.07); border:1px solid rgba(6,214,160,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--green); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Gathering &mdash; the Zelda half</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Third-person exploration of biomes, each with its own puzzle logic, hazards, and feel. Flowers don&#x2019;t grow in safe places. Getting to them is the game.</p>
                  </div>
                  <div style="background:rgba(232,255,71,0.05); border:1px solid rgba(232,255,71,0.15); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Tending &mdash; the Harvest Moon half</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Planting, watering, maintaining, and expanding the garden back home. Healthy patches attract more bees. The hive grows one comb at a time until it becomes a village.</p>
                  </div>
                  <p style="font-size:11px; color:var(--text-dim); line-height:1.7; font-style:italic; padding-left:2px;">The tutorial ends with Little Bear placing a small jar beneath the hive. One drop falls. Everything else is the consequence of making that drop into a river.</p>
                </div>
              </div>
              <div class="gc-doc-section">
                <div class="finding-label">Gathering Mechanics</div>
                <ul class="finding-bullets">
                  <li>Early biomes are gentle puzzles &mdash; a wolf sleeping across the path, distracted by bait; a hawk circling a meadow, driven off by a friend with a loud bell. Solutions are obvious, tools are few, stakes are low.</li>
                  <li>Later biomes stack hazards and introduce timing &mdash; a mountain pass where the bait needs to reach the eagle before the wind window closes, or a desert where the rare bloom only opens at dawn and a scorpion guards the only route.</li>
                  <li>Animal companions change the calculus: a recruited bear friend acts as a presence deterrent, a fox can negotiate passage, a deer creates a distraction by existing somewhere interesting. You never fight. You redirect.</li>
                  <li>Some flowers require multiple trips to understand &mdash; the puzzle is figuring out the pattern before you attempt the collect.</li>
                </ul>
              </div>
              <div class="gc-doc-section" style="grid-column: 1 / -1">
                <div class="finding-label">Little Bear&#x2019;s Toolkit</div>
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-top:4px;">
                  <div style="background:rgba(77,171,247,0.07); border:1px solid rgba(77,171,247,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--blue); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Slingshot &mdash; ranged</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Two ammo types: bait draws animals toward the impact point; pebbles create noise without attracting anything. Both too small to hurt anything. He&#x2019;s not throwing rocks at a wolf &mdash; he&#x2019;s throwing a rock at a bush near a wolf.</p>
                  </div>
                  <div style="background:rgba(255,140,66,0.07); border:1px solid rgba(255,140,66,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--orange); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Garden Trowel &mdash; primary</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Planting, transplanting, and soil preparation. The first tool Little Bear owns and the one he&#x2019;s never without. Upgrades let him work faster and handle tougher terrain, but it&#x2019;s always just a trowel.</p>
                  </div>
                  <div style="background:rgba(180,100,255,0.07); border:1px solid rgba(180,100,255,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:#c87fff; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Fox&#x2019;s Network &mdash; unlockables</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">A bell on a string for sustained noise; a hollow reed that mimics bird calls; a small lantern for bloom-window timing in dark caves. Each solves a class of puzzle the slingshot alone cannot. All sourced through Fox.</p>
                  </div>
                </div>
              </div>
              <div class="gc-doc-section">
                <div class="finding-label">Seasons &amp; Time</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:4px;">
                  <div style="background:rgba(255,180,200,0.07); border:1px solid rgba(255,180,200,0.25); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:#ffb0c8; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Spring</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.6;">Peak rare blooms. Two-week windows that won&#x2019;t come again for a year. Cherry trees planted in year one finally matter. Miss spring and you plan around it until next spring.</p>
                  </div>
                  <div style="background:rgba(232,255,71,0.05); border:1px solid rgba(232,255,71,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Summer</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.6;">Peak bee activity. Maximum honey production. The garden is loudest here. The best time for long gathering runs before the year turns.</p>
                  </div>
                  <div style="background:rgba(255,140,66,0.07); border:1px solid rgba(255,140,66,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--orange); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Autumn</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.6;">Preparation and late-blooming trees. Save seeds from annuals. Plan what changes before winter closes the routes. The garden is winding down, not stopping.</p>
                  </div>
                  <div style="background:rgba(160,200,255,0.06); border:1px solid rgba(160,200,255,0.18); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:#a0c8ff; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Winter</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.6;">Quiet maintenance. A few hardy trees hold the bees over. Planning time: what biome next, which flowers, which companions to deploy when thaw comes.</p>
                  </div>
                </div>
                <p style="font-size:11px; color:var(--text-dim); line-height:1.7; margin-top:10px; font-style:italic;">Perennials regrow reliably, annuals must be replanted, and flowering trees planted early become significant bloom sources years later.</p>
              </div>
              <div class="gc-doc-section">
                <div class="finding-label">Biomes &amp; Progression</div>
                <div style="display:flex; flex-direction:column; gap:6px; margin-top:4px;">
                  <div style="background:rgba(6,214,160,0.07); border:1px solid rgba(6,214,160,0.25); border-radius:4px; padding:8px 12px; display:flex; align-items:baseline; gap:10px;">
                    <div style="font-size:10px; font-weight:700; color:var(--green); text-transform:uppercase; letter-spacing:0.1em; white-space:nowrap; min-width:110px;">Home Forest</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.5; margin:0;">Tutorial. Familiar and forgiving. The hive starts here.</p>
                  </div>
                  <div style="background:rgba(232,255,71,0.05); border:1px solid rgba(232,255,71,0.2); border-radius:4px; padding:8px 12px; display:flex; align-items:baseline; gap:10px;">
                    <div style="font-size:10px; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:0.1em; white-space:nowrap; min-width:110px;">Grasslands</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.5; margin:0;">Open space, seasonal wind. The game breathes here. Wide puzzles, room to experiment.</p>
                  </div>
                  <div style="background:rgba(200,200,220,0.06); border:1px solid rgba(200,200,220,0.18); border-radius:4px; padding:8px 12px; display:flex; align-items:baseline; gap:10px;">
                    <div style="font-size:10px; font-weight:700; color:#c8c8dc; text-transform:uppercase; letter-spacing:0.1em; white-space:nowrap; min-width:110px;">Mountain</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.5; margin:0;">Altitude, narrow paths, territorial birds. Vertical traversal puzzles.</p>
                  </div>
                  <div style="background:rgba(77,171,247,0.07); border:1px solid rgba(77,171,247,0.25); border-radius:4px; padding:8px 12px; display:flex; align-items:baseline; gap:10px;">
                    <div style="font-size:10px; font-weight:700; color:var(--blue); text-transform:uppercase; letter-spacing:0.1em; white-space:nowrap; min-width:110px;">Subtropical Coast</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.5; margin:0;">Tide timing, crabs, mangrove tangles. Flowers at the waterline only.</p>
                  </div>
                  <div style="background:rgba(255,140,66,0.07); border:1px solid rgba(255,140,66,0.25); border-radius:4px; padding:8px 12px; display:flex; align-items:baseline; gap:10px;">
                    <div style="font-size:10px; font-weight:700; color:var(--orange); text-transform:uppercase; letter-spacing:0.1em; white-space:nowrap; min-width:110px;">Desert</div>
                    <p style="font-size:11px; color:var(--text-mid); line-height:1.5; margin:0;">Heat management, nocturnal hazards, bloom windows. The hardest flowers. Unlocks last.</p>
                  </div>
                </div>
                <p style="font-size:11px; color:var(--text-dim); line-height:1.7; margin-top:10px; font-style:italic;">Each biome unlocks a bee variety the hive needs for its next tier. Biomes are progression gates &mdash; not level numbers.</p>
              </div>
              <div class="gc-doc-section" style="grid-column: 1 / -1">
                <div class="finding-label">Animal Companions</div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 4px;">
                  <div>
                    <div class="finding-label" style="margin-bottom: 6px; font-size: 8px;">Specialists &mdash; permanent, passive world changes</div>
                    <ul class="finding-bullets">
                      <li><strong>Deer</strong>
                        <div style="padding-left:10px; margin-top:2px; color:var(--text-dim); font-size:11px; line-height:1.6;">Clears bramble and opens new territory passively while grazing.</div>
                      </li>
                      <li><strong>Beaver</strong>
                        <div style="padding-left:10px; margin-top:2px; color:var(--text-dim); font-size:11px; line-height:1.6;">Builds irrigation channels, unlocking flower beds that need constant water.</div>
                      </li>
                      <li><strong>Fox</strong>
                        <div style="padding-left:10px; margin-top:2px; color:var(--text-dim); font-size:11px; line-height:1.6;">Negotiates with animals who won&#x2019;t be bribed; unlocks the later companion roster and the toolkit upgrade chain.</div>
                      </li>
                      <li><strong>Other Bears</strong>
                        <div style="padding-left:10px; margin-top:2px; color:var(--text-dim); font-size:11px; line-height:1.6;">Recruited one by one, each with a personality. The only ones who can fully substitute for Little Bear on harder gathering runs. His father never finds out they exist.</div>
                      </li>
                    </ul>
                  </div>
                  <div>
                    <div class="finding-label" style="margin-bottom: 6px; font-size: 8px;">Crew &mdash; deployed daily on maintenance &amp; support</div>
                    <ul class="finding-bullets">
                      <li><strong>Rabbit</strong>
                        <div style="padding-left:10px; margin-top:2px; color:var(--text-dim); font-size:11px; line-height:1.6;">Watering. Fast, covers multiple patches per cycle and scales well as the garden grows.</div>
                      </li>
                      <li><strong>Owl</strong>
                        <div style="padding-left:10px; margin-top:2px; color:var(--text-dim); font-size:11px; line-height:1.6;">Scouting. Surveys new territory and flower locations before Little Bear commits to traveling there.</div>
                      </li>
                      <li><strong>Hedgehog</strong>
                        <div style="padding-left:10px; margin-top:2px; color:var(--text-dim); font-size:11px; line-height:1.6;">Pest control. Protects patches from aphids, slugs, and herbivores that damage bloom yield.</div>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
              <div class="gc-doc-section">
                <div class="finding-label">Narrative Arc &amp; Tone</div>
                <ul class="finding-bullets">
                  <li>Little Bear is not sneaking. He&#x2019;s just very busy and hasn&#x2019;t quite explained it yet. The register is Winnie the Pooh: solo, whimsical, entirely sincere, driven by one very specific and honey-related goal. No responsibilities. No drama. Just a small bear who has a plan and is working on it.</li>
                  <li>Dad is flavor, not threat. He shows up occasionally &mdash; calling Little Bear in for dinner, suggesting they go fishing Sunday, cheerfully oblivious to the scale of what&#x2019;s happening in the forest. These moments create soft daily rhythm without pressure. Be back for dinner. Sunday is fishing. The rest of the day is yours.</li>
                  <li>Dad doesn&#x2019;t find out until the story reaches it naturally. The reveal isn&#x2019;t a confrontation &mdash; it&#x2019;s a father standing at the edge of a bee village, not entirely sure when this happened, watching honey drip into a jar below a hive the size of a house. He doesn&#x2019;t say anything for a long time. Then: &ldquo;You could have just asked me to fish more.&rdquo; Little Bear hands him the jar.</li>
                  <li>Scope: one bear, one valley, five biomes, three in-game years. Keep it small. Make it land.</li>
                </ul>
              </div>
              <div class="gc-doc-section">
                <div class="finding-label">Influences</div>
                <ul class="finding-bullets">
                  <li>The Legend of Zelda: Breath of the Wild &mdash; the gathering half; biome-specific puzzle logic; the joy of approaching a problem from an unexpected angle.</li>
                  <li>Stardew Valley &mdash; seasonal tending rhythm; the satisfying accumulation of a garden over years.</li>
                  <li>Pikmin &mdash; the deploy-and-multiply companion loop; small friends with distinct, complementary abilities.</li>
                  <li>Winnie the Pooh &mdash; the emotional register and the bear&#x2019;s relationship with honey. Gentle, single-minded, entirely sincere.</li>
                  <li>Pixar&#x2019;s Brave / Over the Hedge &mdash; the family tension structure: a child doing something the parent can&#x2019;t understand until the moment they finally see it.</li>
                </ul>
              </div>
            </div>
            <div class="gc-vibe">The emotional register is Winnie the Pooh, not Pixar. Little Bear isn&#x2019;t processing anything. He just wants honey and has a very reasonable theory about how flowers and bees work. Dad is there because Dad is always there &mdash; fishing, calling him in for dinner, suggesting Sunday plans. The family structure creates a gentle daily rhythm without stakes. There is no suspicion meter. There is no secret to manage. There is just a small bear with a large project and a soft deadline of dinnertime. The game is a cozy thing. It should feel like one.</div>
          </div>
        </div>

        <!-- GC-006: SWAN MARRIAGE COUNSELOR -->
        <div class="gc-doc" id="gc-005" data-stage="specced" onclick="toggleGcCard(this)" style="animation-delay:0.17s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-005</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Swan Marriage Counselor</div><div class="gc-subtitle">Therapy Visual Novel &middot; Lifelong Commitment &middot; Determinism vs. Choice</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-specced">Specced</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">Swans mate for life. Some of them are not handling it well. You are their counselor. The sessions that follow are about commitment, compromise, aging, and whether the promises we make when young should bind the people we become.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section"><div class="finding-label">Core Premise</div><ul class="finding-bullets"><li>The player is a marriage counselor to swan couples. Literal swans, with the biology of lifelong monogamy built in. These animals have no choice about who they&#x2019;re bound to.</li><li>Sessions explore the fault lines of long commitment: the distance that opens between people who grow in different directions; the resentment of a promise made without full information.</li><li>The subversion of the dating sim: dating sims are about the beginning of love. This game is about what happens after the win, when the romance has become a life and the life has become complicated.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Thematic DNA</div>
                <div style="display:flex; flex-direction:column; gap:8px; margin-top:4px;">
                  <div style="background:rgba(255,140,66,0.07); border:1px solid rgba(255,140,66,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--orange); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Determinism vs. Choice</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Swans are biologically determined to stay. Humans choose to. The game asks what that difference means for the moral weight of commitment &mdash; and whether the players in these sessions understand which one they are.</p>
                  </div>
                  <div style="background:rgba(77,171,247,0.07); border:1px solid rgba(77,171,247,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:var(--blue); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">The Problem of the Self Over Time</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">The person you promised yourself to at 22 is not the person in front of you at 47. The sessions don&#x2019;t ask whether the promise was sincere. They ask whether sincerity is enough.</p>
                  </div>
                  <div style="background:rgba(180,100,255,0.07); border:1px solid rgba(180,100,255,0.2); border-radius:4px; padding:10px 12px;">
                    <div style="font-size:10px; font-weight:700; color:#c87fff; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Aging as Theme, Not Backdrop</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Explicitly about couples who have been together long enough to become strangers. Not a game about falling in love. A game about what happens when the love has become a life and the life has become complicated.</p>
                  </div>
                </div>
              </div>
              <div class="gc-doc-section"><div class="finding-label">Influences</div><ul class="finding-bullets"><li>Florence &mdash; visual novel about the emotional reality of a relationship over time, not just its peak.</li><li>The Sopranos &mdash; therapy as a tool for self-reflection, metamorphosis, ideation, and sometimes delusion. Tony Soprano did not want to get better; he wanted permission to stay the same. Some of these swans have the same problem.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Commercial Note</div><ul class="finding-bullets"><li>Niche audience but a devoted one. Strong festival circuit potential &mdash; Indiecade, IGF.</li><li>Low asset requirement. The game lives in session dialogue. A small team with one strong writer could complete this.</li><li>Replayability is intentionally limited per couple &mdash; each pair&#x2019;s story is a fixed arc, like a short film. The replay value comes from the roster: multiple couples, each with distinct dynamics, fault lines, and endpoints. A player who finishes one couple&#x2019;s sessions picks up the next and finds a structurally different emotional problem. The game is a collection of short films, not a single long one.</li><li>Counselor choices carry weight across couples &mdash; a reputation for bluntness, warmth, or detachment can subtly shift how later clients open up. This creates a soft meta-layer without undermining each couple&#x2019;s standalone integrity.</li></ul></div>
            </div>
            <div class="gc-vibe">Low asset count, strong festival profile, and a demographic that games mostly ignore: people in long relationships. The swan framing isn&#x2019;t cute window dressing; it&#x2019;s the central mechanical question. Swans don&#x2019;t choose to stay. The player&#x2019;s job is to help couples who do choose work through what that costs. That&#x2019;s a different emotional register than anything currently in the visual novel space.</div>
          </div>
        </div>

        <!-- GC-007: WARP GUN -->
        <div class="gc-doc" id="gc-008" data-stage="specced" onclick="toggleGcCard(this)" style="animation-delay:0.20s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-008</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Warp Gun</div><div class="gc-subtitle">First-Person Puzzle &middot; Spacetime Distortion &middot; Light &amp; Traversal</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-specced">Specced</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">Instead of a portal gun, a warp gun. Two modes: contraction and expansion. Spacetime bends around your shots. Light curves. Distances collapse or stretch. Puzzles are solved not by placing doors in walls, but by reshaping the space between you and the solution.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section" style="grid-column: 1 / -1"><div class="finding-label">Core Mechanics</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:4px; margin-bottom:10px;">
                  <div style="background:rgba(77,171,247,0.07); border:1px solid rgba(77,171,247,0.25); border-radius:4px; padding:12px 14px;">
                    <div style="font-size:10px; font-weight:700; color:var(--blue); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:6px;">Contraction</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Localized gravity well. Space folds inward, pulling objects and the player toward the distortion point. Distances collapse. Light paths curve toward the impact. The slingshot technique: jump into the well&#x2019;s pull at the right angle, then deactivate the field before it draws you back &mdash; the arrested momentum launches you across distances no normal jump could reach. Impassable gaps become traversable. The tool is the launch pad.</p>
                  </div>
                  <div style="background:rgba(255,140,66,0.07); border:1px solid rgba(255,140,66,0.25); border-radius:4px; padding:12px 14px;">
                    <div style="font-size:10px; font-weight:700; color:var(--orange); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:6px;">Expansion</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Space pushed outward from the impact point. Geometry stretches and reshapes around the distortion &mdash; a flat wall hit at an angle warps into a curved ramp; a floor expands into a traversable slope. Perceived distances grow. Projectiles and light beams deflect along new paths. The environment is not fixed; it is a variable the player sets.</p>
                  </div>
                </div>
                <ul class="finding-bullets">
                  <li>Light bending is not cosmetic &mdash; it is a puzzle input. Beams that need to hit targets must be routed through warp fields. The curvature is the mechanic.</li>
                  <li>Traversal puzzles emerge from two warp types interacting: a contraction slingshot launches you across a gap that an expansion has reshaped into a landing surface, or a light beam bent by contraction threads through a gap that expansion has opened.</li>
                  <li>The slingshot is a skill move, not just a technique: timing the deactivation of a contraction field at peak pull velocity gives the player momentum that compounds with expansion geometry &mdash; the two modes create movement freedom that neither produces alone.</li>
                </ul>
              </div>
              <div class="gc-doc-section"><div class="finding-label">Design Space</div><ul class="finding-bullets"><li>The distortion fields have a visual presence &mdash; space visibly shimmers, geometry warps at the field boundary, light halos around the contraction point. The world communicates the physics before the player tests it.</li><li>Puzzle difficulty scales by stacking warp interactions: early puzzles use one shot type in isolation; later puzzles require both simultaneously, with each distortion field affecting the other&#x2019;s geometry.</li><li>The setting can leverage the visual language directly: environments where geometry and perspective are already disorienting make warp distortion feel native rather than intrusive.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Influences</div><ul class="finding-bullets"><li>Portal &mdash; the single-tool puzzle design philosophy; the tool is the world&#x2019;s grammar, not a power layered on top of it.</li><li>Antichamber &mdash; non-Euclidean space as a puzzle medium; the willingness to let perception be wrong and make that wrongness mechanical.</li><li>Interstellar / actual gravitational lensing &mdash; the visual reference for what a real contraction field would look like to someone standing inside the light path.</li></ul></div>
            </div>
            <div class="gc-vibe">Portal works because the portal gun is a spatial language, not just a tool. The warp gun needs the same thing: every puzzle is a sentence written in distortion. The light-bending mechanic is the element that separates this from Portal reskin territory &mdash; routing light is a fundamentally different cognitive task than routing a player. The slingshot technique is where the movement ceiling lives: players who understand contraction timing and expansion geometry get traversal freedom that the puzzle design doesn&#x2019;t require but rewards. That emergent skill ceiling is what makes a tool feel like a language.</div>
          </div>
        </div>

        <!-- GC-008: WINTER STORM -->
        <div class="gc-doc" id="gc-006" data-stage="concept" onclick="toggleGcCard(this)" style="animation-delay:0.23s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-006</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Winter Storm</div><div class="gc-subtitle">PVP Extraction Shooter &middot; Arctic Blizzard &middot; Strategic Infiltration &amp; Exfiltration</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-concept">Concept</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">A PVP extraction shooter set in Arctic blizzards. Squads infiltrate, locate the objective, and fight their way out. The storm is not the enemy &mdash; the other team is. Every footprint you leave can be tracked. Every footprint they leave can too.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section" style="grid-column: 1 / -1"><div class="finding-label">Core Systems</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:4px; margin-bottom:10px;">
                  <div style="background:rgba(160,200,255,0.06); border:1px solid rgba(160,200,255,0.18); border-radius:4px; padding:12px 14px;">
                    <div style="font-size:10px; font-weight:700; color:#a0c8ff; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:6px;">Infiltration &mdash; the Blizzard Is Cover</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Whiteout conditions blind the enemy but also blind sensors, create acoustic interference, and mask heat signatures. The storm isn&#x2019;t fighting you &mdash; it&#x2019;s the best tool you have. Every footprint you leave can be tracked. Every footprint they leave can too.</p>
                  </div>
                  <div style="background:rgba(255,77,77,0.07); border:1px solid rgba(255,77,77,0.2); border-radius:4px; padding:12px 14px;">
                    <div style="font-size:10px; font-weight:700; color:var(--red); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:6px;">Exfiltration &mdash; Snowmobile Set Piece</div>
                    <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">The stealth phase ends. The extraction begins. High-speed snowmobile exfiltration as a structural gear shift: you came in quiet, you leave fast, and the other squad knows exactly where you are.</p>
                  </div>
                </div>
                <ul class="finding-bullets">
                  <li>Thermal imaging and heartbeat sensors as detection tools. Enemy use of them forces cat-and-mouse between environmental concealment and technological detection.</li>
                  <li>Footprint persistence: snow records movement. Players must plan routes considering what evidence they leave behind.</li>
                </ul>
              </div>
              <div class="gc-doc-section"><div class="finding-label">Design Gap</div><ul class="finding-bullets"><li>The aesthetic is fully realized. The setting is evocative. The mechanical hooks are genuinely interesting.</li><li>Missing: a narrative reason to care. Metal Gear works not because of its stealth mechanics but because Kojima built a mythology around them.</li><li>Current status: the PVP extraction framing solves the original narrative problem: the other squad is the story. Revisiting.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Influences</div><ul class="finding-bullets"><li>Metal Gear Solid series &mdash; gadget economy, environmental stealth, the idea that preparation is half the mission.</li><li>Call of Duty: MW2 &mdash; the snowmobile chase and Cliffhanger mission specifically; proof that an arctic infiltration set piece can be genuinely cinematic without sacrificing player agency.</li><li>Escape from Tarkov &mdash; the tension architecture of extraction: you brought good gear in, now you have to get it out.</li></ul></div>
            </div>
            <div class="gc-vibe">The extraction shooter market is crowded but nobody has committed to a full blizzard environment as a core design pillar &mdash; not as a weather effect, as the entire tactical premise. The footprint mechanic alone differentiates this from Tarkov: every route is a decision about what you leave behind, and the other squad is reading the same snow. The narrative gap is acknowledged and being addressed. The PVP frame solves it cleanly &mdash; the other squad is the story, the blizzard is the referee, and the snowmobile is the gear shift that ends every match with momentum. The bones are strong. This one needs a mythology built around them.</div>
          </div>
        </div>

        <!-- GC-009: CONQUISTADOR SIM -->
        <div class="gc-doc" id="gc-007" data-stage="concept" onclick="toggleGcCard(this)" style="animation-delay:0.26s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-007</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Conquistador Sim</div><div class="gc-subtitle">Political Simulation &middot; New World Exploration &middot; God &middot; Guns &middot; Gold</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-concept">Concept</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">You are a Spanish explorer in the New World. Work for the Crown, defect and conquer on your own terms like Cort&#xe9;s, or abandon Europe entirely and disappear into a continent that has been here ten thousand years longer than your maps. Three paths. Only one of them requires you to stop seeing the land as something to be taken.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section" style="grid-column: 1 / -1"><div class="finding-label">Core Factions / Paths</div><div style="display:flex; flex-direction:column; gap:8px; margin-top:4px;">
                <div style="background:rgba(77,171,247,0.07); border:1px solid rgba(77,171,247,0.2); border-radius:4px; padding:10px 12px;">
                  <div style="font-size:10px; font-weight:700; color:var(--blue); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Crown Loyalist</div>
                  <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">The institutional path. Supplied, supported, and expendable. High demand, high reward. The Crown owns your success.</p>
                </div>
                <div style="background:rgba(255,77,77,0.07); border:1px solid rgba(255,77,77,0.2); border-radius:4px; padding:10px 12px;">
                  <div style="font-size:10px; font-weight:700; color:var(--red); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Renegade &mdash; the Cort&#xe9;s Path</div>
                  <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Defection and conquest on personal terms. No supply lines, no safety net. If the Crown must negotiate with you, you&#x2019;ve won.</p>
                </div>
                <div style="background:rgba(6,214,160,0.07); border:1px solid rgba(6,214,160,0.2); border-radius:4px; padding:10px 12px;">
                  <div style="font-size:10px; font-weight:700; color:var(--green); text-transform:uppercase; letter-spacing:0.1em; margin-bottom:4px;">Gone Native &mdash; the Kurtz Path</div>
                  <p style="font-size:12px; color:var(--text-mid); line-height:1.7;">Abandon European frameworks entirely &mdash; not just politically, epistemologically. The most demanding path. The only one where the continent stops trying to kill you.</p>
                </div>
              </div></div>
              <div class="gc-doc-section"><div class="finding-label">Core Systems</div><ul class="finding-bullets"><li>Translation as a mechanic &mdash; language barriers are real and consequential. Miscommunication with tribes produces outcomes the player did not intend.</li><li>Tribal politics with genuine complexity: alliances, rivalries, territorial conflicts. The player enters a political environment that predates them and will outlast them.</li><li>The Gone Native path requires operating inside a worldview where the land is not a resource, where balance and reciprocity govern every action, where the cycle of life and death demands acknowledgment. It asks the player to unlearn what the other two paths treat as obvious. That is the design challenge and the point.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Design Problem</div><ul class="finding-bullets"><li>This concept is enormous. Translation systems, tribal relationship graphs, three divergent path structures &mdash; any one of these would be a major system in another game.</li><li>Needs a version that is 80% smaller &mdash; a proof of concept, not a full simulation.</li><li>The Conquista is genuinely underexplored in games. This deserves to exist. The question is when and at what scale.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Influences</div><ul class="finding-bullets"><li>Apocalypse Now / Heart of Darkness &mdash; the gone-native path&#x2019;s psychological architecture.</li><li>Crusader Kings III &mdash; faction diplomacy, shifting allegiances, personal ambition at the expense of the institution.</li><li>Civilization series &mdash; the 4X framework for expansion, city management, and nation-building.</li></ul></div>
            </div>
            <div class="gc-vibe">The translation mechanic and the three-path structure are both worth building. Just not at the same time, at full scale, as a first project. Needs a proof-of-concept version that is roughly 20% of this scope. The setting is too underrepresented in games to abandon entirely.</div>
          </div>
        </div>

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
  <div>Boston, MA &nbsp;&middot;&nbsp; wendell91097@gmail.com &nbsp;&middot;&nbsp; (228) 237-6193</div>
</footer>

<script>
{filter_js}
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Output written to {output_path}")
    print(f"  {total_bugs} bugs | {len(case_studies)} case studies | 9 game concepts")


if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    build_dashboard(
        bugs_json_path        = os.path.join(base, "bugs.json"),
        case_studies_json_path= os.path.join(base, "case_studies.json"),
        output_path           = os.path.join(base, "index.html"),
    )
