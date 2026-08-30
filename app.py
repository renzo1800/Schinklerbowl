import streamlit as st
import requests
import pandas as pd
import os
import base64
from itertools import combinations

# ==========================================
# AUTO-ENFORCE EMBED MODE (NO FOOTER/HEADER)
# ==========================================
# ==========================================
# DEFAULT LEAGUE CONFIGURATION
# ==========================================
DEFAULT_LEAGUE_ID = "1312109425275736064"
BASE_URL = "https://api.sleeper.app/v1"

# Load local logo.png as base64 for reliable in-card rendering
def get_base64_logo():
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as f:
            data = f.read()
            return f"data:image/png;base64,{base64.b64encode(data).decode()}"
    return None

LOGO_B64 = get_base64_logo()

st.set_page_config(
    page_title="Schinklerbowl Trade Tracker",
    page_icon="logo.png" if os.path.exists("logo.png") else "🏈",
    layout="wide"
)

# --- Enhanced Sleeper Aesthetic & Glassmorphism Stylesheet ---
st.markdown("""
<style>
    /* 1. Global Reset & Dark Mode Theme */
    .stApp {
        background-color: #0b111a;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* 2. Strip Native Streamlit Distractions */
    footer, [data-testid="stFooter"], [data-testid="stBottom"], #viewer-badge, div[class*="viewerBadge"], div[class*="stBottom"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    #MainMenu, [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton {
        display: none !important;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }

    /* 3. Hero Header with Integrated Logo & Ambient Glow */
    .hero-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(0, 206, 184, 0.35);
        border-radius: 18px;
        padding: 24px 30px;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 24px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
        backdrop-filter: blur(10px);
    }
    .hero-logo {
        width: 110px;               /* Increased size from 72px */
        height: auto;               /* Keeps natural aspect ratio */
        background: transparent;    /* Eliminates any background fill */
        border: none !important;    /* Removes the bounding box border */
        box-shadow: none !important;/* Removes box shadow */
        filter: drop-shadow(0 4px 12px rgba(0, 206, 184, 0.35)); /* Neon logo glow */
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 900;
        background: linear-gradient(90deg, #00ceb8 0%, #38bdf8 60%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.92rem;
        margin-top: 2px;
        font-weight: 500;
    }

    /* 4. Podium Trophy Cards */
    .champ-card {
        background: linear-gradient(145deg, #064e3b 0%, #022c22 100%);
        border: 2px solid #10b981;
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.22);
    }
    .bitch-card {
        background: linear-gradient(145deg, #7f1d1d 0%, #450a0a 100%);
        border: 2px solid #ef4444;
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.22);
    }

    /* 5. Mini Award Cards */
    .mini-award-card {
        background: #141c28;
        border: 1px solid #233044;
        border-radius: 14px;
        padding: 14px 16px;
        height: 100%;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .mini-award-card:hover {
        border-color: #38bdf8;
        transform: translateY(-2px);
    }

    /* 6. Leaderboard Manager Cards */
    .leaderboard-card {
        background: #141c28;
        border: 1px solid #233044;
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .leaderboard-card:hover {
        border-color: #00ceb8;
        transform: translateY(-2px);
    }
    .rank-badge {
        font-size: 1.15rem;
        font-weight: 800;
        width: 32px;
        text-align: center;
        color: #94a3b8;
    }
    .manager-avatar {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        object-fit: cover;
        margin-right: 14px;
        border: 2px solid #2a374f;
    }

    /* 7. Badges & Trade Outcome Pills */
    .net-pill-pos {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid #10b981;
        padding: 6px 14px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 1.05rem;
    }
    .net-pill-neg {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid #ef4444;
        padding: 6px 14px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 1.05rem;
    }
    .net-pill-even {
        background-color: rgba(148, 163, 184, 0.15);
        color: #cbd5e1;
        border: 1px solid #64748b;
        padding: 6px 14px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 1.05rem;
    }
    .trade-pill-container {
        display: flex;
        flex-direction: column;
        gap: 5px;
        align-items: flex-end;
    }
    .trade-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.82rem;
        font-weight: 700;
    }
    .pill-win {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid #10b981;
    }
    .pill-loss {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid #ef4444;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=86400)
def discover_all_seasons(current_league_id):
    seasons = {}
    curr_id = str(current_league_id).strip()
    is_first = True
    while curr_id:
        try:
            res = requests.get(f"{BASE_URL}/league/{curr_id}").json()
            if not res or "season" not in res:
                break
            year = res.get("season", "Unknown")
            label = f"{year} Season" + (" (Current)" if is_first else "")
            seasons[label] = curr_id
            curr_id = res.get("previous_league_id")
            is_first = False
        except Exception:
            break
    return seasons

def get_mock_trades():
    return [
        {
            "week": 3,
            "team_a": "Gridiron Gurus (@FantasyKing99)",
            "avatar_a": None,
            "players_a": [
                {"id": "lamb", "name": "CeeDee Lamb (WR)", "total_pts": 218.4, "started_pts": 218.4, "early_pts": 54.2},
                {"id": "pacheco", "name": "Isiah Pacheco (RB)", "total_pts": 45.0, "started_pts": 32.0, "early_pts": 28.5}
            ],
            "team_b": "Touchdown Titans (@JoshAllenFan)",
            "avatar_b": None,
            "players_b": [
                {"id": "arsb", "name": "Amon-Ra St. Brown (WR)", "total_pts": 184.2, "started_pts": 184.2, "early_pts": 46.1}
            ],
        },
        {
            "week": 6,
            "team_a": "Championship Bound (@DynastyBro)",
            "avatar_a": None,
            "players_a": [
                {"id": "bijan", "name": "Bijan Robinson (RB)", "total_pts": 164.8, "started_pts": 164.8, "early_pts": 49.0}
            ],
            "team_b": "Touchdown Titans (@JoshAllenFan)",
            "avatar_b": None,
            "players_b": [
                {"id": "breece", "name": "Breece Hall (RB)", "total_pts": 212.5, "started_pts": 195.0, "early_pts": 61.2}
            ],
        },
        {
            "week": 8,
            "team_a": "Gridiron Gurus (@FantasyKing99)",
            "avatar_a": None,
            "players_a": [
                {"id": "josh", "name": "Josh Allen (QB)", "total_pts": 194.0, "started_pts": 194.0, "early_pts": 72.4}
            ],
            "team_b": "Waiver Wire Kings (@BenchWarmer)",
            "avatar_b": None,
            "players_b": [
                {"id": "mahomes", "name": "Patrick Mahomes (QB)", "total_pts": 132.6, "started_pts": 132.6, "early_pts": 41.0},
                {"id": "dud", "name": "Miles Sanders (RB)", "total_pts": 0.0, "started_pts": 0.0, "early_pts": 0.0}
            ],
        }
    ]

@st.cache_data(ttl=3600)
def fetch_raw_league_data(league_id):
    try:
        users = requests.get(f"{BASE_URL}/league/{league_id}/users").json()
        user_map, user_avatar_map = {}, {}
        for u in users:
            uid = u["user_id"]
            username = u.get("display_name", "")
            team_name = u.get("metadata", {}).get("team_name")
            user_map[uid] = f"{team_name} (@{username})" if (team_name and team_name != username) else (f"@{username}" if username else f"User {uid}")
            avatar_id = u.get("avatar")
            user_avatar_map[uid] = f"https://sleepercdn.com/avatars/thumbs/{avatar_id}" if avatar_id else None

        rosters = requests.get(f"{BASE_URL}/league/{league_id}/rosters").json()
        roster_map, roster_avatar_map = {}, {}
        for r in rosters:
            rid = r["roster_id"]
            oid = r.get("owner_id")
            roster_map[rid] = user_map.get(oid, f"Team {rid}")
            roster_avatar_map[rid] = user_avatar_map.get(oid)

        players_data = requests.get(f"{BASE_URL}/players/nfl").json()
        player_names = {pid: p.get("full_name", pid) for pid, p in players_data.items()}

        weekly_points, weekly_starters = {}, {}
        for week in range(1, 19):
            res = requests.get(f"{BASE_URL}/league/{league_id}/matchups/{week}").json()
            if not res:
                continue
            weekly_points[week] = {}
            weekly_starters[week] = {}
            for match in res:
                rid = match.get("roster_id")
                if "players_points" in match and match["players_points"]:
                    for pid, pts in match["players_points"].items():
                        weekly_points[week][pid] = pts
                if rid and "starters" in match and match["starters"]:
                    weekly_starters[week][rid] = set(match["starters"])

        raw_trades = []
        for week in range(1, 19):
            transactions = requests.get(f"{BASE_URL}/league/{league_id}/transactions/{week}").json()
            if not transactions:
                continue
            for tx in transactions:
                if tx.get("type") == "trade" and tx.get("status") == "complete":
                    adds = tx.get("adds", {})
                    roster_ids = tx.get("roster_ids", [])
                    if len(roster_ids) != 2:
                        continue
                    team_a, team_b = roster_ids[0], roster_ids[1]
                    raw_trades.append({
                        "week": week,
                        "team_a_id": team_a,
                        "team_b_id": team_b,
                        "team_a_name": roster_map.get(team_a, f"Team {team_a}"),
                        "team_b_name": roster_map.get(team_b, f"Team {team_b}"),
                        "avatar_a": roster_avatar_map.get(team_a),
                        "avatar_b": roster_avatar_map.get(team_b),
                        "players_to_a_ids": [pid for pid, r_id in adds.items() if r_id == team_a],
                        "players_to_b_ids": [pid for pid, r_id in adds.items() if r_id == team_b],
                    })
        return raw_trades, weekly_points, weekly_starters, player_names
    except Exception:
        return [], {}, {}, {}

def process_trade_metrics(raw_trades, weekly_points, weekly_starters, player_names, only_starters=False):
    processed = []
    for t in raw_trades:
        week = t["week"]
        team_a_id = t["team_a_id"]
        team_b_id = t["team_b_id"]

        def score_player_list(pids, owner_roster_id):
            players_scored = []
            for pid in pids:
                total_pts, started_pts, early_pts = 0.0, 0.0, 0.0
                for w in range(week + 1, 19):
                    if w in weekly_points:
                        pts = weekly_points[w].get(pid, 0.0)
                        total_pts += pts
                        is_starter = pid in weekly_starters.get(w, {}).get(owner_roster_id, set())
                        if is_starter:
                            started_pts += pts
                        if w <= week + 3:
                            early_pts += (started_pts if only_starters else pts)
                
                players_scored.append({
                    "id": pid,
                    "name": player_names.get(pid, f"Player {pid}"),
                    "total_pts": round(total_pts, 1),
                    "started_pts": round(started_pts, 1),
                    "early_pts": round(early_pts, 1)
                })
            return players_scored

        p_a = score_player_list(t["players_to_a_ids"], team_a_id)
        p_b = score_player_list(t["players_to_b_ids"], team_b_id)

        processed.append({
            "week": week,
            "team_a": t["team_a_name"],
            "avatar_a": t["avatar_a"],
            "players_a": p_a,
            "team_b": t["team_b_name"],
            "avatar_b": t["avatar_b"],
            "players_b": p_b
        })
    return processed

# --- Hero Banner with Integrated Logo ---
logo_html = f'<img src="{LOGO_B64}" class="hero-logo" />' if LOGO_B64 else '<span style="font-size: 2.8rem;">🏈</span>'

st.markdown(f"""
<div class="hero-container">
    {logo_html}
    <div>
        <div class="hero-title">Schinklerbowl Trade Tracker</div>
        <div class="hero-subtitle">Real-time cumulative trade points, manager ROI, and historical fleece metrics</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- On-Page Controls Toolbar ---
with st.container():
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.5, 1.5, 1])
    
    with ctrl_col3:
        use_demo = st.checkbox("🧪 Preview Demo", value=False, help="Toggle sample trade data before real trades happen.")
        
    with ctrl_col1:
        selected_id = DEFAULT_LEAGUE_ID
        if not use_demo:
            season_history = discover_all_seasons(DEFAULT_LEAGUE_ID)
            if len(season_history) > 1:
                selected_label = st.selectbox("📅 Select Season Year", options=list(season_history.keys()))
                selected_id = season_history[selected_label]
            elif len(season_history) == 1:
                st.selectbox("📅 Season", options=[list(season_history.keys())[0]], disabled=True)
        else:
            st.selectbox("📅 Season", options=["2024 Demo Season"], disabled=True)

    with ctrl_col2:
        scoring_mode = st.radio("📈 Points Scoring Mode", ["All Points", "Starters Only"], horizontal=True)
        only_starters = (scoring_mode == "Starters Only")

st.divider()

# Data Fetching
if use_demo:
    trades_data = get_mock_trades()
else:
    with st.spinner("Crunching Sleeper trade history..."):
        raw_trades, weekly_points, weekly_starters, player_names = fetch_raw_league_data(selected_id)
        trades_data = process_trade_metrics(raw_trades, weekly_points, weekly_starters, player_names, only_starters)

if trades_data:
    # 1. Compile Manager Standings & Trade Records
    standings = {}
    fleece_records = []
    player_impact_list = []
    trade_pair_counts = {}

    for t in trades_data:
        tm_a, tm_b = t["team_a"], t["team_b"]
        pts_a = sum(p["started_pts"] if only_starters else p["total_pts"] for p in t["players_a"])
        pts_b = sum(p["started_pts"] if only_starters else p["total_pts"] for p in t["players_b"])
        pts_a, pts_b = round(pts_a, 1), round(pts_b, 1)

        diff_a = round(pts_a - pts_b, 1)
        diff_b = round(pts_b - pts_a, 1)

        pair_key = tuple(sorted([tm_a, tm_b]))
        trade_pair_counts[pair_key] = trade_pair_counts.get(pair_key, 0) + 1

        for tm, av in [(tm_a, t.get("avatar_a")), (tm_b, t.get("avatar_b"))]:
            if tm not in standings:
                standings[tm] = {"Trades": 0, "Acquired": 0.0, "GivenUp": 0.0, "Net": 0.0, "Avatar": av, "Wins": 0, "Losses": 0}

        standings[tm_a]["Trades"] += 1
        standings[tm_a]["Acquired"] += pts_a
        standings[tm_a]["GivenUp"] += pts_b
        standings[tm_a]["Net"] += diff_a
        if diff_a > 0: standings[tm_a]["Wins"] += 1
        elif diff_a < 0: standings[tm_a]["Losses"] += 1

        standings[tm_b]["Trades"] += 1
        standings[tm_b]["Acquired"] += pts_b
        standings[tm_b]["GivenUp"] += pts_a
        standings[tm_b]["Net"] += diff_b
        if diff_b > 0: standings[tm_b]["Wins"] += 1
        elif diff_b < 0: standings[tm_b]["Losses"] += 1

        margin = abs(diff_a)
        win_team = tm_a if diff_a > 0 else (tm_b if diff_b > 0 else "Even")
        lose_team = tm_b if diff_a > 0 else (tm_a if diff_b > 0 else "Even")
        fleece_records.append({"week": t["week"], "winner": win_team, "loser": lose_team, "margin": margin, "pts_a": pts_a, "pts_b": pts_b, "trade": t})

        for p in t["players_a"]:
            player_impact_list.append({"name": p["name"], "pts": p["started_pts"] if only_starters else p["total_pts"], "traded_by": tm_b, "acquired_by": tm_a})
        for p in t["players_b"]:
            player_impact_list.append({"name": p["name"], "pts": p["started_pts"] if only_starters else p["total_pts"], "traded_by": tm_a, "acquired_by": tm_b})

    # Prepare DataFrame
    standings_rows = []
    for m, s in standings.items():
        acq = round(s["Acquired"], 1)
        giv = round(s["GivenUp"], 1)
        roi = round((acq / giv), 2) if giv > 0 else (acq if acq > 0 else 1.0)
        standings_rows.append({
            "Manager": m,
            "Avatar": s["Avatar"],
            "Trades": s["Trades"],
            "Record": f"{s['Wins']}-{s['Losses']}",
            "Acquired Pts": acq,
            "Given Up Pts": giv,
            "Net Differential": round(s["Net"], 1),
            "ROI": roi
        })
    standings_df = pd.DataFrame(standings_rows).sort_values(by="Net Differential", ascending=False).reset_index(drop=True)

    # 2. Main Awards (Champ & Bitch)
    if len(standings_df) >= 2:
        champ = standings_df.iloc[0]
        bitch = standings_df.iloc[-1]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="champ-card">
                <div style="font-size: 0.8rem; font-weight: 800; color: #34d399; text-transform: uppercase;">👑 Current Fleece King</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #ffffff; margin-top: 2px;">🏆 Trade Champ</div>
                <div style="font-size: 1.15rem; font-weight: 600; color: #a7f3d0;">{champ['Manager']}</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #34d399; margin-top: 6px;">+{champ['Net Differential']:.1f} <span style="font-size: 0.95rem; font-weight: 400; color: #a7f3d0;">pts net (ROI: {champ['ROI']}x)</span></div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="bitch-card">
                <div style="font-size: 0.8rem; font-weight: 800; color: #f87171; text-transform: uppercase;">💩 League Donation Bin</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #ffffff; margin-top: 2px;">🤡 Trade Bitch</div>
                <div style="font-size: 1.15rem; font-weight: 600; color: #fecaca;">{bitch['Manager']}</div>
                <div style="font-size: 1.8rem; font-weight: 800; color: #f87171; margin-top: 6px;">{bitch['Net Differential']:.1f} <span style="font-size: 0.95rem; font-weight: 400; color: #fecaca;">pts net (ROI: {bitch['ROI']}x)</span></div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")

    # 3. Fun Superlative Metric Cards Row
    if fleece_records and player_impact_list:
        grand_heist = max(fleece_records, key=lambda x: x["margin"])
        sellers_remorse = max(player_impact_list, key=lambda x: x["pts"])
        paperweight = min(player_impact_list, key=lambda x: x["pts"])
        most_frequent_pair = max(trade_pair_counts.items(), key=lambda x: x[1]) if trade_pair_counts else (("None", "None"), 0)

        a1, a2, a3, a4 = st.columns(4)
        with a1:
            st.markdown(f"""
            <div class="mini-award-card">
                <div style="font-size: 0.75rem; color: #38bdf8; font-weight: 800; text-transform: uppercase;">🚨 Grand Heist (Top Fleece)</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #ffffff; margin-top: 4px;">+{grand_heist['margin']:.1f} pts</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 2px;">Week {grand_heist['week']}: <b>{grand_heist['winner']}</b> over {grand_heist['loser']}</div>
            </div>
            """, unsafe_allow_html=True)
        with a2:
            st.markdown(f"""
            <div class="mini-award-card">
                <div style="font-size: 0.75rem; color: #f59e0b; font-weight: 800; text-transform: uppercase;">📉 Seller's Remorse</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #ffffff; margin-top: 4px;">{sellers_remorse['name']}</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 2px;">Scored <b>{sellers_remorse['pts']} pts</b> after <i>{sellers_remorse['traded_by']}</i> gave him away</div>
            </div>
            """, unsafe_allow_html=True)
        with a3:
            st.markdown(f"""
            <div class="mini-award-card">
                <div style="font-size: 0.75rem; color: #ef4444; font-weight: 800; text-transform: uppercase;">📦 Paperweight Award</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #ffffff; margin-top: 4px;">{paperweight['name']}</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 2px;">Produced only <b>{paperweight['pts']} pts</b> for <i>{paperweight['acquired_by']}</i></div>
            </div>
            """, unsafe_allow_html=True)
        with a4:
            st.markdown(f"""
            <div class="mini-award-card">
                <div style="font-size: 0.75rem; color: #a855f7; font-weight: 800; text-transform: uppercase;">🤝 Collusion Alarm</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #ffffff; margin-top: 4px;">{most_frequent_pair[1]} Deals Made</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 2px;">Between {most_frequent_pair[0][0]} & {most_frequent_pair[0][1]}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")

    # 4. Multi-Tab Section
    tab_standings, tab_h2h, tab_log = st.tabs(["📊 Manager Standings & ROI", "🥊 Head-to-Head Feud Matrix", "📜 Season Trade History"])

    with tab_standings:
        st.subheader("Leaderboard & Return on Investment")
        default_avatar = "https://sleepercdn.com/images/v2/icons/player_default.webp"

        for idx, row in standings_df.iterrows():
            rank = idx + 1
            rank_icon = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
            avatar_url = row['Avatar'] if row['Avatar'] else default_avatar
            diff = row['Net Differential']

            pill_class = "net-pill-pos" if diff > 0 else ("net-pill-neg" if diff < 0 else "net-pill-even")
            pill_text = f"+{diff:.1f} pts" if diff > 0 else f"{diff:.1f} pts"

            st.markdown(f"""
            <div class="leaderboard-card">
                <div style="display: flex; align-items: center;">
                    <div class="rank-badge">{rank_icon}</div>
                    <img src="{avatar_url}" class="manager-avatar" onerror="this.src='{default_avatar}'" />
                    <div>
                        <div style="font-size: 1.1rem; font-weight: 700; color: #ffffff;">{row['Manager']}</div>
                        <div style="font-size: 0.85rem; color: #94a3b8;">
                            Deals: <b>{row['Trades']}</b> ({row['Record']}) &nbsp;|&nbsp; 
                            🟢 Acquired: <span style="color: #cbd5e1; font-weight: 600;">{row['Acquired Pts']} pts</span> &nbsp;|&nbsp; 
                            🔴 Given Up: <span style="color: #cbd5e1; font-weight: 600;">{row['Given Up Pts']} pts</span> &nbsp;|&nbsp;
                            ⚡ ROI: <span style="color: #38bdf8; font-weight: 700;">{row['ROI']}x</span>
                        </div>
                    </div>
                </div>
                <div>
                    <span class="{pill_class}">{pill_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.divider()
        st.subheader("Visual Net Margin Breakdown")
        chart_data = standings_df.set_index("Manager")["Net Differential"]
        st.bar_chart(chart_data)

    with tab_h2h:
        st.subheader("Manager vs Manager Rivalry Matrix")
        all_managers = list(standings.keys())
        if len(all_managers) >= 2:
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                man_a = st.selectbox("Select Manager A:", all_managers, index=0)
            with m_col2:
                man_b = st.selectbox("Select Manager B:", [m for m in all_managers if m != man_a], index=0)

            direct_trades = []
            h2h_net_a = 0.0

            for t in trades_data:
                if (t["team_a"] == man_a and t["team_b"] == man_b) or (t["team_a"] == man_b and t["team_b"] == man_a):
                    pts_to_a = sum(p["started_pts"] if only_starters else p["total_pts"] for p in (t["players_a"] if t["team_a"] == man_a else t["players_b"]))
                    pts_to_b = sum(p["started_pts"] if only_starters else p["total_pts"] for p in (t["players_b"] if t["team_a"] == man_a else t["players_a"]))
                    diff = round(pts_to_a - pts_to_b, 1)
                    h2h_net_a += diff
                    direct_trades.append({"week": t["week"], "pts_a": pts_to_a, "pts_b": pts_to_b, "diff": diff, "trade": t})

            if direct_trades:
                res_color = "#34d399" if h2h_net_a > 0 else ("#f87171" if h2h_net_a < 0 else "#94a3b8")
                lead_text = f"<b>{man_a}</b> leads by <b>+{h2h_net_a:.1f} pts</b>" if h2h_net_a > 0 else (f"<b>{man_b}</b> leads by <b>+{abs(h2h_net_a):.1f} pts</b>" if h2h_net_a < 0 else "All square (0.0 pts)")
                
                st.markdown(f"""
                <div style="background: #172030; border-left: 4px solid {res_color}; border-radius: 8px; padding: 14px 18px; margin: 16px 0;">
                    <div style="font-size: 1.15rem; color: #ffffff;">🥊 Head-to-Head Balance: {lead_text}</div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">Total deals between these managers: {len(direct_trades)}</div>
                </div>
                """, unsafe_allow_html=True)

                for dt in direct_trades:
                    t = dt["trade"]
                    with st.container(border=True):
                        st.markdown(f"**Week {dt['week']} Deal:** {man_a} scored `{dt['pts_a']:.1f} pts` vs {man_b} scored `{dt['pts_b']:.1f} pts` (Net Margin: `{dt['diff']:+0.1f} pts`)")
            else:
                st.info(f"No completed trades on record between {man_a} and {man_b}.")

    with tab_log:
        st.subheader("Completed Trades Log")
        for t in trades_data:
            pts_a = sum(p["started_pts"] if only_starters else p["total_pts"] for p in t["players_a"])
            pts_b = sum(p["started_pts"] if only_starters else p["total_pts"] for p in t["players_b"])
            pts_a, pts_b = round(pts_a, 1), round(pts_b, 1)
            margin = round(abs(pts_a - pts_b), 1)

            if pts_a > pts_b: winner, loser = t["team_a"], t["team_b"]
            elif pts_b > pts_a: winner, loser = t["team_b"], t["team_a"]
            else: winner, loser = "Even", "Even"

            with st.container(border=True):
                h1, h2 = st.columns([3, 2])
                h1.markdown(f"#### 📅 Week {t['week']} Transaction")
                if winner != "Even":
                    h2.markdown(f"""
                    <div class="trade-pill-container">
                        <span class="trade-pill pill-win">👑 Winner: {winner} (+{margin} pts)</span>
                        <span class="trade-pill pill-loss">🤡 Loser: {loser} (-{margin} pts)</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    h2.markdown('<div class="trade-pill-container"><span class="trade-pill" style="background: #334155;">⚖️ Even (0.0 pts)</span></div>', unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**{t['team_a']} received:**")
                    for p in t['players_a']:
                        val = p['started_pts'] if only_starters else p['total_pts']
                        bench_tax = round(p['total_pts'] - p['started_pts'], 1)
                        st.markdown(f"- `{p['name']}`: **{val} pts** (3-Wk ROI: `{p['early_pts']} pts`, Bench Tax: `{bench_tax} pts`)")
                    st.metric(label="Total Points Acquired", value=f"{pts_a} pts")

                with c2:
                    st.markdown(f"**{t['team_b']} received:**")
                    for p in t['players_b']:
                        val = p['started_pts'] if only_starters else p['total_pts']
                        bench_tax = round(p['total_pts'] - p['started_pts'], 1)
                        st.markdown(f"- `{p['name']}`: **{val} pts** (3-Wk ROI: `{p['early_pts']} pts`, Bench Tax: `{bench_tax} pts`)")
                    st.metric(label="Total Points Acquired", value=f"{pts_b} pts")

elif not use_demo and selected_id:
    st.info("No completed trades found for this season yet. Toggle **Preview Demo** in the top toolbar to see all awards and sample data!")
