import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Sleeper Trade Winner Tracker", page_icon="🏈", layout="wide")

# Custom Title & Header
st.title("🏈 Sleeper Fantasy Trade Ledger")
st.markdown("Track weekly fantasy point differentials to see who **won** or **lost** their trades.")

league_id = st.text_input("Enter Sleeper League ID:", placeholder="e.g. 104900000000000000")

@st.cache_data(ttl=3600)
def fetch_trade_ledger(league_id):
    BASE_URL = "https://api.sleeper.app/v1"
    
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

if league_id:
    with st.spinner("Fetching transaction history..."):
        trades = fetch_trade_ledger(league_id)
        
    if trades:
        # 1. Top KPI Metric Cards
        total_margin = sum(t["margin"] for t in trades)
        biggest_fleece = max(trades, key=lambda x: x["margin"])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Trades Made", len(trades))
        col2.metric("Biggest Point Swing", f"+{biggest_fleece['margin']} pts", f"Won by {biggest_fleece['winner']}")
        col3.metric("Avg Margin per Trade", f"{round(total_margin/len(trades), 1)} pts")

        st.divider()

        # 2. Visual Trade Cards
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
                    st.metric(label="Total Post-Trade Points", value=f"{t['pts_a']} pts")
                    
                with c2:
                    st.markdown(f"**{t['team_b']} received:**")
                    for p in t['players_b']:
                        st.markdown(f"- `{p}`")
                    st.metric(label="Total Post-Trade Points", value=f"{t['pts_b']} pts")
    else:
        st.info("No completed trades found for this League ID.")


