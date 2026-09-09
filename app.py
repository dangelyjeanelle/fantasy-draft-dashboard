import streamlit as st
import pandas as pd
from difflib import get_close_matches

st.set_page_config(page_title="Draft Strategy Engine", layout="wide")

st.title("⚡ Dynamic Draft Recommendation Dashboard")
st.caption("League ID: 1721704463 | 8-Team PPR + Heavy IDP & Punters")

# --- INITIALIZE SESSION STATE ---
if "drafted_players" not in st.session_state:
    st.session_state["drafted_players"] = []

if "my_roster" not in st.session_state:
    st.session_state["my_roster"] = []

# --- MASTER RANKINGS DATA ---
@st.cache_data(ttl=600)
def load_draft_data():
    data = [
        {"Player": "Jahmyr Gibbs", "Pos": "RB", "ESPN_Rank": 1, "Consensus_ECR": 1, "Proj_Pts": 315.0, "VORP": 120.0},
        {"Player": "Ja'Marr Chase", "Pos": "WR", "ESPN_Rank": 2, "Consensus_ECR": 1, "Proj_Pts": 310.0, "VORP": 115.0},
        {"Player": "Puka Nacua", "Pos": "WR", "ESPN_Rank": 6, "Consensus_ECR": 3, "Proj_Pts": 298.0, "VORP": 103.0},
        {"Player": "Bijan Robinson", "Pos": "RB", "ESPN_Rank": 3, "Consensus_ECR": 2, "Proj_Pts": 292.0, "VORP": 97.0},
        {"Player": "CeeDee Lamb", "Pos": "WR", "ESPN_Rank": 10, "Consensus_ECR": 6, "Proj_Pts": 285.0, "VORP": 90.0},
        {"Player": "Josh Allen", "Pos": "QB", "ESPN_Rank": 25, "Consensus_ECR": 16, "Proj_Pts": 350.0, "VORP": 65.0},
        {"Player": "Brock Bowers", "Pos": "TE", "ESPN_Rank": 40, "Consensus_ECR": 24, "Proj_Pts": 220.0, "VORP": 50.0},
        {"Player": "Ladd McConkey", "Pos": "WR", "ESPN_Rank": 58, "Consensus_ECR": 34, "Proj_Pts": 230.0, "VORP": 35.0},
        {"Player": "Luther Burden III", "Pos": "WR", "ESPN_Rank": 72, "Consensus_ECR": 44, "Proj_Pts": 215.0, "VORP": 28.0},
        {"Player": "Roquan Smith", "Pos": "LB", "ESPN_Rank": 130, "Consensus_ECR": 60, "Proj_Pts": 205.0, "VORP": 75.0},
        {"Player": "Fred Warner", "Pos": "LB", "ESPN_Rank": 142, "Consensus_ECR": 68, "Proj_Pts": 195.0, "VORP": 65.0},
        {"Player": "Kyle Hamilton", "Pos": "S", "ESPN_Rank": 165, "Consensus_ECR": 90, "Proj_Pts": 160.0, "VORP": 30.0},
        {"Player": "Trent McDuffie", "Pos": "CB", "ESPN_Rank": 180, "Consensus_ECR": 110, "Proj_Pts": 145.0, "VORP": 25.0},
        {"Player": "AJ Cole", "Pos": "P", "ESPN_Rank": 220, "Consensus_ECR": 150, "Proj_Pts": 95.0, "VORP": 25.0},
    ]
    df = pd.DataFrame(data)
    df["Value_Delta"] = df["ESPN_Rank"] - df["Consensus_ECR"]
    return df

master_df = load_draft_data()

# Helper function to fuzzy match input names to master player names
def resolve_player_name(raw_input, available_list):
    if not raw_input:
        return None
    # 1. Exact or Substring match
    for p in available_list:
        if raw_input.lower() in p.lower():
            return p
    # 2. Fuzzy match for typos/punctuation
    matches = get_close_matches(raw_input, available_list, n=1, cutoff=0.5)
    return matches[0] if matches else None

# Filter Available vs My Team
available_df = master_df[~master_df["Player"].isin(st.session_state["drafted_players"])]
my_team_df = master_df[master_df["Player"].isin(st.session_state["my_roster"])]

available_names = available_df["Player"].tolist()

# --- CALLBACK FUNCTIONS ---
def handle_opponent_pick():
    selected = st.session_state.get("dropdown_selection")
    typed = st.session_state.get("text_selection")
    target = selected if selected else resolve_player_name(typed, available_names)
    
    if target and target not in st.session_state["drafted_players"]:
        st.session_state["drafted_players"].append(target)
    st.session_state["text_selection"] = ""

def handle_my_pick():
    selected = st.session_state.get("dropdown_selection")
    typed = st.session_state.get("text_selection")
    target = selected if selected else resolve_player_name(typed, available_names)
    
    if target and target not in st.session_state["drafted_players"]:
        st.session_state["drafted_players"].append(target)
        st.session_state["my_roster"].append(target)
    st.session_state["text_selection"] = ""

def reset_board():
    st.session_state["drafted_players"] = []
    st.session_state["my_roster"] = []
    st.session_state["text_selection"] = ""

# --- SIDEBAR DRAFT CONTROLS ---
st.sidebar.header("🕹️ Live Draft Controls")

st.sidebar.selectbox("Predictive Player Search:", options=[""] + available_names, key="dropdown_selection")
st.sidebar.text_input("Or Quick Type Name (Fuzzy Matching):", key="text_selection")

col1, col2 = st.sidebar.columns(2)
with col1:
    st.button("Cross Off (Opponent)", on_click=handle_opponent_pick, use_container_width=True)
with col2:
    st.button("Draft to MY TEAM", on_click=handle_my_pick, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.button("Reset Draft Board", on_click=reset_board, use_container_width=True)

# --- SENSIBLE POSITION ORDER RECOMMENDATION ENGINE ---
st.subheader("💡 Real-Time On-The-Clock Recommendations")

def get_sensible_recommendations(avail_df, my_df):
    recs = []
    my_pos = my_df["Pos"].value_counts().to_dict() if not my_df.empty else {}
    
    rb_count = my_pos.get("RB", 0)
    wr_count = my_pos.get("WR", 0)
    qb_count = my_pos.get("QB", 0)
    te_count = my_pos.get("TE", 0)
    lb_count = my_pos.get("LB", 0)

    # 1. Early Priority: Core Starters (RB/WR)
    if rb_count == 0 or wr_count == 0:
        top_skill = avail_df[avail_df["Pos"].isin(["RB", "WR"])].sort_values(by="VORP", ascending=False).head(2)
        for _, r in top_skill.iterrows():
            recs.append({
                "Priority": "1. High (Core Starter)",
                "Player": r["Player"],
                "Pos": r["Pos"],
                "Reason": f"Top available skill starter with {r['VORP']} VORP.",
                "Action": "MUST DRAFT" if r["Value_Delta"] <= 5 else "HIGH VALUE TARGET"
            })

    # 2. Mid Priority: Elite IDP Linebacker (2 required starters)
    if lb_count < 2:
        top_lbs = avail_df[avail_df["Pos"] == "LB"].head(1)
        if not top_lbs.empty:
            lbr = top_lbs.iloc[0]
            recs.append({
                "Priority": "2. Medium (IDP Advantage)",
                "Player": lbr["Player"],
                "Pos": "LB",
                "Reason": f"4pt sacks/1.5pt tackles give top LBs ~200 pts. ESPN ranks them low ({lbr['ESPN_Rank']}).",
                "Action": "STEAL TARGET (Delay 1-2 Rounds)"
            })

    # 3. Onesie Positions: QB / TE (Only 1 starter required)
    if qb_count == 0:
        top_qb = avail_df[avail_df["Pos"] == "QB"].head(1)
        if not top_qb.empty:
            qbr = top_qb.iloc[0]
            recs.append({
                "Priority": "3. Situational (QB)",
                "Player": qbr["Player"],
                "Pos": "QB",
                "Reason": "In 8-team leagues, QB depth is high. Only draft if top-tier QB falls.",
                "Action": "DRAFT IF ELITE TIER FALLS"
            })

    return pd.DataFrame(recs) if recs else pd.DataFrame(columns=["Priority", "Player", "Pos", "Reason", "Action"])

recs_df = get_sensible_recommendations(available_df, my_team_df)
st.dataframe(recs_df, use_container_width=True, hide_index=True)

st.markdown("---")

# --- MAIN DISPLAY GRID ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Available Players Grid")
    pos_selected = st.multiselect("Filter Positions:", ["QB", "RB", "WR", "TE", "LB", "S", "CB", "P"], default=["RB", "WR", "LB"])
    view_df = available_df[available_df["Pos"].isin(pos_selected)] if pos_selected else available_df
    st.dataframe(view_df.sort_values(by="VORP", ascending=False), use_container_width=True, hide_index=True)

with col2:
    st.subheader("🛡️ My Current Roster")
    st.caption(f"Players Drafted: {len(st.session_state['my_roster'])}")
    if not my_team_df.empty:
        st.dataframe(my_team_df[["Player", "Pos", "Proj_Pts"]], use_container_width=True, hide_index=True)
    else:
        st.info("No players drafted to your team yet.")
