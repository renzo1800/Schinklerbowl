import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Sleeper Trade Ledger & Standings", page_icon="🏈", layout="wide")

# ==========================================
# 1. CONFIGURE YOUR DEFAULT LEAGUE ID HERE
# ==========================================
DEFAULT_LEAGUE_ID = "1312109425275736064"

BASE_URL = "https://api.sleeper.app/v1"

@st.cache_data(ttl=86400)
def discover_all_seasons(current_league_id):
    """Recursively crawls backwards to find all historical league years."""
    seasons = {}
    curr_id = current_league_id
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
    """Mock trades and manager standings for pre-season preview."""
    trades = [
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
    return trades

@st.cache_data(ttl=3600)
def fetch_trade_ledger(league_id):
    # Fetch League metadata
    users = requests.get(f"{BASE_URL}/league/{league_id}/users").json()
    user_map = {u["user_id"]: u.get("display_name", "Unknown") for u in users}

    rosters = requests.get(f"{BASE_URL}/league/{league_id}/rosters").json()
    roster_map = {r["roster_id"]: user_map.get(r["owner_id"], f"Team {r['roster_id']}") for r in rosters}

    players_data = requests.get(f"{BASE_URL}/players/nfl").json()
    player_names = {pid: p.get("full_name", pid) for pid, p in players_data.items()}

    # Fetch weekly matchup scores
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

    # Fetch completed transactions
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

def calculate_manager_standings(trades):
    """Calculates overall cumulative trade points won/lost for every manager."""
    standings = {}
    
    for t in trades:
        team_a = t["team_a"]
        team_b = t["team_b"]
        diff_a = round(t["pts_a"] - t["pts_b"], 1)
        diff_b = round(t["pts_b"] - t["pts_a"], 1)

        # Initialize team if not seen
        for tm in [team_a, team_b]:
            if tm not in standings:
                standings[tm] = {"Trades": 0, "Points Gained": 0.0, "Points Given Up": 0.0, "Net +/-": 0.0}
        
        # Team A stats
        standings[team_a]["Trades"] += 1
        standings[team_a]["Points Gained"] += t["pts_a"]
        standings[team_a]["Points Given Up"] += t["pts_b"]
        standings[team_a]["Net +/-"] += diff_a
        
        # Team B stats
        standings[team_b]["Trades"] += 1
        standings[team_b]["Points Gained"] += t["pts_b"]
        standings[team_b]["Points Given Up"] += t["pts_a"]
        standings[team_b]["Net +/-"] += diff_b

    rows = []
    for manager, stats in standings.items():
        rows.append({
            "Manager": manager,
            "Trades Made": stats["Trades"],
            "Acquired Pts": round(stats["Points Gained"], 1),
            "Traded Away Pts": round(stats["Points Given Up"], 1),
            "Net Differential": round(stats["Net +/-"], 1)
        })
        
    df = pd.DataFrame(rows).sort_values(by="Net Differential", ascending=False).reset_index(drop=True)
    return df

# --- Sidebar Controls ---
with st.sidebar:
    st.header("🏈 League Settings")
    use_demo = st.checkbox("🧪 Preview Demo Mode", value=False, help="Toggle sample data to preview layout before trades happen.")
    st.divider()
    active_league_id = st.text_input("League ID", value=DEFAULT_LEAGUE_ID, disabled=use_demo)
    
    selected_id = active_league_id
    if not use_demo and active_league_id and active_league_id != "YOUR_CURRENT_LEAGUE_ID_HERE":
        season_history = discover_all_seasons(active_league_id)
        if len(season_history) > 1:
            selected_season_label = st.selectbox("Select Season Year", options=list(season_history.keys()))
            selected_id = season_history[selected_season_label]
        elif len(season_history) == 1:
            st.caption(f"Showing: {list(season_history.keys())[0]}")
    st.divider()

# --- Main Dashboard ---
st.title("🏈 Sleeper Fantasy Trade Ledger")

trades = []
if use_demo:
    st.info("💡 **Preview Mode Active:** Showing simulated league trades.")
    trades = get_mock_data()
elif selected_id and selected_id != "YOUR_CURRENT_LEAGUE_ID_HERE":
    with st.spinner("Fetching transaction and scoring history..."):
        trades = fetch_trade_ledger(selected_id)

if trades:
    standings_df = calculate_manager_standings(trades)
    
    # 1. Awards / Titles
    champ = standings_df.iloc[0]
    bitch = standings_df.iloc[-1]
    
    col_champ, col_bitch = st.columns(2)
    with col_champ:
        with st.container(border=True):
            st.markdown("### 🏆 Trade Champ")
            st.markdown(f"**{champ['Manager']}**")
            st.metric(label="Season Net Gain", value=f"+{champ['Net Differential']} pts", delta="Top Fleece Artist")
            
    with col_bitch:
        with st.container(border=True):
            st.markdown("### 🤡 Trade Bitch")
            st.markdown(f"**{bitch['Manager']}**")
            st.metric(label="Season Net Loss", value=f"{bitch['Net Differential']} pts", delta="League Donation Bin", delta_color="inverse")

    st.divider()

    # 2. Tabs for Leaderboard vs Individual Log
    tab_standings, tab_log = st.tabs(["📊 Manager Trade Standings", "📜 All Trades Log"])
    
    with tab_standings:
        st.subheader("Season Net Trade Differential")
        
        # Color coding formatting
        def highlight_diff(val):
            color = '#10b981' if val > 0 else ('#ef4444' if val < 0 else '#94a3b8')
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            standings_df.style.map(highlight_diff, subset=['Net Differential']),
            use_container_width=True,
            hide_index=True
        )

    with tab_log:
        st.subheader("Trade-by-Trade Breakdown")
        for t in trades:
            with st.container(border=True):
                head1, head2 = st.columns([3, 1])
                head1.markdown(f"#### 📅 Week {t['week']} Trade")
                head2.markdown(f"**Leader:** :green[{t['winner']}] (+{t['margin']} pts)")
                
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

elif not use_demo and selected_id != "YOUR_CURRENT_LEAGUE_ID_HERE":
    st.info("No completed trades found for this season.")
else:
    st.warning("Please configure your League ID in the sidebar or toggle Preview Demo Mode.")
