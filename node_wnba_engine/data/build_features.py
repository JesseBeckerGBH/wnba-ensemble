#!/usr/bin/env python3
"""
D:/WNBA/data/build_features.py

Compute ML features for every completed WNBA game and write to game_features table.

Features computed per team per game (using only data PRIOR to that game):
  - Rolling form (last 10 games): win rate, pts for/against, FG%, FG3%, FT%, TOV, REB margin
  - Pace + efficiency: possessions/40, OFF RTG, DEF RTG, NET RTG
  - Rest: days since last game, back-to-back flag
  - Elo rating (1500 start, K=20)
  - H2H: win rate and avg total vs opponent in last 2 seasons
  - Sentiment: most recent snapshot before game

Usage:
    py -3.13 data/build_features.py
    py -3.13 data/build_features.py --season 2024  # rebuild just one season
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
from collections import defaultdict
from datetime import timedelta

import duckdb
import pandas as pd
import numpy as np
from dotenv import load_dotenv

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
load_dotenv(str(_ROOT / ".env"))

DB_PATH = os.getenv("WNBA_DB_PATH", str(_ROOT / "db" / "wnba.duckdb"))
ROLLING_WINDOW = 10   # last N games for rolling stats
ELO_K          = 20   # Elo K-factor
ELO_START      = 1500.0


def get_conn() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(DB_PATH)


# ── Elo ────────────────────────────────────────────────────────────────────────
def expected_elo(r_a: float, r_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((r_b - r_a) / 400.0))

def update_elo(r_a: float, r_b: float, a_won: bool):
    e_a = expected_elo(r_a, r_b)
    new_a = r_a + ELO_K * ((1.0 if a_won else 0.0) - e_a)
    new_b = r_b + ELO_K * ((0.0 if a_won else 1.0) - (1.0 - e_a))
    return new_a, new_b


# ── Possessions estimate ───────────────────────────────────────────────────────
def possessions(fga, oreb, tov, fta, fg3a=0):
    """Estimate possessions from box score."""
    def _n(v):  # convert pd.NA / None to 0.0
        try:
            return float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            return 0.0
    if fga is None or _n(fga) == 0:
        return None
    return (_n(fga) - _n(oreb) + _n(tov) + 0.44 * _n(fta))


def build_features(conn: duckdb.DuckDBPyConnection, season_filter: int | None = None):
    # Load all completed games ordered by date
    where = f"WHERE g.home_score IS NOT NULL"
    if season_filter:
        where += f" AND g.season_year = {season_filter}"

    games_df = conn.execute(f"""
        SELECT g.game_id, g.game_date, g.season_year,
               g.home_team_id, g.away_team_id,
               g.home_score, g.away_score, g.home_win
        FROM games g
        {where}
        ORDER BY g.game_date, g.game_id
    """).df()

    if games_df.empty:
        print("No completed games found.")
        return

    # Load box scores (team stats)
    tgs = conn.execute("""
        SELECT game_id, team_id, pts, fgm, fga, fg_pct, fg3m, fg3a, fg3_pct,
               ftm, fta, ft_pct, oreb, dreb, reb, ast, stl, blk, tov, pf
        FROM team_game_stats
    """).df()
    tgs_map = {(r.game_id, r.team_id): r for _, r in tgs.iterrows()}

    # Load sentiment
    sent = conn.execute("""
        SELECT game_id, team_id, AVG(sentiment_score) AS sent_score
        FROM sentiment
        GROUP BY game_id, team_id
    """).df()
    sent_map = {}
    for _, r in sent.iterrows():
        sent_map[(r.game_id, r.team_id)] = r.sent_score

    # Per-team state: rolling deque, Elo, etc.
    team_history: dict[str, list[dict]] = defaultdict(list)  # sorted list of past games
    elo: dict[str, float] = defaultdict(lambda: ELO_START)

    rows_written = 0
    # Clear existing features for season if requested
    if season_filter:
        conn.execute(
            "DELETE FROM game_features WHERE season_year = ?", [season_filter]
        )
    else:
        conn.execute("DELETE FROM game_features")

    for _, game in games_df.iterrows():
        gid  = game.game_id
        date = pd.Timestamp(game.game_date).date()
        home_id = str(game.home_team_id)
        away_id = str(game.away_team_id)

        for team_id, opp_id, is_home in [
            (home_id, away_id, True),
            (away_id, home_id, False),
        ]:
            hist = team_history[team_id]
            opp_hist = team_history[opp_id]
            elo_pre = elo[team_id]
            opp_elo = elo[opp_id]

            # ── Rolling form ─────────────────────────────────────────────────
            recent = hist[-ROLLING_WINDOW:]

            def avg(key, default=None):
                vals = [g[key] for g in recent if g.get(key) is not None]
                return float(np.mean(vals)) if vals else default

            rolling_win_rate    = avg("won", 0.5)
            rolling_pts_for     = avg("pts_for")
            rolling_pts_against = avg("pts_against")
            rolling_net_pts     = (
                (rolling_pts_for - rolling_pts_against)
                if rolling_pts_for and rolling_pts_against else None
            )
            rolling_fg_pct  = avg("fg_pct")
            rolling_fg3_pct = avg("fg3_pct")
            rolling_ft_pct  = avg("ft_pct")
            rolling_tov_rate = avg("tov_rate")
            rolling_reb_margin = avg("reb_margin")

            # ── Pace / efficiency ─────────────────────────────────────────────
            pace = avg("pace")
            off_rating = avg("off_rating")
            def_rating = avg("def_rating")
            net_rating = (
                (off_rating - def_rating)
                if off_rating and def_rating else None
            )

            # ── Rest ──────────────────────────────────────────────────────────
            days_rest = None
            b2b       = False
            if hist:
                last_date = pd.Timestamp(hist[-1]["date"]).date()
                days_rest = (date - last_date).days
                b2b = days_rest == 1

            # ── H2H ───────────────────────────────────────────────────────────
            h2h_games = [
                g for g in hist
                if g.get("opp_id") == opp_id and g.get("date") is not None
                and (date - pd.Timestamp(g["date"]).date()).days <= 730
            ]
            h2h_meetings  = len(h2h_games)
            h2h_win_rate  = float(np.mean([g["won"] for g in h2h_games])) if h2h_games else 0.5
            h2h_avg_total = (
                float(np.mean([g["pts_for"] + g.get("pts_against", 0) for g in h2h_games]))
                if h2h_games else None
            )

            # ── Sentiment ─────────────────────────────────────────────────────
            sentiment_score = sent_map.get((gid, team_id), 0.0)

            # ── Target labels ─────────────────────────────────────────────────
            won_ml = None
            if game.home_win is not None:
                won_ml = bool(game.home_win) if is_home else not bool(game.home_win)

            # Total line + over determination handled in todays_bets.py
            # Here we just record the raw total
            total_pts = None
            if game.home_score is not None and game.away_score is not None:
                total_pts = int(game.home_score) + int(game.away_score)

            conn.execute(
                """
                INSERT OR REPLACE INTO game_features (
                    game_id, team_id, opp_team_id, game_date, season_year, is_home,
                    rolling_win_rate, rolling_pts_for, rolling_pts_against, rolling_net_pts,
                    rolling_fg_pct, rolling_fg3_pct, rolling_ft_pct,
                    rolling_tov_rate, rolling_reb_margin,
                    pace, off_rating, def_rating, net_rating,
                    days_rest, b2b,
                    elo_pre, opp_elo_pre, elo_diff,
                    h2h_win_rate, h2h_avg_total, h2h_meetings,
                    sentiment_score,
                    won_moneyline, total_line
                ) VALUES (
                    ?,?,?,?,?,?,
                    ?,?,?,?,
                    ?,?,?,
                    ?,?,
                    ?,?,?,?,
                    ?,?,
                    ?,?,?,
                    ?,?,?,
                    ?,
                    ?,?
                )
                """,
                [
                    gid, team_id, opp_id, date, int(game.season_year), is_home,
                    rolling_win_rate, rolling_pts_for, rolling_pts_against, rolling_net_pts,
                    rolling_fg_pct, rolling_fg3_pct, rolling_ft_pct,
                    rolling_tov_rate, rolling_reb_margin,
                    pace, off_rating, def_rating, net_rating,
                    days_rest, b2b,
                    elo_pre, opp_elo, (elo_pre - opp_elo) if elo_pre and opp_elo else None,
                    h2h_win_rate, h2h_avg_total, h2h_meetings,
                    sentiment_score,
                    won_ml, total_pts,
                ],
            )
            rows_written += 1

        # ── Update Elo after game ──────────────────────────────────────────────
        if game.home_win is not None:
            new_home, new_away = update_elo(
                elo[home_id], elo[away_id], bool(game.home_win)
            )
            elo[home_id] = new_home
            elo[away_id] = new_away

        # ── Update team history ────────────────────────────────────────────────
        for team_id, opp_id, is_home in [
            (home_id, away_id, True),
            (away_id, home_id, False),
        ]:
            won_flag = (
                (bool(game.home_win) if is_home else not bool(game.home_win))
                if game.home_win is not None else None
            )
            bs = tgs_map.get((gid, team_id))
            opp_bs = tgs_map.get((gid, opp_id))

            pts_for     = int(game.home_score if is_home else game.away_score) if game.home_score else None
            pts_against = int(game.away_score if is_home else game.home_score) if game.away_score else None

            poss = possessions(
                bs.fga if bs is not None else None,
                bs.oreb if bs is not None else None,
                bs.tov if bs is not None else None,
                bs.fta if bs is not None else None,
            ) if bs is not None else None

            def _f(v):
                """Safe float from pandas Series value — returns None for NA/None/0."""
                try:
                    f = float(v)
                    return f if f == f else None  # NaN check
                except (TypeError, ValueError):
                    return None

            bs_tov  = _f(bs.tov)  if bs is not None else None
            bs_reb  = _f(bs.reb)  if bs is not None else None
            obs_reb = _f(opp_bs.reb) if opp_bs is not None else None

            team_history[team_id].append({
                "date":       date,
                "opp_id":     opp_id,
                "won":        float(won_flag) if won_flag is not None else 0.5,
                "pts_for":    pts_for,
                "pts_against": pts_against,
                "fg_pct":     _f(bs.fg_pct)  if bs is not None else None,
                "fg3_pct":    _f(bs.fg3_pct) if bs is not None else None,
                "ft_pct":     _f(bs.ft_pct)  if bs is not None else None,
                "tov_rate":   (bs_tov / poss * 100) if (bs_tov and poss) else None,
                "reb_margin": (bs_reb - obs_reb) if (bs_reb is not None and obs_reb is not None) else None,
                "pace":       poss,
                "off_rating": (pts_for / poss * 100) if (pts_for and poss) else None,
                "def_rating": (pts_against / poss * 100) if (pts_against and poss) else None,
            })

    print(f"  Wrote {rows_written} feature rows")


def main():
    p = argparse.ArgumentParser(description="Build WNBA game features")
    p.add_argument("--season", type=int, default=None,
                   help="Rebuild features for a single season (default: all)")
    args = p.parse_args()

    print(f"[features] DB: {DB_PATH}")
    conn = get_conn()
    build_features(conn, season_filter=args.season)
    conn.close()
    print("[done]")


if __name__ == "__main__":
    main()
