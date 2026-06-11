#!/usr/bin/env python3
"""
node_nba_engine/data/ingest_nba.py

Load NBA historical game data from nba_api into DuckDB.
nba_api uses league_id='00' for NBA.

Usage:
    python data/ingest_nba.py --seasons 2020 2021 2022 2023 2024 2025
    python data/ingest_nba.py --seasons 2025 --boxscores
    python data/ingest_nba.py --teams
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
import time

import duckdb
import pandas as pd
from dotenv import load_dotenv

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
load_dotenv(str(_ROOT / ".env"))

DB_PATH = os.getenv("NBA_DB_PATH", str(_ROOT / "db" / "nba.duckdb"))
SLEEP   = 0.8

try:
    from nba_api.stats.endpoints import (
        LeagueGameLog,
        BoxScoreTraditionalV2,
    )
except ImportError:
    print("ERROR: nba_api not installed. Run: pip install nba_api")
    sys.exit(1)

NBA_LEAGUE_ID = "00"


def get_conn() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(DB_PATH)
    conn.execute(open(_ROOT / "db" / "schema.sql").read())
    return conn


# ── NBA Teams ──────────────────────────────────────────────────────────────────
def ingest_teams(conn: duckdb.DuckDBPyConnection) -> int:
    """Load all 30 NBA teams."""
    nba_teams = [
        # Eastern Conference — Atlantic
        ("1610612738", "Boston Celtics",       "BOS", "Boston",       "Eastern", "Atlantic"),
        ("1610612751", "Brooklyn Nets",        "BKN", "Brooklyn",     "Eastern", "Atlantic"),
        ("1610612752", "New York Knicks",      "NYK", "New York",     "Eastern", "Atlantic"),
        ("1610612755", "Philadelphia 76ers",   "PHI", "Philadelphia", "Eastern", "Atlantic"),
        ("1610612761", "Toronto Raptors",      "TOR", "Toronto",      "Eastern", "Atlantic"),
        # Eastern Conference — Central
        ("1610612741", "Chicago Bulls",        "CHI", "Chicago",      "Eastern", "Central"),
        ("1610612739", "Cleveland Cavaliers",  "CLE", "Cleveland",    "Eastern", "Central"),
        ("1610612765", "Detroit Pistons",      "DET", "Detroit",      "Eastern", "Central"),
        ("1610612754", "Indiana Pacers",       "IND", "Indianapolis", "Eastern", "Central"),
        ("1610612749", "Milwaukee Bucks",      "MIL", "Milwaukee",    "Eastern", "Central"),
        # Eastern Conference — Southeast
        ("1610612737", "Atlanta Hawks",        "ATL", "Atlanta",      "Eastern", "Southeast"),
        ("1610612766", "Charlotte Hornets",    "CHA", "Charlotte",    "Eastern", "Southeast"),
        ("1610612748", "Miami Heat",           "MIA", "Miami",        "Eastern", "Southeast"),
        ("1610612753", "Orlando Magic",        "ORL", "Orlando",      "Eastern", "Southeast"),
        ("1610612764", "Washington Wizards",   "WAS", "Washington",   "Eastern", "Southeast"),
        # Western Conference — Northwest
        ("1610612743", "Denver Nuggets",       "DEN", "Denver",       "Western", "Northwest"),
        ("1610612750", "Minnesota Timberwolves","MIN","Minneapolis",  "Western", "Northwest"),
        ("1610612760", "Oklahoma City Thunder","OKC", "Oklahoma City","Western", "Northwest"),
        ("1610612757", "Portland Trail Blazers","POR","Portland",     "Western", "Northwest"),
        ("1610612762", "Utah Jazz",            "UTA", "Salt Lake City","Western","Northwest"),
        # Western Conference — Pacific
        ("1610612744", "Golden State Warriors","GSW", "San Francisco","Western", "Pacific"),
        ("1610612746", "LA Clippers",          "LAC", "Los Angeles",  "Western", "Pacific"),
        ("1610612747", "Los Angeles Lakers",   "LAL", "Los Angeles",  "Western", "Pacific"),
        ("1610612756", "Phoenix Suns",         "PHX", "Phoenix",      "Western", "Pacific"),
        ("1610612758", "Sacramento Kings",     "SAC", "Sacramento",   "Western", "Pacific"),
        # Western Conference — Southwest
        ("1610612742", "Dallas Mavericks",     "DAL", "Dallas",       "Western", "Southwest"),
        ("1610612745", "Houston Rockets",      "HOU", "Houston",      "Western", "Southwest"),
        ("1610612763", "Memphis Grizzlies",    "MEM", "Memphis",      "Western", "Southwest"),
        ("1610612740", "New Orleans Pelicans",  "NOP","New Orleans",  "Western", "Southwest"),
        ("1610612759", "San Antonio Spurs",    "SAS", "San Antonio",  "Western", "Southwest"),
    ]
    conn.executemany(
        """
        INSERT OR REPLACE INTO teams
            (team_id, team_name, team_abbrev, city, conference, division)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        nba_teams,
    )
    n = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    print(f"  Teams: {n} rows in DB")
    return n


def ingest_season(conn: duckdb.DuckDBPyConnection, season_year: int,
                   season_type: str = "Regular Season") -> int:
    """Load all games for an NBA season."""
    label = "playoffs" if season_type == "Playoffs" else "regular"
    print(f"\n  [season {season_year} {label}] Fetching game log...")

    try:
        log = LeagueGameLog(
            league_id=NBA_LEAGUE_ID,
            season=str(season_year),
            season_type_all_star=season_type,
            timeout=60,
        )
        df = log.get_data_frames()[0]
    except Exception as e:
        print(f"    ERROR fetching season {season_year}: {e}")
        return 0

    if df.empty:
        print(f"    No data for {season_year} {label}")
        return 0

    print(f"    {len(df)} team-game rows (= {len(df)//2} games)")
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"]).dt.date

    games_inserted = 0
    is_playoffs = season_type == "Playoffs"

    for game_id, grp in df.groupby("GAME_ID"):
        grp = grp.reset_index(drop=True)
        if len(grp) != 2:
            continue

        home_row = grp[grp["MATCHUP"].str.contains(r"vs\.")]
        away_row = grp[grp["MATCHUP"].str.contains("@")]
        if home_row.empty or away_row.empty:
            home_row = grp.iloc[[0]]
            away_row = grp.iloc[[1]]

        home = home_row.iloc[0]
        away = away_row.iloc[0]

        home_score = int(home["PTS"]) if pd.notna(home["PTS"]) else None
        away_score = int(away["PTS"]) if pd.notna(away["PTS"]) else None
        home_win   = (home["WL"] == "W") if home["WL"] in ("W", "L") else None

        conn.execute(
            """
            INSERT OR REPLACE INTO games
                (game_id, season_year, game_date, home_team_id, away_team_id,
                 home_score, away_score, home_win, is_playoffs, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Final')
            """,
            [
                str(game_id), season_year, home["GAME_DATE"],
                str(home["TEAM_ID"]), str(away["TEAM_ID"]),
                home_score, away_score, home_win, is_playoffs,
            ],
        )
        games_inserted += 1

    print(f"    Inserted/updated {games_inserted} games")
    time.sleep(SLEEP)
    return games_inserted


def ingest_boxscores(conn: duckdb.DuckDBPyConnection, season_year: int) -> int:
    """Load team box score stats for all games in a season."""
    game_ids = conn.execute(
        "SELECT game_id FROM games WHERE season_year = ? AND home_score IS NOT NULL",
        [season_year],
    ).fetchall()
    game_ids = [r[0] for r in game_ids]

    already = set(
        r[0] for r in conn.execute(
            "SELECT DISTINCT game_id FROM team_game_stats"
        ).fetchall()
    )
    to_load = [g for g in game_ids if g not in already]
    print(f"\n  [boxscores {season_year}] {len(to_load)} games to load...")

    loaded = 0
    for i, game_id in enumerate(to_load):
        if i % 50 == 0 and i > 0:
            print(f"    Progress: {i}/{len(to_load)}...")
        team_df = None
        for attempt in range(3):
            try:
                bs = BoxScoreTraditionalV2(game_id=game_id, timeout=45)
                team_df = bs.team_stats.get_data_frame()
                break
            except Exception as e:
                wait = (attempt + 1) * 5
                time.sleep(wait)
        if team_df is None:
            continue

        for _, row in team_df.iterrows():
            is_home = conn.execute(
                "SELECT home_team_id = ? FROM games WHERE game_id = ?",
                [str(row["TEAM_ID"]), game_id],
            ).fetchone()
            is_home = is_home[0] if is_home else False

            conn.execute(
                """
                INSERT OR REPLACE INTO team_game_stats
                    (game_id, team_id, is_home, pts, fgm, fga, fg_pct,
                     fg3m, fg3a, fg3_pct, ftm, fta, ft_pct,
                     oreb, dreb, reb, ast, stl, blk, tov, pf, plus_minus)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    game_id, str(row["TEAM_ID"]), is_home,
                    _i(row, "PTS"),  _i(row, "FGM"),  _i(row, "FGA"),
                    _f(row, "FG_PCT"),
                    _i(row, "FG3M"), _i(row, "FG3A"), _f(row, "FG3_PCT"),
                    _i(row, "FTM"),  _i(row, "FTA"),  _f(row, "FT_PCT"),
                    _i(row, "OREB"), _i(row, "DREB"), _i(row, "REB"),
                    _i(row, "AST"),  _i(row, "STL"),  _i(row, "BLK"),
                    _i(row, "TOV"),  _i(row, "PF"),   _f(row, "PLUS_MINUS"),
                ],
            )
        loaded += 1
        time.sleep(SLEEP)

    print(f"    Loaded {loaded} game box scores")
    return loaded


def _i(row, col):
    v = row.get(col)
    return int(v) if pd.notna(v) else None

def _f(row, col):
    v = row.get(col)
    return float(v) if pd.notna(v) else None


def main():
    p = argparse.ArgumentParser(description="NBA data ingestion via nba_api")
    p.add_argument("--seasons",    nargs="+", type=int, default=[2025],
                   help="Season year(s) to load")
    p.add_argument("--teams",      action="store_true", help="Refresh team roster")
    p.add_argument("--boxscores",  action="store_true", help="Load box scores (slower)")
    p.add_argument("--playoffs",   action="store_true", help="Also load playoff games")
    args = p.parse_args()

    print(f"\n[NBA ingest] DB: {DB_PATH}")
    conn = get_conn()

    print("\n[teams] Loading NBA roster...")
    ingest_teams(conn)

    total_games = 0
    for yr in sorted(args.seasons):
        n = ingest_season(conn, yr)
        total_games += n
        if args.playoffs:
            n += ingest_season(conn, yr, "Playoffs")
        if args.boxscores:
            ingest_boxscores(conn, yr)

    conn.close()
    print(f"\n[done] {total_games} games across {len(args.seasons)} season(s)")


if __name__ == "__main__":
    main()
