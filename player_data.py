#!/usr/bin/env python3

import pandas as pd
from nba_api.stats.endpoints import *

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
    MperG = MP/player["GP"]
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
    team_fgm = team_stats["FGM"]

    USG = 100 * ((FGA + 0.44 * FTA + TOV) * (team_minutes)) / (MP * (team_fga + 0.44 * team_fta + team_tov))
    TS = PTS / (2 * (FGA + 0.44 * FTA))
    ASTP = 100 * AST * (team_minutes) / (MP * (team_fgm - FGM))
    EFG = (FGM + 0.5 * FG3M) / FGA
    TOVP = 100 * TOV / (FGA + 0.44 * FTA + TOV)

    stats_per_100 = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star='Regular Season',
        per_mode_detailed="Per100Possessions"
    ).get_data_frames()[0]
    player_per_100 = stats_per_100[stats_per_100["PLAYER_ID"] == player_id].iloc[0]
    print(player_per_100["FGM"])
    profile.update({"volume": {
        "USG_PCT": round(USG, 2).item(),
        "FGA_100": player_per_100["FGA"].item(),
        "MIN_PER_GAME": round(MperG, 2).item()
    }})

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
    shot_chart = shotchartdetail.ShotChartDetail(
        player_id=player_id,
        season_nullable=season,
        context_measure_simple="FGA",
        season_type_all_star="Regular Season",
        team_id=profile["team_id"]
    ).get_data_frames()[0]
    
    zone_stats_df = (
        shot_chart
        .groupby("SHOT_ZONE_BASIC")
        .agg(
            attempts=("SHOT_MADE_FLAG", "count"),
            fg_pct=("SHOT_MADE_FLAG", "mean"),
            efg_pct=("SHOT_MADE_FLAG", lambda x: (
                (shot_chart.loc[x.index, "SHOT_MADE_FLAG"] +
                 0.5 * shot_chart.loc[x.index, "SHOT_TYPE"].eq("3PT Field Goal").astype(int)
                ).sum() / len(x)
            ))
        )
        .reset_index()
    )

    # Round percentages
    zone_stats_df["fg_pct"] = zone_stats_df["fg_pct"].round(3)
    zone_stats_df["efg_pct"] = zone_stats_df["efg_pct"].round(3)

    # Convert to nested dictionary
    zone_stats = {
        row["SHOT_ZONE_BASIC"]: {
            "attempts": int(row["attempts"]),
            "fg_pct": row["fg_pct"],
            "efg_pct": row["efg_pct"]
        }
        for _, row in zone_stats_df.iterrows()
    }
    zone_stats.update({"Free Throw": {"attempts": player["FTA"], "fg_pct": player["FT_PCT"], "efg_pct": player["FT_PCT"]}})

    profile.update({"shotchart": zone_stats})

    return profile

if __name__ == "__main__":
    season = "2023-24"

    example_player_id = 201939  # Steph Curry
    player_data = get_player_profile(example_player_id, season=season)

    for k, v in player_data.items():
        print(f"{k}: {v}")
