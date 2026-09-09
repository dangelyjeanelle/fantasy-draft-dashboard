import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="Draft Arbitrage Dashboard | League 1721704463",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚡ Draft Arbitrage & Value Dashboard")
st.caption("League ID: 1721704463 | 8-Team PPR + High-Scoring IDP & Punters")

# --- SESSION STATE FOR LIVE DRAFTING ---
if "drafted_players" not in st.session_state:
    st.session_state["drafted_players"] = []

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Draft Management")

# Quick manual cross-off
player_to_draft = st.sidebar.text_input("Enter Player Name to Cross Off:")
if st.sidebar.button("Mark Drafted") and player_to_draft:
    st.session_state["drafted_players"].append(player_to_draft.strip())
    st.sidebar.success(f"Removed: {player_to_draft}")

if st.sidebar.button("Reset Draft Board"):
    st.session_state["drafted_players"] = []
    st.sidebar.warning("Board Reset!")

st.sidebar.markdown("---")
st.sidebar.write(f"**Total Drafted:** {len(st.session_state['drafted_players'])} players")
if st.session_state["drafted_players"]:
    with st.sidebar.expander("View Drafted List"):
        st.write(", ".join(st.session_state["drafted_players"]))

# --- MASTER DATASET (Custom Tuned for League Settings) ---
@st.cache_data(ttl=600)
def get_master_rankings():
    # Tuned specifically for 8-team PPR, boosted LBs (4pt Sack/FF/FR, 1.5pt Tackle), and Punters
    data = [
        # Skill Positions
        {"Player": "Jahmyr Gibbs", "Pos": "RB", "ESPN_Rank": 1, "Consensus_ECR": 1, "Proj_Pts": 315.0, "Tier": 1},
        {"Player": "Ja'Marr Chase", "Pos": "WR", "ESPN_Rank": 2, "Consensus_ECR": 1, "Proj_Pts": 310.0, "Tier": 1},
        {"Player": "Puka Nacua", "Pos": "WR", "ESPN_Rank": 6, "Consensus_ECR": 3, "Proj_Pts": 298.0, "Tier": 1},
        {"Player": "Bijan Robinson", "Pos": "RB", "ESPN_Rank": 3, "Consensus_ECR": 2, "Proj_Pts": 292.0, "Tier": 1},
        {"Player": "Amon-Ra St. Brown", "Pos": "WR", "ESPN_Rank": 12, "Consensus_ECR": 5, "Proj_Pts": 288.0, "Tier": 1},
        {"Player": "CeeDee Lamb", "Pos": "WR", "ESPN_Rank": 10, "Consensus_ECR": 6, "Proj_Pts": 285.0, "Tier": 1},
        {"Player": "Christian McCaffrey", "Pos": "RB", "ESPN_Rank": 4, "Consensus_ECR": 4, "Proj_Pts": 280.0, "Tier": 1},
        {"Player": "Josh Allen", "Pos": "QB", "ESPN_Rank": 25, "Consensus_ECR": 16, "Proj_Pts": 350.0, "Tier": 1},
        {"Player": "Lamar Jackson", "Pos": "QB", "ESPN_Rank": 38, "Consensus_ECR": 22, "Proj_Pts": 335.0, "Tier": 1},
        {"Player": "Brock Bowers", "Pos": "TE", "ESPN_Rank": 40, "Consensus_ECR": 24, "Proj_Pts": 220.0, "Tier": 1},
        {"Player": "Ladd McConkey", "Pos": "WR", "ESPN_Rank": 58, "Consensus_ECR": 34, "Proj_Pts": 230.0, "Tier": 2},
        {"Player": "Luther Burden III", "Pos": "WR", "ESPN_Rank": 72, "Consensus_ECR": 44, "Proj_Pts": 215.0, "Tier": 2},
        
        # High-Value IDPs (Scoring Boosted)
        {"Player": "Roquan Smith", "Pos": "LB", "ESPN_Rank": 130, "Consensus_ECR": 60, "Proj_Pts": 205.0, "Tier": 1},
        {"Player": "Fred Warner", "Pos": "LB", "ESPN_Rank": 142, "Consensus_ECR": 68, "Proj_Pts": 195.0, "Tier": 1},
        {"Player": "Foyesade Oluokun", "Pos": "LB", "ESPN_Rank": 150, "Consensus_ECR": 75, "Proj_Pts": 188.0, "Tier": 1},
        {"Player": "Kyle Hamilton", "Pos": "S", "ESPN_Rank": 165, "Consensus_ECR": 90, "Proj_Pts": 160.0, "Tier": 1},
        {"Player": "Trent McDuffie", "Pos": "CB", "ESPN_Rank": 180, "Consensus_ECR": 110, "Proj_Pts": 145.0, "Tier": 1},
        
        # High-Value Punters (44+ Yd Bonus + In20)
        {"Player": "AJ Cole", "Pos": "P", "ESPN_Rank": 220, "Consensus_ECR": 150, "Proj_Pts": 95.0, "Tier": 1},
        {"Player": "Ryan Stonehouse", "Pos": "P", "ESPN_Rank": 225, "Consensus_ECR": 155, "Proj_Pts": 92.0, "Tier": 1},
    ]
    df = pd.DataFrame(data)
    df["Arbitrage_Value"] = df["ESPN_Rank"] - df["Consensus_ECR"]
    return df

master_df = get_master_rankings()

# Filter out drafted players
available_df = master_df[~master_df["Player"].isin(st.session_state["drafted_players"])]

# --- LAYOUT SETUP ---
col1, col2 = st.columns([2.5, 1])

with col1:
    st.subheader("🎯 Market Arbitrage Grid (Best Value Picks)")
    st.caption("Positive **Arbitrage Value** means ESPN ranks them LOWER than industry consensus (Draft Targets).")
    
    # Filtering Controls
    pos_selected = st.multiselect(
        "Filter Positions:",
        options=["QB", "RB", "WR", "TE", "LB", "S", "CB", "P"],
        default=["RB", "WR", "LB"]
    )
    
    if pos_selected:
        view_df = available_df[available_df["Pos"].isin(pos_selected)]
    else:
        view_df = available_df

    st.dataframe(
        view_df.sort_values(by="Arbitrage_Value", ascending=False),
        column_config={
            "Arbitrage_Value": st.column_config.NumberColumn(
                "Value Delta (Rounds/Picks)",
                help="Higher positive numbers = Steals on ESPN!",
                format="+%d"
            ),
            "Proj_Pts": st.column_config.NumberColumn("Projected Points", format="%.1f pts")
        },
        use_container_width=True,
        hide_index=True
    )

with col2:
    st.subheader("⚠️ Positional Tier Cliffs")
    st.caption("Drop-off in point production to the next available tier.")
    
    # Calculate real-time top gaps
    for pos in ["WR", "RB", "LB", "QB"]:
        pos_avail = available_df[available_df["Pos"] == pos]
        if len(pos_avail) >= 2:
            gap = pos_avail.iloc[0]["Proj_Pts"] - pos_avail.iloc[1]["Proj_Pts"]
            top_player = pos_avail.iloc[0]["Player"]
            st.metric(
                label=f"Next Best {pos} ({top_player})",
                value=f"{pos_avail.iloc[0]['Proj_Pts']} pts",
                delta=f"-{gap:.1f} pts to next option",
                delta_color="inverse"
            )

st.markdown("---")
st.info("💡 **Draft Strategy Tip for Tonight:** Because your league has 2 LB starters with 4pt sacks/turnovers & 1.5pt tackles, top LBs (Roquan, Warner) outscore WR2s. ESPN's default client places LBs in rounds 15+, allowing you to scoop up elite starters late!")
