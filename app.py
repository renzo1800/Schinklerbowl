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
# CONFIGURE YOUR LEAGUE ID
# ==========================================
DEFAULT_LEAGUE_ID = "1312109425275736064"

BASE_URL = "https://api.sleeper.app/v1"

# --- Custom Sleeper Aesthetic CSS Injection ---
st.markdown("""
<style>
    /* Global Background & Font styling */
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
    
    /* Trade Item Cards */
    .trade-card {
        background-color: #172030;
        border: 1px solid #2a374f;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
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
            "players_a": ["CeeDee Lamb (WR)", "Isiah Pacheco (RB)"],
            "pts_a": 218.4,
            "team_b": "Touchdown Titans",
            "players_b": ["Amon-Ra St. Brown (WR)"],
            "pts_b": 184.2,
            "winner": "Gridiron Gurus",
            "margin": 34.2
        },
        {
            "week": 6,
            "team_a": "Championship Bound",
            "players_a": ["Bijan Robinson (RB)"],
            "pts_a": 164.8,
            "team_b": "Touchdown Titans",
            "players_b": ["Breece Hall (RB)"],
            "pts_b": 202.5,
            "winner": "Touchdown Titans",
            "margin": 37.7
        },
        {
            "week": 8,
            "team_a": "Gridiron Gurus",
            "players_a": ["Josh Allen (QB)"],
            "pts_a": 194.0,
            "team_b": "Waiver Wire Kings",
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
        user_map = {u["user_id"]: u.get("display_name", "Unknown") for u in users}

        rosters = requests.get(f"{BASE_URL}/league/{league_id}/rosters").json()
        roster_map = {r["roster_id"]: user_map.get(r["owner_id"], f"Team {r['roster_id']}") for r in rosters}

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
                        "players_a": [player_names.get(p, p) for p in players_a] or ["Draft Picks / FAAB"],
                        "pts_a": round(pts_a, 1),
                        "team_b": name_b,
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

        for tm in [team_a, team_b]:
            if tm not in standings:
                standings[tm] = {"Trades": 0, "Points Gained": 0.0, "Points Given Up": 0.0, "Net +/-": 0.0}
        
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

    # 2. Main Tabs
    tab_standings, tab_log = st.tabs(["📊 Manager Standings & Chart", "📜 Season Trade History"])
    
    with tab_standings:
        st.subheader("Leaderboard")
        
        # Interactive Leaderboard Table
        st.dataframe(
            standings_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Net Differential": st.column_config.NumberColumn(
                    "Net +/- Margin",
                    format="%+0.1f pts"
                ),
                "Acquired Pts": st.column_config.NumberColumn("Acquired Points", format="%.1f pts"),
                "Given Up Pts": st.column_config.NumberColumn("Traded Away Points", format="%.1f pts"),
                "Trades": st.column_config.NumberColumn("Total Deals")
            }
        )
        
        st.divider()
        st.subheader("Visual Net Margin Breakdown")
        # Visual Bar Chart showing best to worst
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
