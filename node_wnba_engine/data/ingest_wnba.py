#!/usr/bin/env python3
"""
D:/WNBA/data/ingest_wnba.py

Load WNBA historical game data from nba_api into DuckDB.

nba_api uses league_id='10' for WNBA.
WNBA seasons: 2019–2025 (2024 = most recent complete season, Aces won).
2026 expansion: Toronto + Portland.

Usage:
    py -3.13 data/ingest_wnba.py --seasons 2019 2020 2021 2022 2023 2024
    py -3.13 data/ingest_wnba.py --seasons 2024        # single season refresh
    py -3.13 data/ingest_wnba.py --seasons 2024 --boxscores  # include box scores
    py -3.13 data/ingest_wnba.py --teams               # refresh team roster
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
import time
import uuid
from datetime import datetime

import duckdb
import pandas as pd
from dotenv import load_dotenv

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
load_dotenv(str(_ROOT / ".env"))

DB_PATH = os.getenv("WNBA_DB_PATH", str(_ROOT / "db" / "wnba.duckdb"))
SLEEP   = 0.8   # seconds between nba_api calls to avoid rate limiting

# ── nba_api imports ────────────────────────────────────────────────────────────
try:
    from nba_api.stats.endpoints import (
        LeagueGameLog,
        BoxScoreTraditionalV2,
        TeamInfoCommon,
    )
    from nba_api.stats.static import teams as nba_teams_static
except ImportError:
    print("ERROR: nba_api not installed. Run: py -3.13 -m pip install nba_api")
    sys.exit(1)

WNBA_LEAGUE_ID = "10"


# ── DB helpers ─────────────────────────────────────────────────────────────────
def get_conn() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(DB_PATH)
    conn.execute(open(_ROOT / "db" / "schema.sql").read())
    return conn


# ── Team roster ────────────────────────────────────────────────────────────────
def ingest_teams(conn: duckdb.DuckDBPyConnection) -> int:
    """Load all WNBA teams into the teams table."""
    # nba_api static teams for WNBA (league_id '10')
    # Note: nba_api.stats.static.teams doesn't separate WNBA — use TeamInfoCommon
    # We'll seed from a known list and supplement with API data
    known_teams = [
        # (team_id, team_name, abbrev, city, conference, joined_year, is_expansion)
        ("1611661313", "Atlanta Dream",          "ATL", "Atlanta",     "Eastern", 2008,  False),
        ("1611661329", "Chicago Sky",             "CHI", "Chicago",     "Eastern", 2006,  False),
        ("1611661323", "Connecticut Sun",         "CON", "Connecticut", "Eastern", 1999,  False),
        ("1611661319", "Indiana Fever",           "IND", "Indianapolis","Eastern", 2000,  False),
        ("1611661324", "New York Liberty",        "NYL", "New York",    "Eastern", 1997,  False),
        ("1611661320", "Washington Mystics",      "WAS", "Washington",  "Eastern", 1998,  False),
        ("1611661330", "Dallas Wings",            "DAL", "Dallas",      "Western", 2016,  False),
        ("1611661325", "Golden State Valkyries",  "GSV", "San Francisco","Western",2025,  False),
        ("1611661321", "Las Vegas Aces",          "LVA", "Las Vegas",   "Western", 2018,  False),
        ("1611661328", "Los Angeles Sparks",      "LAS", "Los Angeles", "Western", 1997,  False),
        ("1611661326", "Minnesota Lynx",          "MIN", "Minneapolis", "Western", 1999,  False),
        ("1611661322", "Phoenix Mercury",         "PHX", "Phoenix",     "Western", 1997,  False),
        ("1611661327", "Seattle Storm",           "SEA", "Seattle",     "Western", 2000,  False),
        # 2026 expansion teams (IDs are placeholders until nba_api confirms them)
        ("9999001",    "Toronto Tempo",           "TOR", "Toronto",     "Eastern", 2026,  True),
        ("9999002",    "Portland Fire",           "POR", "Portland",    "Western", 2026,  True),
    ]
    conn.executemany(
        """
        INSERT OR REPLACE INTO teams
            (team_id, team_name, team_abbrev, city, conference, joined_year, is_expansion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        known_teams,
    )
    n = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    print(f"  Teams: {n} rows in DB")
    return n


# ── Game log ───────────────────────────────────────────────────────────────────
def ingest_season(conn: duckdb.DuckDBPyConnection, season_year: int) -> int:
    """
    Load all games for a WNBA season from LeagueGameLog.
    season_year: e.g. 2024  → season_id '22024' (nba_api format for WNBA)
    """
    # WNBA season_id format: '2' + year (e.g. '22024')
    season_id = f"2{season_year}"
    print(f"\n  [season {season_year}] Fetching game log (season_id={season_id})...")

    try:
        log = LeagueGameLog(
            league_id=WNBA_LEAGUE_ID,
            season=str(season_year),
            season_type_all_star="Regular Season",
            timeout=60,
        )
        df = log.get_data_frames()[0]
    except Exception as e:
        print(f"    ERROR fetching season {season_year}: {e}")
        return 0

    if df.empty:
        print(f"    No data returned for season {season_year}")
        return 0

    print(f"    {len(df)} team-game rows (= {len(df)//2} games)")

    # LeagueGameLog gives one row per team per game.
    # Pair up home/away rows by GAME_ID.
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"]).dt.date

    games_inserted = 0
    # Group by GAME_ID — each group should have exactly 2 rows (home + away)
    for game_id, grp in df.groupby("GAME_ID"):
        grp = grp.reset_index(drop=True)
        if len(grp) != 2:
            continue

        # Identify home vs away from MATCHUP column: "X vs. Y" = home, "X @ Y" = away
        home_row = grp[grp["MATCHUP"].str.contains("vs\\.")]
        away_row = grp[grp["MATCHUP"].str.contains("@")]
        if home_row.empty or away_row.empty:
            # Fallback: use WL and pts
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
                 home_score, away_score, home_win, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Final')
            """,
            [
                str(game_id),
                season_year,
                home["GAME_DATE"],
                str(home["TEAM_ID"]),
                str(away["TEAM_ID"]),
                home_score,
                away_score,
                home_win,
            ],
        )
        games_inserted += 1

    print(f"    Inserted/updated {games_inserted} games")
    time.sleep(SLEEP)
    return games_inserted


def ingest_season_playoffs(conn: duckdb.DuckDBPyConnection, season_year: int) -> int:
    """Load playoff games for a WNBA season."""
    print(f"\n  [season {season_year}] Fetching playoffs...")
    try:
        log = LeagueGameLog(
            league_id=WNBA_LEAGUE_ID,
            season=str(season_year),
            season_type_all_star="Playoffs",
            timeout=60,
        )
        df = log.get_data_frames()[0]
    except Exception as e:
        print(f"    ERROR: {e}")
        return 0

    if df.empty:
        return 0

    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"]).dt.date
    games_inserted = 0

    for game_id, grp in df.groupby("GAME_ID"):
        grp = grp.reset_index(drop=True)
        if len(grp) != 2:
            continue
        home_row = grp[grp["MATCHUP"].str.contains("vs\\.")]
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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRUE, 'Final')
            """,
            [str(game_id), season_year, home["GAME_DATE"],
             str(home["TEAM_ID"]), str(away["TEAM_ID"]),
             home_score, away_score, home_win],
        )
        games_inserted += 1

    print(f"    Inserted {games_inserted} playoff games")
    time.sleep(SLEEP)
    return games_inserted


# ── Box scores ─────────────────────────────────────────────────────────────────
def ingest_boxscores(conn: duckdb.DuckDBPyConnection, season_year: int) -> int:
    """
    Load team box score stats for all games in a season.
    Slower — makes one API call per game.
    """
    game_ids = conn.execute(
        "SELECT game_id FROM games WHERE season_year = ? AND home_score IS NOT NULL",
        [season_year],
    ).fetchall()
    game_ids = [r[0] for r in game_ids]

    # Skip games already loaded
    already = set(
        r[0] for r in conn.execute(
            "SELECT DISTINCT game_id FROM team_game_stats"
        ).fetchall()
    )
    to_load = [g for g in game_ids if g not in already]
    print(f"\n  [boxscores {season_year}] {len(to_load)} games to load...")

    loaded = 0
    for i, game_id in enumerate(to_load):
        if i % 20 == 0 and i > 0:
            print(f"    Progress: {i}/{len(to_load)}...")
        team_df = None
        for attempt in range(3):
            try:
                bs = BoxScoreTraditionalV2(game_id=game_id, timeout=45)
                team_df = bs.team_stats.get_data_frame()
                break
            except Exception as e:
                wait = (attempt + 1) * 5
                print(f"    WARN: {game_id} attempt {attempt+1}/3 failed ({type(e).__name__}) - wait {wait}s")
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
                    game_id,
                    str(row["TEAM_ID"]),
                    is_home,
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


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="WNBA data ingestion via nba_api")
    p.add_argument("--seasons",    nargs="+", type=int, default=[2024],
                   help="Season year(s) to load, e.g. 2019 2020 2021 2022 2023 2024")
    p.add_argument("--teams",      action="store_true", help="Refresh team roster")
    p.add_argument("--boxscores",  action="store_true",
                   help="Also load per-team box score stats (slower — 1 API call/game)")
    p.add_argument("--playoffs",   action="store_true", help="Also load playoff games")
    args = p.parse_args()

    print(f"\n[WNBA ingest] DB: {DB_PATH}")
    conn = get_conn()

    if args.teams or True:  # always refresh teams
        print("\n[teams] Loading team roster...")
        ingest_teams(conn)

    total_games = 0
    for yr in sorted(args.seasons):
        n = ingest_season(conn, yr)
        total_games += n
        if args.playoffs:
            ingest_season_playoffs(conn, yr)
        if args.boxscores:
            ingest_boxscores(conn, yr)

    conn.close()
    print(f"\n[done] {total_games} games inserted/updated across {len(args.seasons)} season(s)")


if __name__ == "__main__":
    main()
