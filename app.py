import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Sleeper Trade Ledger", page_icon="🏈", layout="wide")

# ==========================================
# 1. CONFIGURE YOUR DEFAULT LEAGUE ID HERE
# ==========================================
DEFAULT_LEAGUE_ID = "1312109425275736064"  # Paste your current League ID here

BASE_URL = "https://api.sleeper.app/v1"

@st.cache_data(ttl=86400)
def discover_all_seasons(current_league_id):
    """Recursively walks backwards using previous_league_id to find all historical years."""
    seasons = {} # e.g., {"2024 (Current)": "1049...", "2023": "9823...", "2022": "8712..."}
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

@st.cache_data(ttl=3600)
def fetch_trade_ledger(league_id):
    # Fetch League metadata
    users = requests.get(f"{BASE_URL}/league/{league_id}/users").json()
    user_map = {u["user_id"]: u.get("display_name", "Unknown") for u in users}

    rosters = requests.get(f"{BASE_URL}/league/{league_id}/rosters").json()
    roster_map = {r["roster_id"]: user_map.get(r["owner_id"], f"Team {r['roster_id']}") for r in rosters}

    players_data = requests.get(f"{BASE_URL}/players/nfl").json()
    player_names = {pid: p.get("full_name", pid) for pid, p in players_data.items()}

    # Fetch weekly matchup points for that year
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

# Sidebar: Season Selector
with st.sidebar:
    st.header("🏈 League Settings")
    active_league_id = st.text_input("League ID", value=DEFAULT_LEAGUE_ID)
    
    selected_id = active_league_id
    if active_league_id and active_league_id != "YOUR_CURRENT_LEAGUE_ID_HERE":
        season_history = discover_all_seasons(active_league_id)
        if len(season_history) > 1:
            selected_season_label = st.selectbox("Select Season Year", options=list(season_history.keys()))
            selected_id = season_history[selected_season_label]
        elif len(season_history) == 1:
            st.caption(f"Showing: {list(season_history.keys())[0]}")
    st.divider()

# Main Dashboard
st.title("🏈 Sleeper Fantasy Trade Ledger")

if selected_id and selected_id != "YOUR_CURRENT_LEAGUE_ID_HERE":
    with st.spinner("Fetching transaction and scoring history..."):
        trades = fetch_trade_ledger(selected_id)
        
    if trades:
        total_margin = sum(t["margin"] for t in trades)
        biggest_fleece = max(trades, key=lambda x: x["margin"])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Completed Trades", len(trades))
        col2.metric("Biggest Point Swing", f"+{biggest_fleece['margin']} pts", f"Leader: {biggest_fleece['winner']}")
        col3.metric("Avg Margin per Trade", f"{round(total_margin/len(trades), 1)} pts")

        st.divider()
        st.subheader("Trade Breakdown")
        
        for t in trades:
            with st.container(border=True):
                head1, head2 = st.columns([3, 1])
                head1.markdown(f"#### 📅 Week {t['week']} Trade")
                head2.markdown(f"**Winner:** :green[{t['winner']}] (+{t['margin']} pts)")
                
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
    else:
        st.info("No completed trades found for the selected season.")
else:
    st.warning("Please configure your League ID in the code or sidebar.")
