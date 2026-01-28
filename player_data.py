#!/usr/bin/env python3
"""
Full NBA Player Data Extractor
Pulls season-level stats for embedding/player profiling:
- Bio, position, size
- Traditional + advanced metrics
- Shot chart / shot diet
- Shot type breakdown (C&S, Pull-up)
- Passing / playmaking
- Offensive roles (synergy play types)
- Defensive metrics
- Hustle counts
- Tracking stats aggregated across the season (BoxScorePlayerTrackV3)
- Combine / physical measurements
"""

import pandas as pd
from nba_api.stats.endpoints import (
    commonplayerinfo,
    leaguedashplayerstats,
    shotchartdetail,
    playerdashptshots,
    playerdashptpass,
    synergyplaytypes,
    leaguedashptdefend,
    leaguehustlestatsplayer,
    boxscoreplayertrackv3,
    draftcombineplayeranthro,
    leaguegamelog,
    leaguedashteamstats
)
import time

# ------------------------------
# Helper function: tracking aggregation
# ------------------------------
def aggregate_tracking(season="2023-24"):
    print("Aggregating tracking stats across all games...")
    games = leaguegamelog.LeagueGameLog(season=season).get_data_frames()[0]
    game_ids = games["GAME_ID"].unique()
    all_tracking = []

    for gid in game_ids:
        try:
            df = boxscoreplayertrackv3.BoxScorePlayerTrackV3(game_id=gid).get_data_frames()[0]
            all_tracking.append(df)
            time.sleep(0.6)  # prevent API rate limit
        except Exception as e:
            print(f"Skipping game {gid} due to error: {e}")

    tracking_data = pd.concat(all_tracking, ignore_index=True)
    season_aggregates = tracking_data.groupby("PLAYER_ID").agg({
        "TOUCHES": "sum",
        "PASSES": "sum",
        "SECONDARY_ASSISTS": "sum",
        "SPEED": "mean",
        "DISTANCE": "mean"
    }).reset_index()
    return season_aggregates

# ------------------------------
# Main player profile function
# ------------------------------
def get_player_profile(player_id, season="2023-24", tracking_df=None):
    profile = {}
    # 1) Bio / Position / Size
    info = commonplayerinfo.CommonPlayerInfo(player_id)
    bio = info.get_data_frames()[0].iloc[0]
    profile.update({
        "team_id": bio["TEAM_ID"],
        "player_id": player_id,
        "player_name": bio["DISPLAY_FIRST_LAST"],
        "position": bio["POSITION"],
        "height": bio["HEIGHT"],
        "weight": bio["WEIGHT"]
    })

    # 2) Advanced Box Stats
    stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star='Regular Season',
        per_mode_detailed="Totals"
    ).get_data_frames()[0]
    player = stats[stats["PLAYER_ID"] == player_id].iloc[0]
    profile.update({
        "fga": player["FGA"],
        "fta": player["FTA"],
        "fg3_pct": player["FG3_PCT"],
        "GP": player["GP"]
    })

    all_team_stats = leaguedashteamstats.LeagueDashTeamStats(
        season=season,
        per_mode_detailed="Totals",
        season_type_all_star="Regular Season"
    ).get_data_frames()[0]

    team_stats = all_team_stats[all_team_stats["TEAM_ID"] == player['TEAM_ID']].iloc[0]

    MP = player["MIN"]
    FGA = player["FGA"]
    FTA = player["FTA"]
    TOV = player["TOV"]
    PTS = player["PTS"]
    AST = player["AST"]
    FGM = player["FGM"]
    FG3M = player["FG3M"]

    team_minutes = team_stats["MIN"]
    team_fga = team_stats["FGA"]
    team_fta = team_stats["FTA"]
    team_tov = team_stats["TOV"]
    team_pts = team_stats["PTS"]
    team_fgm = team_stats["FGM"]

    USG = 100 * ((FGA + 0.44 * FTA + TOV) * (team_minutes)) / (MP * (team_fga + 0.44 * team_fta + team_tov))
    TS = PTS / (2 * (FGA + 0.44 * FTA))
    ASTP = 100 * AST * (team_minutes) / (MP * (team_fgm - FGM))
    EFG = (FGM + 0.5 * FG3M) / FGA
    TOVP = 100 * TOV / (FGA + 0.44 * FTA + TOV)

    profile.update({
        "USG_PCT": round(USG, 2),
        "TS_PCT": round(TS, 3),
        "AST_PCT": round(ASTP, 2),
        "EFG_PCT": round(EFG, 3),
        "TOV_PCT": round(TOVP, 2),
        "PTS": PTS,
        "AST": AST,
        "REB": player["REB"],
        "STL": player["STL"],
        "BLK": player["BLK"],
        "PLUS_MINUS": player["PLUS_MINUS"]
    })

# ---DATA DOESN'T EXIST---
#     play_types = [
#     "PRBallHandler", "PRRollMan", "SpotUp", "Handoff",
#     "Isolation", "OffScreen", "Cut", "PostUp", "OffRebound",
#     "Transition", "Misc"
# ]

#     roles = {}
#     for p in play_types:
#         try:
#             df = synergyplaytypes.SynergyPlayTypes(
#                 player_or_team_abbreviation=profile["player_name"],
#                 play_type_nullable=p,
#                 season=season
#             ).get_data_frames()[0]

#             roles[p] = {
#                 "freq": df["POSS_PCT"].mean(),
#                 "tov_rate": df["TOV_POSS_PCT"].mean(),
#                 "ppp": df["PPP"].mean()
#             }   
#         except:
#             print('no data for', p)
#     profile.update(roles) 

    # 3) Shot Location / Shot Diet
    shots = shotchartdetail.ShotChartDetail(
        player_id=player_id,
        season_nullable=season,
        context_measure_simple="FGA",
        season_type_all_star="Regular Season",
        team_id=profile["team_id"]
    ).get_data_frames()[0]
    
    zone_stats = (
        shots
        .groupby("SHOT_ZONE_BASIC")
        .agg(
            attempts=("SHOT_MADE_FLAG", "count"),
            fg_pct=("SHOT_MADE_FLAG", "mean"),
            efg_pct=("SHOT_MADE_FLAG", lambda x: (
                (shots.loc[x.index, "SHOT_MADE_FLAG"] +
                 0.5 * shots.loc[x.index, "SHOT_TYPE"].eq("3PT Field Goal").astype(int)
                ).sum() / len(x)
            ))
        )
        .reset_index()
    )

    zone_stats["fg_pct"] = zone_stats["fg_pct"].round(3)
    zone_stats["efg_pct"] = zone_stats["efg_pct"].round(3)
    profile.update(zone_stats)

    # # 5) Passing / Playmaking
    # passing = playerdashptpass.PlayerDashPtPass(player_id).get_data_frames()[0].iloc[0]
    # profile["potential_ast"] = passing["POTENTIAL_AST"]
    # profile["passes_made"] = passing["PASSES_MADE"]

    # # 6) Offensive Role (Synergy)
    # roles = {}
    # for p in ["Isolation", "PRBallHandler", "PRRollMan", "SpotUp", "OffScreen", "Cut", "PostUp"]:
    #     df = synergyplaytypes.SynergyPlayTypes(
    #         player_id=player_id,
    #         play_type=p,
    #         season=season
    #     ).get_data_frames()[0]
    #     roles[p] = {"freq": df["POSS_PCT"].mean(), "ppp": df["PPP"].mean()}
    # profile["off_roles"] = roles

    # # 7) Defensive Metrics
    # defend = leaguedashptdefend.LeagueDashPtDefend().get_data_frames()[0]
    # d = defend[defend["PLAYER_ID"] == player_id].iloc[0]
    # profile.update({
    #     "defended_fg_pct": d["D_FG_PCT"],
    #     "rim_def_pct": d["D_FG_PCT_LT_6"]
    # })

    # # 8) Hustle Stats
    # hustle = leaguehustlestatsplayer.LeagueHustleStatsPlayer(season=season).get_data_frames()[0]
    # h = hustle[hustle["PLAYER_ID"] == player_id].iloc[0]
    # profile.update({
    #     "deflections": h["DEFLECTIONS"],
    #     "contested_shots": h["CONTESTED_SHOTS"],
    #     "loose_balls": h["LOOSE_BALLS_RECOVERED"],
    #     "charges": h["CHARGES_DRAWN"],
    #     "screen_assists": h["SCREEN_ASSISTS"]
    # })

    # # 9) Tracking Aggregated Stats (if precomputed)
    # # if tracking_df is not None and player_id in tracking_df["PLAYER_ID"].values:
    # #     track_row = tracking_df[tracking_df["PLAYER_ID"] == player_id].iloc[0]
    # #     profile.update({
    # #         "touches": track_row["TOUCHES"],
    # #         "passes_tracking": track_row["PASSES"],
    # #         "secondary_assists": track_row["SECONDARY_ASSISTS"],
    # #         "avg_speed": track_row["SPEED"],
    # #         "avg_distance": track_row["DISTANCE"]
    # #     })

    # # 10) Draft Combine / Physicals
    # try:
    #     combine = draftcombineplayeranthro.DraftCombinePlayerAnthro().get_data_frames()[0]
    #     c = combine[combine["PLAYER_ID"] == player_id]
    #     if len(c) > 0:
    #         c = c.iloc[0]
    #         profile.update({
    #             "wingspan": c["WINGSPAN"],
    #             "vert": c["MAX_VERTICAL"],
    #             "agility": c["LANE_AGILITY_TIME"],
    #             "sprint": c["THREE_QUARTER_SPRINT"]
    #         })
    # except:
    #     pass

    return profile

# ------------------------------
# Example Usage
# ------------------------------
if __name__ == "__main__":
    season = "2023-24"

    # Step 1: Aggregate tracking stats for the season
    # tracking_df = aggregate_tracking(season=season)

    # Step 2: Pull a single player profile
    example_player_id = 201939  # Jayson Tatum
    player_data = get_player_profile(example_player_id, season=season)

    # Print the player profile
    for k, v in player_data.items():
        print(f"{k}: {v}")
