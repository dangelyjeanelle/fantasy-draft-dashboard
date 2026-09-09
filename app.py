import streamlit as st
import pandas as pd

st.set_page_config(page_title="Draft Strategy & Real-Time Engine", layout="wide")

st.title("⚡ Dynamic Draft Recommendation Dashboard")
st.caption("League ID: 1721704463 | 8-Team PPR + Heavy IDP & Punters")

# --- SESSION STATE MANAGEMENT ---
if "drafted_players" not in st.session_state:
    st.session_state["drafted_players"] = []

if "my_roster" not in st.session_state:
    st.session_state["my_roster"] = []

# --- SIDEBAR: DRAFT & ROSTER CONTROLS ---
st.sidebar.header("🕹️ Live Draft Controls")

col_sb1, col_sb2 = st.sidebar.columns(2)
player_input = st.sidebar.text_input("Player Name:")

if st.sidebar.button("Cross Off (Opponent Pick)"):
    if player_input:
        st.session_state["drafted_players"].append(player_input.strip())
        st.sidebar.success(f"Crossed off: {player_input}")

if st.sidebar.button("Draft to MY TEAM"):
    if player_input:
        st.session_state["drafted_players"].append(player_input.strip())
        st.session_state["my_roster"].append(player_input.strip())
        st.sidebar.balloons()

if st.sidebar.button("Reset Draft Board"):
    st.session_state["drafted_players"] = []
    st.session_state["my_roster"] = []
    st.sidebar.warning("Reset Complete")

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
available_df = master_df[~master_df["Player"].isin(st.session_state["drafted_players"])]
my_team_df = master_df[master_df["Player"].isin(st.session_state["my_roster"])]

# --- REAL-TIME RECOMMENDATION ENGINE ---
st.subheader("💡 Real-Time On-The-Clock Pick Recommendations")

def get_recommendations(avail_df, my_df):
    recs = []
    
    # Analyze my current position counts
    my_positions = my_df["Pos"].value_counts().to_dict()
    
    # 1. Check for Highest VORP available
    top_vorp = avail_df.sort_values(by="VORP", ascending=False).head(3)
    for _, row in top_vorp.iterrows():
        recs.append({
            "Player": row["Player"],
            "Pos": row["Pos"],
            "Reason": f"Highest available VORP ({row['VORP']} pts over baseline). Pure talent pick.",
            "Action": "DRAFT NOW" if row["Value_Delta"] <= 10 else "CONSIDER / WAIT"
        })
        
    # 2. Check for IDP Advantage (If LB starter needed)
    lb_count = my_positions.get("LB", 0)
    if lb_count < 2:
        top_lbs = avail_df[avail_df["Pos"] == "LB"].head(1)
        if not top_lbs.empty:
            lb_row = top_lbs.iloc[0]
            recs.append({
                "Player": lb_row["Player"],
                "Pos": "LB",
                "Reason": f"ESPN ranks LBs low (Rank {lb_row['ESPN_Rank']}), but 4pt sacks/1.5pt tackles make him an elite starter.",
                "Action": "STEAL TARGET (Can delay 1-2 rounds)"
            })
            
    return pd.DataFrame(recs)

recommendations_df = get_recommendations(available_df, my_team_df)

st.dataframe(
    recommendations_df,
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# --- MAIN DISPLAY GRID ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Available Players Grid")
    pos_selected = st.multiselect("Filter Position:", ["QB", "RB", "WR", "TE", "LB", "S", "CB", "P"], default=["RB", "WR", "LB"])
    view_df = available_df[available_df["Pos"].isin(pos_selected)] if pos_selected else available_df
    st.dataframe(view_df.sort_values(by="VORP", ascending=False), use_container_width=True, hide_index=True)

with col2:
    st.subheader("🛡️ My Current Roster")
    if not my_team_df.empty:
        st.dataframe(my_team_df[["Player", "Pos", "Proj_Pts"]], use_container_width=True, hide_index=True)
    else:
        st.info("No players drafted to your team yet.")
