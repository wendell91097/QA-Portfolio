import json
import os
from collections import Counter
from html import escape


# ── GAME CONFIG ────────────────────────────────────────────────────────────────
# Add new games here whenever you add a new game to bugs.json.
# css_class maps to the .game-XXXX style in the CSS block below.
GAME_CONFIG = {
    "ds3":        {"label": "Dark Souls III",               "css_class": "game-ds3"},
    "eldenring":  {"label": "Elden Ring",                   "css_class": "game-eldenring"},
    "fallout4":   {"label": "Fallout 4",                    "css_class": "game-fallout4"},
    "fallout76":  {"label": "Fallout 76",                   "css_class": "game-fallout76"},
    "spiderman":  {"label": "Spider-Man Remastered",        "css_class": "game-spiderman"},
    "rdr1":       {"label": "RDR Remastered",               "css_class": "game-rdr1"},
    "rdr2":       {"label": "Red Dead Redemption 2",        "css_class": "game-rdr2"},
    "witcher3":   {"label": "The Witcher III",              "css_class": "game-witcher3"},
    "wolf":       {"label": "Wolfenstein II",               "css_class": "game-wolf"},
    "cp77":       {"label": "Cyberpunk 2077",               "css_class": "game-cp77"},
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


# ── HTML GENERATORS ────────────────────────────────────────────────────────────

def make_video_embed(bug: dict) -> str:
    url = bug.get("video_url", "").strip()
    text = bug.get("video_text", "Add YouTube link here")

    if url:
        # Convert standard YouTube watch URL to embed URL if needed
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


def make_sidebar(bugs: list) -> str:
    # Count occurrences for each dimension
    game_counts     = Counter(b["game"] for b in bugs)
    sev_counts      = Counter(b["severity"] for b in bugs)
    type_counts     = Counter(b["type"] for b in bugs)
    total           = len(bugs)

    # Games section — only show games that appear in the data
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

    # Severity section — only show severities that appear in the data
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

    # Type section — only show types that appear in the data
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
    unique_games = len(set(b["game"] for b in bugs))

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
    <div class="stat-value">1</div>
    <div class="stat-label">Shipped Title</div>
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
    --text-mid: #9ca3af;
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
  }
  .stat-item:last-child { border-right: none; }
  .stat-value {
    font-family: 'Syne', sans-serif;
    font-weight: 800; font-size: 26px; color: var(--accent); line-height: 1;
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
  .game-ds3       { background: rgba(255,77,77,0.1);    color: #ff7070; }
  .game-eldenring { background: rgba(255,215,0,0.1);    color: #ffd700; }
  .game-fallout4  { background: rgba(144,238,144,0.1);  color: #90ee90; }
  .game-fallout76 { background: rgba(0,255,127,0.1);    color: #00c875; }
  .game-spiderman { background: rgba(255,0,0,0.1);      color: #ff6b6b; }
  .game-rdr1      { background: rgba(139,90,43,0.25);   color: #c4965a; }
  .game-rdr2      { background: rgba(160,82,45,0.2);    color: #d4a96a; }
  .game-witcher3  { background: rgba(255,165,0,0.1);    color: #ffb347; }
  .game-wolf      { background: rgba(255,140,66,0.1);   color: #ffaa70; }
  .game-cp77      { background: rgba(252,238,9,0.1);    color: #fcee09; }
  .game-default   { background: rgba(156,163,175,0.1);  color: #9ca3af; }

  /* EXPANDED DETAIL */
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
  .detail-text { font-size: 12px; color: var(--text-mid); line-height: 1.7; }
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
  .skill-list { display: flex; flex-direction: column; gap: 4px; }
  .skill-item { font-size: 11px; color: var(--text-mid); display: flex; align-items: center; gap: 8px; }
  .skill-item::before { content: '▸'; color: var(--accent); font-size: 9px; }

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
"""


# ── MAIN BUILD FUNCTION ────────────────────────────────────────────────────────

def build_dashboard(json_path: str, output_path: str) -> None:
    with open(json_path, "r", encoding="utf-8") as f:
        bugs = json.load(f)

    print(f"  Loaded {len(bugs)} bug reports from {json_path}")

    # Build dynamic sections
    stats_bar   = make_stats_bar(bugs)
    sidebar     = make_sidebar(bugs)
    bug_cards   = "\n".join(make_bug_card(b) for b in bugs)
    filter_js   = make_filter_js(bugs)
    total_bugs  = len(bugs)
    unique_games = len(set(b["game"] for b in bugs))

    # Build titles list for about panel
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
<title>Wendell Lancaster — QA Portfolio</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>

<!-- HEADER -->
<header>
  <div class="header-left">
    <div class="logo-mark">WL</div>
    <div class="header-name">WENDELL LANCASTER</div>
    <div class="header-role">QA Tester &amp; Game Developer</div>
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
    <div class="content-header">
      <div class="content-title">// Bug Reports</div>
      <div class="result-count">Showing <span id="count">{total_bugs}</span> of {total_bugs} reports</div>
    </div>

    <div class="bug-list" id="bugList">
{bug_cards}
    </div>

    <!-- ABOUT PANEL -->
    <div class="about-panel">
      <div class="about-header">// About This Portfolio</div>
      <div class="about-body">
        <div class="about-col">
          <div class="about-col-title">Background</div>
          <p>Independent QA tester and game developer based in Ocean Springs, MS. Shipped WordSmith on Itch.io (Godot), completed 100+ hours of paid user testing, and self-directed bug documentation across {unique_games} AAA titles. Open to remote entry-level QA roles.</p>
        </div>
        <div class="about-col">
          <div class="about-col-title">QA Skills</div>
          <div class="skill-list">
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
  <div>Wendell Lancaster — QA Portfolio // Built with precision</div>
  <div>Ocean Springs, MS &nbsp;·&nbsp; wendell91097@gmail.com &nbsp;·&nbsp; (228) 237-6193</div>
</footer>

<script>
{filter_js}
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Dashboard written to {output_path}")
    print(f"  Stats: {total_bugs} bugs across {unique_games} titles")


# ── ENTRY POINT ────────────────────────────────────────────────────────────────

def main():
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    json_path   = os.path.join(script_dir, "bugs.json")
    output_path = os.path.join(script_dir, "qa-dashboard.html")

    if not os.path.exists(json_path):
        print(f"ERROR: Could not find {json_path}")
        print("Make sure bugs.json is in the same folder as this script.")
        return

    print("Building QA dashboard...")
    build_dashboard(json_path, output_path)
    print("Done.")


if __name__ == "__main__":
    main()