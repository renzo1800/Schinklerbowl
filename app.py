import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="Schinklerbowl Trade Tracker",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# DEFAULT LEAGUE ID CONFIGURED
# ==========================================
DEFAULT_LEAGUE_ID = "1312109425275736064"

BASE_URL = "https://api.sleeper.app/v1"

# --- Custom Sleeper Aesthetic CSS Injection ---
st.markdown("""
<style>
    .stApp {
        background-color: #0d131d;
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Header Card */
    .hero-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid rgba(0, 206, 184, 0.3);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00ceb8, #38bdf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    
    /* Awards Cards */
    .champ-card {
        background: linear-gradient(145deg, #064e3b 0%, #022c22 100%);
        border: 2px solid #10b981;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.2);
    }
    .bitch-card {
        background: linear-gradient(145deg, #7f1d1d 0%, #450a0a 100%);
        border: 2px solid #ef4444;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(239, 68, 68, 0.2);
    }
    
    /* Leaderboard Manager Cards */
    .leaderboard-card {
        background: #151d2a;
        border: 1px solid #222f44;
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 12px;
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
        font-size: 1.1rem;
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
    .net-pill-pos {
        background-color: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid #10b981;
        padding: 6px 14px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 1.1rem;
    }
    .net-pill-neg {
        background-color: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid #ef4444;
        padding: 6px 14px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 1.1rem;
    }
    .net-pill-even {
        background-color: rgba(148, 163, 184, 0.15);
        color: #cbd5e1;
        border: 1px solid #64748b;
        padding: 6px 14px;
        border-radius: 10px;
        font-weight: 800;
        font-size: 1.1rem;
    }

    /* Trade Item Pills */
    .trade-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .pill-win {
        background-color: rgba(0, 206, 184, 0.15);
        color: #00ceb8;
        border: 1px solid #00ceb8;
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

def get_mock_data():
    return [
        {
            "week": 3,
            "team_a": "Gridiron Gurus",
            "avatar_a": None,
            "players_a": ["CeeDee Lamb (WR)", "Isiah Pacheco (RB)"],
            "pts_a": 218.4,
            "team_b": "Touchdown Titans",
            "avatar_b": None,
            "players_b": ["Amon-Ra St. Brown (WR)"],
            "pts_b": 184.2,
            "winner": "Gridiron Gurus",
            "margin": 34.2
        },
        {
            "week": 6,
            "team_a": "Championship Bound",
            "avatar_a": None,
            "players_a": ["Bijan Robinson (RB)"],
            "pts_a": 164.8,
            "team_b": "Touchdown Titans",
            "avatar_b": None,
            "players_b": ["Breece Hall (RB)"],
            "pts_b": 202.5,
            "winner": "Touchdown Titans",
            "margin": 37.7
        },
        {
            "week": 8,
            "team_a": "Gridiron Gurus",
            "avatar_a": None,
            "players_a": ["Josh Allen (QB)"],
            "pts_a": 194.0,
            "team_b": "Waiver Wire Kings",
            "avatar_b": None,
            "players_b": ["Patrick Mahomes (QB)"],
            "pts_b": 142.6,
            "winner": "Gridiron Gurus",
            "margin": 51.4
        }
    ]

@st.cache_data(ttl=3600)
def fetch_trade_ledger(league_id):
    try:
        users = requests.get(f"{BASE_URL}/league/{league_id}/users").json()
        user_map = {}
        user_avatar_map = {}
        for u in users:
            uid = u["user_id"]
            user_map[uid] = u.get("metadata", {}).get("team_name") or u.get("display_name", "Unknown")
            avatar_id = u.get("avatar")
            user_avatar_map[uid] = f"https://sleepercdn.com/avatars/thumbs/{avatar_id}" if avatar_id else None

        rosters = requests.get(f"{BASE_URL}/league/{league_id}/rosters").json()
        roster_map = {}
        roster_avatar_map = {}
        for r in rosters:
            rid = r["roster_id"]
            oid = r.get("owner_id")
            roster_map[rid] = user_map.get(oid, f"Team {rid}")
            roster_avatar_map[rid] = user_avatar_map.get(oid)

        players_data = requests.get(f"{BASE_URL}/players/nfl").json()
        player_names = {pid: p.get("full_name", pid) for pid, p in players_data.items()}

        weekly_points = {}
        for week in range(1, 19):
            res = requests.get(f"{BASE_URL}/league/{league_id}/matchups/{week}").json()
            if not res:
                continue
            weekly_points[week] = {}
            for match in res:
                if "players_points" in match and match["players_points"]:
                    for pid, pts in match["players_points"].items():
                        weekly_points[week][pid] = pts

        trade_list = []
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
                    name_a, name_b = roster_map.get(team_a, f"Team {team_a}"), roster_map.get(team_b, f"Team {team_b}")
                    avatar_a, avatar_b = roster_avatar_map.get(team_a), roster_avatar_map.get(team_b)
                    
                    players_a = [pid for pid, r_id in adds.items() if r_id == team_a]
                    players_b = [pid for pid, r_id in adds.items() if r_id == team_b]
                    
                    pts_a, pts_b = 0.0, 0.0
                    for w in range(week + 1, 19):
                        if w in weekly_points:
                            for pid in players_a:
                                pts_a += weekly_points[w].get(pid, 0.0)
                            for pid in players_b:
                                pts_b += weekly_points[w].get(pid, 0.0)
                    
                    net_margin = round(pts_a - pts_b, 1)
                    
                    trade_list.append({
                        "week": week,
                        "team_a": name_a,
                        "avatar_a": avatar_a,
                        "players_a": [player_names.get(p, p) for p in players_a] or ["Draft Picks / FAAB"],
                        "pts_a": round(pts_a, 1),
                        "team_b": name_b,
                        "avatar_b": avatar_b,
                        "players_b": [player_names.get(p, p) for p in players_b] or ["Draft Picks / FAAB"],
                        "pts_b": round(pts_b, 1),
                        "winner": name_a if net_margin > 0 else (name_b if net_margin < 0 else "Even"),
                        "margin": abs(net_margin)
                    })
        return trade_list
    except Exception:
        return []

def calculate_manager_standings(trades):
    standings = {}
    for t in trades:
        team_a, team_b = t["team_a"], t["team_b"]
        diff_a = round(t["pts_a"] - t["pts_b"], 1)
        diff_b = round(t["pts_b"] - t["pts_a"], 1)

        for tm, av in [(team_a, t.get("avatar_a")), (team_b, t.get("avatar_b"))]:
            if tm not in standings:
                standings[tm] = {
                    "Trades": 0,
                    "Points Gained": 0.0,
                    "Points Given Up": 0.0,
                    "Net +/-": 0.0,
                    "Avatar": av
                }
        
        standings[team_a]["Trades"] += 1
        standings[team_a]["Points Gained"] += t["pts_a"]
        standings[team_a]["Points Given Up"] += t["pts_b"]
        standings[team_a]["Net +/-"] += diff_a
        
        standings[team_b]["Trades"] += 1
        standings[team_b]["Points Gained"] += t["pts_b"]
        standings[team_b]["Points Given Up"] += t["pts_a"]
        standings[team_b]["Net +/-"] += diff_b

    rows = []
    for manager, stats in standings.items():
        rows.append({
            "Manager": manager,
            "Avatar": stats["Avatar"],
            "Trades": stats["Trades"],
            "Acquired Pts": round(stats["Points Gained"], 1),
            "Given Up Pts": round(stats["Points Given Up"], 1),
            "Net Differential": round(stats["Net +/-"], 1)
        })
        
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by="Net Differential", ascending=False).reset_index(drop=True)
    return df

# --- Sidebar ---
with st.sidebar:
    st.header("⚡ League Settings")
    use_demo = st.checkbox("🧪 Preview Demo Mode", value=False)
    st.divider()
    active_league_id = st.text_input("League ID", value=DEFAULT_LEAGUE_ID, disabled=use_demo)
    
    selected_id = active_league_id
    if not use_demo and active_league_id:
        season_history = discover_all_seasons(active_league_id)
        if len(season_history) > 1:
            selected_season_label = st.selectbox("Select Season", options=list(season_history.keys()))
            selected_id = season_history[selected_season_label]
        elif len(season_history) == 1:
            st.caption(f"Showing: {list(season_history.keys())[0]}")
    st.divider()

# --- Main Dashboard Header ---
st.markdown("""
<div class="hero-header">
    <div class="hero-title">🏆 Schinklerbowl Trade Tracker</div>
    <div style="color: #94a3b8; font-size: 1rem;">Tracking net fantasy points won and lost across all completed trades</div>
</div>
""", unsafe_allow_html=True)

trades = []
if use_demo:
    st.info("💡 **Preview Mode Active:** Showing simulated league trades.")
    trades = get_mock_data()
elif selected_id:
    with st.spinner("Crunching Sleeper trade stats..."):
        trades = fetch_trade_ledger(selected_id)

if trades:
    standings_df = calculate_manager_standings(trades)
    
    # 1. Hall of Fame / Shame Badges
    if len(standings_df) >= 2:
        champ = standings_df.iloc[0]
        bitch = standings_df.iloc[-1]
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="champ-card">
                <div style="font-size: 0.85rem; font-weight: 800; color: #34d399; text-transform: uppercase; letter-spacing: 0.1em;">👑 Current Fleece King</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #ffffff; margin-top: 4px;">🏆 Trade Champ</div>
                <div style="font-size: 1.25rem; font-weight: 600; color: #a7f3d0; margin-top: 2px;">{champ['Manager']}</div>
                <div style="font-size: 2rem; font-weight: 800; color: #34d399; margin-top: 8px;">+{champ['Net Differential']} <span style="font-size: 1rem; font-weight: 400; color: #a7f3d0;">pts net</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
            <div class="bitch-card">
                <div style="font-size: 0.85rem; font-weight: 800; color: #f87171; text-transform: uppercase; letter-spacing: 0.1em;">💩 Community Food Bank</div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #ffffff; margin-top: 4px;">🤡 Trade Bitch</div>
                <div style="font-size: 1.25rem; font-weight: 600; color: #fecaca; margin-top: 2px;">{bitch['Manager']}</div>
                <div style="font-size: 2rem; font-weight: 800; color: #f87171; margin-top: 8px;">{bitch['Net Differential']} <span style="font-size: 1rem; font-weight: 400; color: #fecaca;">pts net</span></div>
            </div>
            """, unsafe_allow_html=True)
            
        st.write("")

    # 2. Tabs
    tab_standings, tab_log = st.tabs(["📊 Manager Standings & Cards", "📜 Season Trade History"])
    
    with tab_standings:
        st.subheader("Leaderboard")
        
        # High-Energy Manager Standings Cards
        default_avatar = "https://sleepercdn.com/images/v2/icons/player_default.webp"
        
        for idx, row in standings_df.iterrows():
            rank = idx + 1
            rank_icon = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
            avatar_url = row['Avatar'] if row['Avatar'] else default_avatar
            
            diff = row['Net Differential']
            if diff > 0:
                pill_class = "net-pill-pos"
                pill_text = f"+{diff:.1f} pts"
            elif diff < 0:
                pill_class = "net-pill-neg"
                pill_text = f"{diff:.1f} pts"
            else:
                pill_class = "net-pill-even"
                pill_text = "0.0 pts"
                
            st.markdown(f"""
            <div class="leaderboard-card">
                <div style="display: flex; align-items: center;">
                    <div class="rank-badge">{rank_icon}</div>
                    <img src="{avatar_url}" class="manager-avatar" onerror="this.src='{default_avatar}'" />
                    <div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: #ffffff;">{row['Manager']}</div>
                        <div style="font-size: 0.85rem; color: #94a3b8;">
                            {row['Trades']} deals &nbsp;|&nbsp; 🟢 Acquired: <span style="color: #cbd5e1; font-weight: 600;">{row['Acquired Pts']} pts</span> &nbsp;|&nbsp; 🔴 Traded Away: <span style="color: #cbd5e1; font-weight: 600;">{row['Given Up Pts']} pts</span>
                        </div>
                    </div>
                </div>
                <div>
                    <span class="{pill_class}">{pill_text}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        st.subheader("Visual Net Differential Chart")
        chart_data = standings_df.set_index("Manager")["Net Differential"]
        st.bar_chart(chart_data)

    with tab_log:
        st.subheader("Completed Trades Log")
        for t in trades:
            with st.container(border=True):
                h1, h2 = st.columns([3, 1])
                h1.markdown(f"#### 📅 Week {t['week']} Transaction")
                h2.markdown(f"<span class='trade-pill pill-win'>👑 Leader: {t['winner']} (+{t['margin']} pts)</span>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**{t['team_a']} received:**")
                    for p in t['players_a']:
                        st.markdown(f"- `{p}`")
                    st.metric(label="Post-Trade Points Scored", value=f"{t['pts_a']} pts")
                    
                with c2:
                    st.markdown(f"**{t['team_b']} received:**")
                    for p in t['players_b']:
                        st.markdown(f"- `{p}`")
                    st.metric(label="Post-Trade Points Scored", value=f"{t['pts_b']} pts")

elif not use_demo and selected_id:
    st.info("No completed trades found for this season yet. Toggle **Preview Demo Mode** in the sidebar to see how it looks!")
