import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Sleeper Trade Winner Tracker", layout="wide")

st.title("🏈 Sleeper Fantasy Trade Ledger")
st.caption("Track all season trades and calculate net fantasy points won/lost.")

league_id = st.text_input("Enter your Sleeper League ID:", placeholder="e.g. 104900000000000000")

@st.cache_data(ttl=3600)
def fetch_all_trade_data(league_id):
    BASE_URL = "https://api.sleeper.app/v1"
    
    # 1. Fetch metadata
    users = requests.get(f"{BASE_URL}/league/{league_id}/users").json()
    user_map = {u["user_id"]: u.get("display_name", "Unknown") for u in users}

    rosters = requests.get(f"{BASE_URL}/league/{league_id}/rosters").json()
    roster_map = {r["roster_id"]: user_map.get(r["owner_id"], f"Team {r['roster_id']}") for r in rosters}

    players_data = requests.get(f"{BASE_URL}/players/nfl").json()
    player_names = {pid: p.get("full_name", pid) for pid, p in players_data.items()}

    # 2. Fetch Matchup Points for Weeks 1-18
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

    # 3. Fetch Transactions
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
                team_a_name = roster_map.get(team_a, f"Team {team_a}")
                team_b_name = roster_map.get(team_b, f"Team {team_b}")
                
                players_to_a = [pid for pid, r_id in adds.items() if r_id == team_a]
                players_to_b = [pid for pid, r_id in adds.items() if r_id == team_b]
                
                pts_a, pts_b = 0.0, 0.0
                for w in range(week + 1, 19):
                    if w in weekly_points:
                        for pid in players_to_a:
                            pts_a += weekly_points[w].get(pid, 0.0)
                        for pid in players_to_b:
                            pts_b += weekly_points[w].get(pid, 0.0)
                
                net_margin = round(pts_a - pts_b, 2)
                winner = team_a_name if net_margin > 0 else (team_b_name if net_margin < 0 else "Even")

                trade_list.append({
                    "Week": f"Week {week}",
                    "Team 1": team_a_name,
                    "Acquired by Team 1": ", ".join([player_names.get(p, p) for p in players_to_a]) or "None / Picks",
                    "Team 1 Pts": round(pts_a, 1),
                    "Team 2": team_b_name,
                    "Acquired by Team 2": ", ".join([player_names.get(p, p) for p in players_to_b]) or "None / Picks",
                    "Team 2 Pts": round(pts_b, 1),
                    "Current Winner": winner,
                    "Net Lead": abs(net_margin)
                })
    return trade_list

if league_id:
    with st.spinner("Crunching season trade stats..."):
        trades = fetch_all_trade_data(league_id)
        
    if trades:
        df = pd.DataFrame(trades)
        st.success(f"Found {len(trades)} completed trade(s)!")
        
        # Display as an interactive table
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No completed trades found in this league yet.")


