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
    "collision":  {"label": "Collision / Physics"},
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
}


# ── HTML GENERATORS — BUG REPORTS ─────────────────────────────────────────────

def make_video_embed(bug: dict) -> str:
    url = bug.get("video_url", "").strip()
    text = bug.get("video_text", "Add YouTube link here")

    if url:
        embed_url = url
        if "youtube.com/watch?v=" in url:
            vid_id = url.split("watch?v=")[-1].split("&")[0]
            embed_url = f"https://www.youtube.com/embed/{vid_id}"
        elif "youtu.be/" in url:
            vid_id = url.split("youtu.be/")[-1].split("?")[0]
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
    else:
        return f"""
          <div class="video-placeholder">
            <div class="video-icon">▶</div>
            <span>Clip pending upload</span>
            <a href="https://youtube.com" target="_blank">{escape(text)}</a>
          </div>"""


def make_repro_steps(steps: list) -> str:
    items = ""
    for i, step in enumerate(steps, 1):
        num = str(i).zfill(2)
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
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    items = "".join(f"<li>{s}</li>" for s in sentences)
    return f'<ul class="finding-bullets">{items}</ul>'


def make_finding_row(finding: dict) -> str:
    risk = finding.get("risk_level", "Low")
    risk_cfg = RISK_CONFIG.get(risk, {"css_class": "risk-low"})
    rec_html = ""
    if finding.get("recommendation"):
        rec_html = f"""
                    <div style="margin-top:12px">
                      <div class="finding-label">Recommendation</div>
                      {make_bullet_list(finding.get('recommendation', ''))}
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
                  </div>
                  <div class="finding-col">
                    <div class="finding-label">Forward Risk</div>
                    {make_bullet_list(finding.get('forward_risk', ''))}
                    {rec_html}
                  </div>
                </div>
              </div>"""


def make_case_study_card(cs: dict) -> str:
    findings_html = "".join(make_finding_row(f) for f in cs.get("findings", []))
    high_count = sum(1 for f in cs.get("findings", []) if f.get("risk_level") == "High")
    mod_count  = sum(1 for f in cs.get("findings", []) if f.get("risk_level") == "Moderate")

    return f"""
      <div class="cs-card" onclick="toggleCsCard(this)">
        <div class="cs-card-header">
          <div class="bug-id">{escape(cs.get('id', ''))}</div>
          <div class="cs-classification">{escape(cs.get('classification', ''))}</div>
          <div class="cs-title">{escape(cs.get('title', ''))}</div>
          <div class="cs-meta">
            <span class="risk-badge risk-high">{high_count} High</span>
            <span class="risk-badge risk-moderate">{mod_count} Moderate</span>
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


def make_sidebar(bugs: list) -> str:
    game_counts = Counter(b["game"] for b in bugs)
    sev_counts  = Counter(b["severity"] for b in bugs)
    type_counts = Counter(b["type"] for b in bugs)
    total       = len(bugs)

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

    type_btns = ""
    for type_key, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        label = TYPE_CONFIG.get(type_key, {}).get("label", type_key.title())
        type_btns += f"""
      <button class="filter-btn" onclick="filterBugs('{type_key}', this)">
        {escape(label)}
        <span class="filter-count">{count}</span>
      </button>"""

    return f"""  <aside class="sidebar">
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
  </aside>"""


def make_stats_bar(bugs: list) -> str:
    total_bugs   = len(bugs)
    unique_games = len({
        gk for gk in set(b["game"] for b in bugs)
        if GAME_CONFIG.get(gk, {}).get("tier") == "AAA"
    })

    return f"""<div class="stats-bar">
  <div class="stat-item">
    <div class="stat-value">{total_bugs}</div>
    <div class="stat-label">Documented Bugs</div>
  </div>
  <div class="stat-item">
    <div class="stat-value">{unique_games}</div>
    <div class="stat-label">AAA Titles Tested</div>
  </div>
  <div class="stat-item">
    <div class="stat-value">100+</div>
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
    Available — Remote
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
    const wasExpanded = card.classList.contains('expanded');
    document.querySelectorAll('.bug-card').forEach(c => c.classList.remove('expanded'));
    if (!wasExpanded) card.classList.add('expanded');
  }}

  function toggleCsCard(card) {{
    const wasExpanded = card.classList.contains('expanded');
    document.querySelectorAll('.cs-card').forEach(c => c.classList.remove('expanded'));
    if (!wasExpanded) card.classList.add('expanded');
  }}

  function filterBugs(filter, btn) {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const gameKeys = {game_list};
    const sevKeys  = {sev_list};
    const typeKeys = {type_list};

    const cards = document.querySelectorAll('.bug-card');
    let visible = 0;

    cards.forEach(card => {{
      const game = card.dataset.game;
      const severity = card.dataset.severity;
      const type = card.dataset.type;

      let show = false;
      if (filter === 'all')              show = true;
      else if (gameKeys.includes(filter)) show = game === filter;
      else if (sevKeys.includes(filter))  show = severity === filter;
      else if (typeKeys.includes(filter)) show = type === filter;

      card.classList.toggle('hidden', !show);
      if (show) visible++;
    }});

    document.getElementById('count').textContent = visible;
  }}

  function toggleGcCard(card) {{
    const wasExpanded = card.classList.contains('gc-expanded');
    document.querySelectorAll('.gc-doc').forEach(c => c.classList.remove('gc-expanded'));
    if (!wasExpanded) card.classList.add('gc-expanded');
  }}

  // Tab switching
  function switchTab(tab) {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    document.querySelector('.tab-btn[data-tab="' + tab + '"]').classList.add('active');
    document.getElementById('panel-' + tab).classList.remove('hidden');
    const sidebar = document.querySelector('.sidebar');
    const mainGrid = document.querySelector('.main');
    if (tab === 'bugs') {{
      sidebar.style.display = '';
      mainGrid.style.gridTemplateColumns = '220px 1fr';
    }} else {{
      sidebar.style.display = 'none';
      mainGrid.style.gridTemplateColumns = '1fr';
    }}
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
    content: "▸"; color: var(--accent); font-size: 9px;
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
  .video-placeholder a { color: var(--accent); text-decoration: none; font-size: 12px; font-weight: 600; }
  .video-placeholder a:hover { text-decoration: underline; }
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

  /* RISK BADGES — fit to content, no min-width */
  .risk-badge {
    font-size: 10px; font-weight: 700; padding: 3px 10px;
    border-radius: 3px; text-align: center; text-transform: uppercase;
    letter-spacing: 0.08em; white-space: nowrap; justify-self: end;
  }
  .risk-high          { background: rgba(255,77,77,0.15);    color: var(--critical); border: 1px solid rgba(255,77,77,0.3); }
  .risk-moderate      { background: rgba(255,140,66,0.15);   color: var(--major);    border: 1px solid rgba(255,140,66,0.3); }
  .risk-low           { background: rgba(77,171,247,0.15);   color: var(--visual);   border: 1px solid rgba(77,171,247,0.3); }
  .risk-low-moderate  { background: rgba(255,209,102,0.15);  color: var(--minor);    border: 1px solid rgba(255,209,102,0.3); }

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
  .skill-list-single .skill-item::before { content: '▸'; color: var(--accent); font-size: 9px; }

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
  .gc-flagship { border-color: rgba(232,255,71,0.25); }
  .gc-flagship:hover, .gc-flagship.gc-expanded { border-color: var(--accent); }
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
  .gc-title { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 14px; color: var(--text); }
  .gc-flagship .gc-title { color: var(--accent); }
  .gc-subtitle { font-size: 10px; color: var(--text-dim); letter-spacing: 0.04em; }
  .gc-doc-col-meta { display: flex; flex-direction: column; gap: 6px; align-items: flex-end; }
  .gc-stage-badge {
    font-size: 9px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.12em; padding: 3px 8px; border-radius: 3px; white-space: nowrap;
  }
  .gc-stage-concept   { background: rgba(77,171,247,0.12);  color: var(--visual); border: 1px solid rgba(77,171,247,0.25); }
  .gc-stage-specced   { background: rgba(255,209,102,0.12); color: var(--minor);  border: 1px solid rgba(255,209,102,0.25); }
  .gc-stage-prototype { background: rgba(6,214,160,0.12);   color: var(--green);  border: 1px solid rgba(6,214,160,0.25); }
  .gc-stage-shipped   { background: rgba(255,165,0,0.15);   color: #ffaa33;        border: 1px solid rgba(255,165,0,0.35); }
  .gc-flagship-badge {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em;
    color: var(--accent); background: rgba(232,255,71,0.1); border: 1px solid rgba(232,255,71,0.25);
    padding: 3px 8px; border-radius: 3px;
  }
  .gc-doc-body {
    display: none; border-top: 1px solid var(--border);
    padding: 20px 18px 24px; background: var(--bg3);
  }
  .gc-doc.gc-expanded .gc-doc-body { display: block; }
  .gc-doc-pitch {
    font-size: 13px; color: var(--text); line-height: 1.8; margin-bottom: 20px;
    font-style: italic; border-left: 2px solid var(--border-bright); padding-left: 14px;
  }
  .gc-flagship .gc-doc-pitch { border-left-color: var(--accent); }
  .gc-doc-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
  .gc-links {
    display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap;
  }
  .gc-link-btn {
    font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em;
    padding: 5px 12px; border-radius: 3px; text-decoration: none;
    border: 1px solid var(--border-bright); color: var(--text-dim);
    transition: color 0.15s, border-color 0.15s;
  }
  .gc-link-btn:hover { color: var(--accent); border-color: var(--accent); }
  .gc-link-btn.gc-link-primary { color: var(--accent); border-color: rgba(232,255,71,0.4); }
  .gc-link-btn.gc-link-primary:hover { border-color: var(--accent); }
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

    stats_bar   = make_stats_bar(bugs)
    sidebar     = make_sidebar(bugs)
    bug_cards   = "\n".join(make_bug_card(b) for b in bugs)
    filter_js   = make_filter_js(bugs)
    total_bugs  = len(bugs)
    unique_games = len({
        gk for gk in set(b["game"] for b in bugs)
        if GAME_CONFIG.get(gk, {}).get("tier") == "AAA"
    })

    cs_cards    = "\n".join(make_case_study_card(cs) for cs in case_studies)
    cs_count    = len(case_studies)

    all_games = []
    seen = set()
    for b in bugs:
        gk = b["game"]
        if gk not in seen:
            seen.add(gk)
            label = GAME_CONFIG.get(gk, {}).get("label", b.get("game_name", gk))
            all_games.append(label)

    titles_html = "\n".join(f'            <div class="skill-item">{escape(g)}</div>' for g in all_games)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wendell Lancaster — QA Portfolio &amp; Game Design</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>

<!-- HEADER -->
<header>
  <div class="header-left">
    <div class="logo-mark">WL</div>
    <div class="header-name">WENDELL LANCASTER</div>
    <div class="header-role">QA Tester &nbsp;·&nbsp; Game Developer &nbsp;·&nbsp; Designer</div>
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
      <button class="tab-btn" data-tab="game-concepts" onclick="switchTab('game-concepts')">// Game Concepts <span style="font-size:10px; opacity:0.6">(6)</span></button>
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
        <div class="result-count"><span>{cs_count}</span> evaluation{'' if cs_count == 1 else 's'}</div>
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

        <!-- GC-007: WORDSMITH -->
        <div class="gc-doc" onclick="toggleGcCard(this)" style="animation-delay:0.02s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-007</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Wordsmith</div><div class="gc-subtitle">Word Puzzle &middot; Letter Grid &middot; Pure Systems</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-shipped">Shipped</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">A word-finding puzzle game with no story, no characters, and no win condition you didn&#x2019;t set yourself. Grid of letters, three game modes, two tools. Find words, clear tiles, keep the grid alive.</div>
            <div class="gc-links">
              <a class="gc-link-btn gc-link-primary" href="https://sovereigndev.itch.io/wordsmith" target="_blank" onclick="event.stopPropagation()">&#9660; Play on itch.io</a>
              <a class="gc-link-btn" href="https://youtu.be/MCcAFdG_dV4" target="_blank" onclick="event.stopPropagation()">&#9654; Gameplay Video</a>
            </div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section"><div class="finding-label">Core Loop</div><ul class="finding-bullets"><li>The player navigates a letter grid ranging from 4&times;4 to 8&times;8 and traces valid words in any direction &mdash; horizontal, vertical, diagonal &mdash; without reusing the same letter twice per word.</li><li>Valid words remove their letters from the grid. The tiles above cascade down to fill the gap, Tetris-style. New letters generate from the top to keep the grid full at all times &mdash; the player never sees a half-empty board.</li><li>The Wordsmith hammer is a targeted tool: the player can use it to remove specific letters from the grid independently of word-making, creating space or breaking up bad distributions.</li><li>Shuffle resets the grid entirely when the current layout is unworkable.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Game Modes</div><ul class="finding-bullets"><li><strong>Classic</strong> &mdash; a set number of letters can be used before the round ends. The constraint is total throughput, not time. Rewards deliberate play.</li><li><strong>Timed</strong> &mdash; a player-set time limit. Same grid, different pressure. Rewards fast pattern recognition over optimization.</li><li><strong>Endless</strong> &mdash; no win condition, no loss condition. The grid runs indefinitely. Chill by design.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Design Notes</div><ul class="finding-bullets"><li>Retro pixel art aesthetic throughout, with parallax backgrounds sourced from open licensed assets with attribution. Settings allow music, SFX, and background swaps from the start screen.</li><li>Built in Godot. Released August 22, 2024. Windows desktop download, no installation required.</li><li>The cascade mechanic changes the strategic calculus compared to static-grid word games: clearing a cluster of letters reshapes the board, which creates new adjacencies and new problems simultaneously.</li><li>The hammer gives the player agency over the board state without requiring a full shuffle &mdash; a small tool that adds meaningful tactical decision-making without complicating the core loop.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Influences</div><ul class="finding-bullets"><li>Boggle &mdash; directional letter adjacency as the core word-finding structure.</li><li>Bookworm (PopCap) &mdash; tiles cleared on valid word submission, board management as an emergent challenge.</li><li>Tetris &mdash; gravity-based cascade as the feedback mechanism for clearing; the board as a living system rather than a static puzzle.</li></ul></div>
            </div>
            <div class="gc-vibe">This is the one card on the slate where the design question is already answered. It shipped. The rest of the concepts are documented to show how I think; this one is here to show that the thinking goes somewhere.</div>
          </div>
        </div>

        <div class="gc-doc gc-flagship" onclick="toggleGcCard(this)" style="animation-delay:0.05s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-006</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Immortal Coil</div><div class="gc-subtitle">Isometric Boxing &middot; Dystopian Arena Drama &middot; Transhumanist Horror</div></div>
            <div class="gc-doc-col-meta"><span class="gc-flagship-badge">&#9733; Flagship</span><span class="gc-stage-badge gc-stage-prototype" style="margin-top:4px">Prototype-Ready</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">All humans are immortal. The worst criminals are made to fight in arenas for public amusement. Win five championships and you earn the only thing anyone in this society still wants: the right to die.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section"><div class="finding-label">Core Premise</div><ul class="finding-bullets"><li>A technologically immortal society has eliminated death &mdash; except as a prize. The arena system exists not merely as punishment but as the only culturally sanctioned exit from existence.</li><li>The player character is a convicted criminal assigned to the Neo-Gladiator circuit. Bodies heal between bouts. Mental deterioration does not.</li><li>The champion is treated near-royally and must defend their title annually. Only a champion of sufficient consecutive victories earns the most coveted right in the world: self-euthanasia.</li><li>Spectators in the stands are prisoners of a different kind &mdash; trapped in a system so ancient and so technically incomprehensible that no one alive knows how to dismantle it. They watch because the alternative is confronting something they did not build and cannot unmake.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Mechanics</div><ul class="finding-bullets"><li>Isometric / 2.5D top-down perspective. Full kinetic movement vocabulary: dodge, duck, sidestep, backpedal, close in, hook, jab, uppercut, feint.</li><li>Cybernetic augmentations upgradeable between bouts &mdash; the tension between optimizing the body and losing what remains of selfhood is mechanical, not just thematic.</li><li>Massive prison transportation system as connective tissue between fights: the world seen through convoy windows, loading docks, holding cells.</li><li>Mental degradation modeled over time &mdash; early fights feel sharp; later fights feel like swimming through static.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Thematic DNA</div><ul class="finding-bullets"><li>Post-modernist collapse of meaning: when death is abolished, what does life cost?</li><li>Dehumanization through spectacle &mdash; gladiatorial Rome refracted through transhumanist technology so advanced it has become indistinguishable from nature. No one built this world; it simply is.</li><li>The apocalypse framework applied inward: not a ruined world but a ruined selfhood. Survival and identity in direct opposition.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Influences</div><ul class="finding-bullets"><li>Dark Souls &mdash; immortality as a curse rather than a gift; the hollow mechanic as a model for what repeated death costs the self over time.</li><li>Disco Elysium &mdash; the collapse of a moral framework as both world-building and gameplay.</li><li>Rollerball (1975) &mdash; sport as a tool of systemic dehumanization.</li><li>Warhammer 40,000 &mdash; civilization sustained by technology so ancient that maintaining it has become religious ritual; understanding it is no longer possible.</li><li>Neon Genesis Evangelion &mdash; the psychic cost of doing what the machine requires of you.</li></ul></div>
            </div>
            <div class="gc-vibe">The arena combat loop gives QA something concrete to test against: does augmentation feel like a tradeoff or just a power increase? Does the mental decay mechanic actually change how the player fights, or is it cosmetic? Those are real design questions with answers, which means this is a real game. The 40K comparison is intentional &mdash; the point is that the horror comes from normalcy, not from anyone being a villain. That&#x2019;s a harder thing to get right, and I know it.</div>
          </div>
        </div>

        <div class="gc-doc" onclick="toggleGcCard(this)" style="animation-delay:0.08s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-002</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Manifest</div><div class="gc-subtitle">Branching Narrative &middot; Frontier Homestead &middot; You Shape What America Becomes</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-specced">Specced</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">You have staked a claim on the frontier &mdash; a homestead at the crossroads of everything America is becoming. Every week someone new comes through. Some are running from something. Some are running toward something worth dying for. Every choice compounds. The country being built around you will remember what you did here.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section"><div class="finding-label">Core Premise &amp; Choice Architecture</div><ul class="finding-bullets"><li>The player is a fixed point while history moves through them. Choices are not isolated &mdash; they establish reputation, close doors, open others, and reshape the settlement growing around you over years of play. Think Fallout 1 and 2: decisions made in Act One are still paying out in Act Three.</li><li>Factions accumulate organically. Side with the railroad and the town booms but the families who were here first get pushed out. Harbor the outlaw and the law stops cooperating. Help the Underground Railroad and certain guests start arriving who would not otherwise trust you.</li><li>This was a deeply Christian nation. The moral vocabulary of the era is scripture &mdash; charity, sanctuary, bearing false witness. Turning someone away is not a neutral act.</li><li>The newspaper mechanic: weeks later, the penny press brings word. Some made it. Some are on wanted posters. Some names appear in obituaries with no next of kin listed.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">The Guests Who Matter Most</div><ul class="finding-bullets"><li><strong>The Comanche</strong> &mdash; traveling under a name that is not his. His sister is missing &mdash; taken from her people, though whether she ran or was taken he does not know. He needs one night&#x2019;s shelter and your silence. What do you do when the marshal comes asking the next morning?</li><li><strong>The conductor</strong> &mdash; a freed Black man who speaks like an educated minister, which is exactly what he is. Moving people north, he needs to know if your homestead is safe. This is the moment the Underground Railroad either routes through you or does not.</li><li><strong>The teacher</strong> &mdash; heading to a mining camp that does not know it needs her. She carries a crate of books and more faith in people than the frontier has earned. Whether she makes it depends partly on what you tell her about the road ahead.</li><li><strong>The pastor</strong> &mdash; road-worn, theologically complicated, genuinely kind. He will accept a free night&#x2019;s stay and leave something worth considerably more. He is also the one guest who will tell you plainly what he thinks you are doing wrong with your life. He is usually right.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">The Fuller Roster</div><ul class="finding-bullets"><li>Outlaws and the lawmen hunting them &mdash; shelter and betrayal each carry a price, and the law is not always the more trustworthy of the two.</li><li>Chinese railroad laborers, Irish navvies, Scottish trappers, English land speculators &mdash; each carrying a different idea of what America is supposed to mean.</li><li>The missionary heading into territory everyone else is heading out of. The Army deserter who saw something he will not describe. The Pinkerton who is not here by accident.</li><li>The Mexican family the law does not recognize as having rights to land they have worked for thirty years. The journalist writing the myth while it is still being made.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Thematic DNA &amp; Influences</div><ul class="finding-bullets"><li>Manifest Destiny written in scripture and enacted in blood &mdash; the heroic and the self-interested arriving at your door in no particular order.</li><li>The question underneath every interaction: whose America are you building? And: does God have an opinion about that?</li><li>Fallout 1 &amp; 2, Fallout: New Vegas &mdash; long-consequence choice architecture, faction reputation, a world that changes shape around your decisions. Papers, Please, Red Dead Redemption 2, Deadwood (HBO).</li></ul></div>
            </div>
            <div class="gc-vibe">The gap this fills is pretty straightforward: faction reputation systems in games like New Vegas are excellent, but you&#x2019;re always the one moving through the world. Flipping that &mdash; you&#x2019;re stationary, the world moves through you &mdash; is a structural difference that changes what choices mean. Papers Please proved the threshold mechanic works. This is what happens when you build a whole world around it instead of a border checkpoint.</div>
          </div>
        </div>

        <div class="gc-doc" onclick="toggleGcCard(this)" style="animation-delay:0.11s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-004</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Playground Noir</div><div class="gc-subtitle">Mystery Visual Novel &middot; Kindergarten Ace Attorney &middot; Unreliable Witnesses</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-prototype">Prototype-Ready</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">The last cookie has been eaten. The daycare is in crisis. Every witness is five years old and completely unreliable. The truth, when you find it, will be wholesome.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section"><div class="finding-label">Core Premise</div><ul class="finding-bullets"><li>Full noir investigation structure applied to playground-scale crimes.</li><li>The specimen case: two kids have cookie crumbs on their shirts. The answer: they shared it. Both guilty. Both innocent. Wholesome resolution mandatory.</li><li>Scalable case structure &mdash; each case functions as a standalone episode.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Mechanics</div><ul class="finding-bullets"><li>Ace Attorney investigation and cross-examination loop adapted for an appropriate tone.</li><li>Unreliable witness system: children misremember, exaggerate, lie to protect friends.</li><li>Red herrings mechanically embedded &mdash; damning evidence leads to innocent explanations.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Thematic DNA</div><ul class="finding-bullets"><li>The comedy of applied seriousness: treating missing cookies with investigative gravity.</li><li>The subversion of noir cynicism: here, truth is sweet and people are trying their best.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Influences</div><ul class="finding-bullets"><li>Ace Attorney series &mdash; investigation loop, testimony contradiction.</li><li>Professor Layton &mdash; episodic puzzle mysteries, gentle tone, standalone cases that work for a mixed-age audience.</li><li>Bluey &mdash; the comedy of treating children&#x2019;s problems with adult seriousness.</li></ul></div>
            </div>
            <div class="gc-vibe">Ace Attorney is 22 years old and nobody has made a wholesome version for a younger audience. That&#x2019;s a gap. The unreliable witness system isn&#x2019;t just a gimmick &mdash; it&#x2019;s the entire design. Children don&#x2019;t lie the way adults lie; they misremember, they protect people, they confabulate completely. Building an investigation loop around that specific truth is what separates this from a reskin.</div>
          </div>
        </div>

        <div class="gc-doc" onclick="toggleGcCard(this)" style="animation-delay:0.14s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-005</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Swan Marriage Counselor</div><div class="gc-subtitle">Therapy Visual Novel &middot; Lifelong Commitment &middot; Determinism vs. Choice</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-specced">Specced</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">Swans mate for life. Some of them are not handling it well. You are their counselor. The sessions are about commitment, compromise, aging, and whether promises made when young should bind the people we become.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section"><div class="finding-label">Core Premise</div><ul class="finding-bullets"><li>The player counsels swan couples &mdash; literal swans, with the biology of lifelong monogamy built in.</li><li>Sessions explore the fault lines of long commitment: growing in different directions, the resentment of promises made without full information.</li><li>Anti-dating-sim by design: rewards sitting with difficulty rather than resolving it cheaply.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Thematic DNA</div><ul class="finding-bullets"><li>Determinism vs. choice: swans are biologically determined to stay. Humans choose to.</li><li>The problem of the self over time: the person you promised yourself to at 22 is not the person in front of you at 47.</li><li>Aging as a theme rather than a backdrop.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Influences</div><ul class="finding-bullets"><li>Florence &mdash; the emotional reality of a relationship over time, not just its peak.</li><li>Richard Linklater&#x2019;s Before trilogy &mdash; the weight of two people talking honestly over years.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Commercial Note</div><ul class="finding-bullets"><li>Niche audience, strong festival circuit potential &mdash; Indiecade, IGF.</li><li>Low asset requirement. A small team with one strong writer could complete this.</li></ul></div>
            </div>
            <div class="gc-vibe">Low asset count, strong festival profile, and a demographic &mdash; people in long relationships &mdash; that games mostly ignore. The swan framing isn&#x2019;t cute window dressing; it&#x2019;s the central mechanical question. Swans don&#x2019;t choose to stay. The player&#x2019;s job is to help couples who do choose work through what that costs. That&#x2019;s a different emotional register than anything currently in the visual novel space.</div>
          </div>
        </div>

        <div class="gc-doc" onclick="toggleGcCard(this)" style="animation-delay:0.17s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-001</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Winter Storm</div><div class="gc-subtitle">Tactical Stealth Action &middot; Arctic Espionage &middot; MGS Framework</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-concept">Concept</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">Tactical stealth action in Arctic blizzards. Snowmobile exfiltration. Thermals and heartbeat sensors cut through whiteout conditions. Every footprint you leave can be tracked.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section"><div class="finding-label">Core Systems</div><ul class="finding-bullets"><li>The blizzard is not a hazard &mdash; it is cover. Whiteout conditions mask heat signatures and create acoustic interference.</li><li>Snowmobile exfiltration as a set-piece mechanic: the stealth infiltration ends; the high-speed extraction begins.</li><li>Footprint persistence: snow records movement. Players must plan routes considering what evidence they leave behind.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Design Gap</div><ul class="finding-bullets"><li>The aesthetic is fully realized. The mechanical hooks are genuinely interesting.</li><li>Missing: a narrative reason to care. Metal Gear works because Kojima built a mythology around the mechanics.</li><li>Shelved pending a narrative hook that elevates it from cool aesthetic to a game with something to say.</li></ul></div>
            </div>
            <div class="gc-vibe">The environmental stealth systems are solid and the footprint mechanic is genuinely underused in the genre. Shelved because mechanics without a reason to care are just a tech demo. Will revisit when the narrative hook shows up.</div>
          </div>
        </div>

        <div class="gc-doc" onclick="toggleGcCard(this)" style="animation-delay:0.20s">
          <div class="gc-doc-header">
            <div class="gc-doc-col-id"><div class="gc-index">GC-003</div><div class="gc-expand-hint">&#9658; expand</div></div>
            <div class="gc-doc-col-main"><div class="gc-title">Conquistador Sim</div><div class="gc-subtitle">Political Simulation &middot; New World Exploration &middot; God &middot; Guns &middot; Gold</div></div>
            <div class="gc-doc-col-meta"><span class="gc-stage-badge gc-stage-concept">Concept</span></div>
          </div>
          <div class="gc-doc-body">
            <div class="gc-doc-pitch">You are a Spanish explorer in the New World. Work for the Crown, defect and lead a revolution, or go native and become a warlord &mdash; navigating tribal politics, language barriers, shifting allegiances, and a continent that is trying to kill you.</div>
            <div class="gc-doc-grid">
              <div class="gc-doc-section"><div class="finding-label">Core Paths</div><ul class="finding-bullets"><li>Crown Loyalist: high demand, high reward &mdash; supplied, supported, and expendable.</li><li>Renegade Revolutionary (the Cort&#xe9;s path): defection and conquest on personal terms.</li><li>Gone Native / Warlord (the Kurtz path): abandon European frameworks entirely.</li><li>Transient phases: paths not locked. Sufficient rogue power forces the Crown to negotiate.</li></ul></div>
              <div class="gc-doc-section"><div class="finding-label">Design Problem</div><ul class="finding-bullets"><li>This concept is enormous. Translation systems, tribal relationship graphs, three divergent path structures &mdash; any one would be a major system in another game.</li><li>Needs a version that is 80% smaller and 20% as interesting &mdash; a proof of concept, not a simulation.</li></ul></div>
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
          <p>Independent QA tester and game developer based in the Greater Boston Metro. Shipped WordSmith on Itch.io (Godot), completed 100+ hours of paid user testing, and self-directed bug documentation across {unique_games} AAA titles. Open to remote entry-level QA roles.</p>
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

  </div>
</div>

<footer>
  <div>Wendell Lancaster — QA Portfolio &amp; Game Design // Built with precision</div>
  <div>Boston, MA &nbsp;·&nbsp; wendell91097@gmail.com &nbsp;·&nbsp; (228) 237-6193</div>
</footer>

<script>
{filter_js}
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Dashboard written to {output_path}")
    print(f"  Stats: {total_bugs} bugs across {unique_games} titles, {cs_count} case studies")


# ── ENTRY POINT ────────────────────────────────────────────────────────────────

def main():
    script_dir          = os.path.dirname(os.path.abspath(__file__))
    bugs_json_path      = os.path.join(script_dir, "bugs.json")
    case_studies_path   = os.path.join(script_dir, "case_studies.json")
    output_path         = os.path.join(script_dir, "index.html")

    if not os.path.exists(bugs_json_path):
        print(f"ERROR: Could not find {bugs_json_path}")
        print("Make sure bugs.json is in the same folder as this script.")
        return

    print("Building QA dashboard...")
    build_dashboard(bugs_json_path, case_studies_path, output_path)
    print("Done.")


if __name__ == "__main__":
    main()
