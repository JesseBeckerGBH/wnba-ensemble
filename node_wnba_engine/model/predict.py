#!/usr/bin/env python3
"""
D:/WNBA/model/predict.py

Predict a single WNBA game (moneyline + totals).

Usage:
    py -3.13 model/predict.py ^
      --home "Las Vegas Aces" ^
      --away "New York Liberty" ^
      --ml-home 1.75 ^
      --ml-away 2.15 ^
      --total-line 162.5 ^
      --over-odds 1.91 ^
      --under-odds 1.91

Returns:
    Home win probability, edge vs moneyline odds,
    predicted total direction and edge vs O/U line.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
from datetime import date, timedelta

import duckdb
import numpy as np
from dotenv import load_dotenv

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
load_dotenv(str(_ROOT / ".env"))

from model.stack_train import (
    load_latest_model,
    ML_FEATURE_COLS,
    TOT_FEATURE_COLS,
)

DB_PATH = os.getenv("WNBA_DB_PATH", str(_ROOT / "db" / "wnba.duckdb"))


# ── Team feature lookup ────────────────────────────────────────────────────────
def get_team_features(conn, team_name: str, as_of: date = None) -> dict:
    """
    Fetch rolling form + Elo for a team from game_features.
    Uses the team's most recent game prior to as_of (default: today).
    """
    if as_of is None:
        as_of = date.today()

    # Find team_id by name (fuzzy)
    team_id = conn.execute(
        """
        SELECT team_id FROM teams
        WHERE LOWER(team_name) LIKE LOWER(?) OR LOWER(team_abbrev) LIKE LOWER(?)
        LIMIT 1
        """,
        [f"%{team_name}%", f"%{team_name}%"],
    ).fetchone()

    if not team_id:
        print(f"  WARN: Team '{team_name}' not found — using league averages")
        return _league_avg_features(conn)

    team_id = team_id[0]

    row = conn.execute(
        """
        SELECT
            rolling_win_rate, rolling_pts_for, rolling_pts_against, rolling_net_pts,
            rolling_fg_pct, rolling_fg3_pct, rolling_ft_pct,
            rolling_tov_rate, rolling_reb_margin,
            pace, off_rating, def_rating, net_rating,
            days_rest, b2b, elo_pre, sentiment_score
        FROM game_features
        WHERE team_id = ? AND game_date < ?
        ORDER BY game_date DESC
        LIMIT 1
        """,
        [team_id, as_of],
    ).fetchone()

    if not row:
        print(f"  WARN: No feature history for '{team_name}' — using league averages")
        return _league_avg_features(conn)

    keys = [
        "rolling_win_rate", "rolling_pts_for", "rolling_pts_against", "rolling_net_pts",
        "rolling_fg_pct", "rolling_fg3_pct", "rolling_ft_pct",
        "rolling_tov_rate", "rolling_reb_margin",
        "pace", "off_rating", "def_rating", "net_rating",
        "days_rest", "b2b", "elo_pre", "sentiment_score",
    ]
    return dict(zip(keys, row))


def _league_avg_features(conn) -> dict:
    row = conn.execute("""
        SELECT
            AVG(rolling_win_rate), AVG(rolling_pts_for), AVG(rolling_pts_against),
            AVG(rolling_net_pts), AVG(rolling_fg_pct), AVG(rolling_fg3_pct),
            AVG(rolling_ft_pct), AVG(rolling_tov_rate), AVG(rolling_reb_margin),
            AVG(pace), AVG(off_rating), AVG(def_rating), AVG(net_rating),
            5.0 AS days_rest, 0 AS b2b, 1500.0 AS elo_pre, 0.0 AS sentiment
        FROM game_features
        WHERE game_date >= (CURRENT_DATE - INTERVAL '60 days')
    """).fetchone()
    keys = [
        "rolling_win_rate", "rolling_pts_for", "rolling_pts_against", "rolling_net_pts",
        "rolling_fg_pct", "rolling_fg3_pct", "rolling_ft_pct",
        "rolling_tov_rate", "rolling_reb_margin",
        "pace", "off_rating", "def_rating", "net_rating",
        "days_rest", "b2b", "elo_pre", "sentiment_score",
    ]
    return dict(zip(keys, row or [0.5] * len(keys)))


def get_h2h(conn, home_name: str, away_name: str) -> tuple[float, int]:
    """Return (h2h_win_rate_for_home, h2h_meetings)."""
    row = conn.execute("""
        SELECT
            COUNT(*)                                        AS meetings,
            SUM(CASE WHEN g.home_win THEN 1.0 ELSE 0.0 END) AS home_wins
        FROM games g
        JOIN teams th ON th.team_id = g.home_team_id
        JOIN teams ta ON ta.team_id = g.away_team_id
        WHERE (LOWER(th.team_name) LIKE LOWER(?) OR LOWER(th.team_abbrev) LIKE LOWER(?))
          AND (LOWER(ta.team_name) LIKE LOWER(?) OR LOWER(ta.team_abbrev) LIKE LOWER(?))
          AND g.home_score IS NOT NULL
          AND g.game_date >= (CURRENT_DATE - INTERVAL '730 days')
    """, [f"%{home_name}%", f"%{home_name}%",
          f"%{away_name}%", f"%{away_name}%"]).fetchone()
    if row and row[0] > 0:
        return float(row[1] / row[0]), int(row[0])
    return 0.5, 0


# ── Prediction ─────────────────────────────────────────────────────────────────
def predict(
    home_team: str,
    away_team: str,
    ml_home: float = None,
    ml_away: float = None,
    total_line: float = None,
    over_odds: float = None,
    under_odds: float = None,
    as_of: date = None,
) -> dict:
    conn = duckdb.connect(DB_PATH)
    try:
        home_f = get_team_features(conn, home_team, as_of)
        away_f = get_team_features(conn, away_team, as_of)
        h2h_rate, h2h_count = get_h2h(conn, home_team, away_team)
    finally:
        conn.close()

    # ── Build moneyline feature vector ─────────────────────────────────────────
    def d(h_key, a_key=None):
        h = home_f.get(h_key) or 0.0
        a = away_f.get(a_key or h_key) or 0.0
        return float(h) - float(a)

    ml_vec = {
        "rolling_win_rate_diff":   d("rolling_win_rate"),
        "rolling_pts_diff":        d("rolling_pts_for"),
        "rolling_net_pts_diff":    d("rolling_net_pts"),
        "rolling_fg_pct_diff":     d("rolling_fg_pct"),
        "rolling_fg3_pct_diff":    d("rolling_fg3_pct"),
        "rolling_tov_rate_diff":   d("rolling_tov_rate"),
        "rolling_reb_margin_diff": d("rolling_reb_margin"),
        "net_rating_diff":         d("net_rating"),
        "pace_diff":               d("pace"),
        "days_rest_diff":          d("days_rest"),
        "b2b_diff":                float(home_f.get("b2b", 0)) - float(away_f.get("b2b", 0)),
        "elo_diff":                float(home_f.get("elo_pre", 1500)) - float(away_f.get("elo_pre", 1500)),
        "h2h_win_rate":            h2h_rate,
        "h2h_meetings":            float(h2h_count),
        "home_advantage":          1.0,
        "sentiment_diff":          float(home_f.get("sentiment_score", 0)) - float(away_f.get("sentiment_score", 0)),
    }
    X_ml = np.array([[ml_vec.get(c, 0.0) for c in ML_FEATURE_COLS]], dtype=np.float32)

    # ── Moneyline prediction ───────────────────────────────────────────────────
    result = {}
    try:
        ml_meta  = load_latest_model("moneyline")
        ml_model = ml_meta["model"]
        medians  = np.array(ml_meta["col_medians"], dtype=np.float32)
        X_ml_imp = np.where(np.isnan(X_ml), medians, X_ml)
        home_win_prob = float(ml_model.predict_proba(X_ml_imp)[0][1])
        away_win_prob = 1.0 - home_win_prob

        result["home_win_prob"]  = home_win_prob
        result["away_win_prob"]  = away_win_prob
        result["ml_auc"]         = ml_meta.get("auc_test", 0.0)
        result["ml_version"]     = ml_meta.get("version", "?")

        if ml_home:
            impl_home = 1.0 / ml_home
            result["ml_edge_home"] = home_win_prob - impl_home
            result["impl_home"]    = impl_home
        if ml_away:
            impl_away = 1.0 / ml_away
            result["ml_edge_away"] = away_win_prob - impl_away
            result["impl_away"]    = impl_away

    except FileNotFoundError as e:
        result["error_ml"] = str(e)
        home_win_prob = 0.5

    # ── Totals prediction ──────────────────────────────────────────────────────
    if total_line is not None:
        tot_vec = {
            "home_rolling_pts_for":    home_f.get("rolling_pts_for", 80.0) or 80.0,
            "away_rolling_pts_for":    away_f.get("rolling_pts_for", 80.0) or 80.0,
            "home_rolling_pts_against": home_f.get("rolling_pts_against", 80.0) or 80.0,
            "away_rolling_pts_against": away_f.get("rolling_pts_against", 80.0) or 80.0,
            "home_off_rating":         max(home_f.get("net_rating", 0) or 0, 0),
            "away_off_rating":         max(away_f.get("net_rating", 0) or 0, 0),
            "home_def_rating":         -min(home_f.get("net_rating", 0) or 0, 0),
            "away_def_rating":         -min(away_f.get("net_rating", 0) or 0, 0),
            "home_pace":               home_f.get("pace", 90.0) or 90.0,
            "away_pace":               away_f.get("pace", 90.0) or 90.0,
            "home_days_rest":          home_f.get("days_rest", 3) or 3,
            "away_days_rest":          away_f.get("days_rest", 3) or 3,
            "home_fg_pct":             home_f.get("rolling_fg_pct", 0.45) or 0.45,
            "away_fg_pct":             away_f.get("rolling_fg_pct", 0.45) or 0.45,
            "home_fg3_pct":            home_f.get("rolling_fg3_pct", 0.35) or 0.35,
            "away_fg3_pct":            away_f.get("rolling_fg3_pct", 0.35) or 0.35,
        }
        X_tot = np.array([[tot_vec.get(c, 0.0) for c in TOT_FEATURE_COLS]], dtype=np.float32)

        try:
            tot_meta  = load_latest_model("totals")
            tot_model = tot_meta["model"]
            tot_med   = np.array(tot_meta["col_medians"], dtype=np.float32)
            X_tot_imp = np.where(np.isnan(X_tot), tot_med, X_tot)
            over_prob = float(tot_model.predict_proba(X_tot_imp)[0][1])

            result["over_prob"]   = over_prob
            result["under_prob"]  = 1.0 - over_prob
            result["tot_auc"]     = tot_meta.get("auc_test", 0.0)

            if over_odds:
                result["tot_edge_over"]  = over_prob - (1.0 / over_odds)
            if under_odds:
                result["tot_edge_under"] = (1.0 - over_prob) - (1.0 / under_odds)

        except FileNotFoundError as e:
            result["error_tot"] = str(e)

    return result


# ── CLI ────────────────────────────────────────────────────────────────────────
def _fmt_edge(edge, odds) -> str:
    if edge is None:
        return "  n/a "
    sign = "+" if edge >= 0 else ""
    return f"{sign}{edge:.1%}"


def main():
    p = argparse.ArgumentParser(description="WNBA single-game prediction")
    p.add_argument("--home",        required=True, help="Home team name")
    p.add_argument("--away",        required=True, help="Away team name")
    p.add_argument("--ml-home",     type=float,    help="Decimal odds: home win")
    p.add_argument("--ml-away",     type=float,    help="Decimal odds: away win")
    p.add_argument("--total-line",  type=float,    help="Total points line (e.g. 162.5)")
    p.add_argument("--over-odds",   type=float,    help="Decimal odds: over")
    p.add_argument("--under-odds",  type=float,    help="Decimal odds: under")
    args = p.parse_args()

    r = predict(
        home_team   = args.home,
        away_team   = args.away,
        ml_home     = args.ml_home,
        ml_away     = args.ml_away,
        total_line  = args.total_line,
        over_odds   = args.over_odds,
        under_odds  = args.under_odds,
    )

    if "error_ml" in r:
        print(f"\nERROR (moneyline model): {r['error_ml']}")
        print("Run: py -3.13 model/stack_train.py")
        return

    W = 60
    print(f"\n{'='*W}")
    print(f"  {args.home:25s}  vs  {args.away:25s}")
    print(f"{'-'*W}")
    print(f"  Home win prob : {r['home_win_prob']:.1%}     "
          f"Away win prob : {r['away_win_prob']:.1%}")

    if args.ml_home:
        print(f"\n  Moneyline:")
        print(f"    Home:  prob={r['home_win_prob']:.1%}  impl={r.get('impl_home',0):.1%}  "
              f"edge={_fmt_edge(r.get('ml_edge_home'), args.ml_home)}  "
              f"odds={args.ml_home:.2f}")
        print(f"    Away:  prob={r['away_win_prob']:.1%}  impl={r.get('impl_away',0):.1%}  "
              f"edge={_fmt_edge(r.get('ml_edge_away'), args.ml_away)}  "
              f"odds={args.ml_away:.2f}")

    if "over_prob" in r and args.total_line:
        print(f"\n  Totals (line={args.total_line}):")
        print(f"    Over:  prob={r['over_prob']:.1%}  "
              f"edge={_fmt_edge(r.get('tot_edge_over'), args.over_odds)}  "
              f"odds={args.over_odds or 'n/a'}")
        print(f"    Under: prob={r['under_prob']:.1%}  "
              f"edge={_fmt_edge(r.get('tot_edge_under'), args.under_odds)}  "
              f"odds={args.under_odds or 'n/a'}")

    print(f"\n  Model: {r.get('ml_version','?')}   AUC: {r.get('ml_auc',0):.4f}")
    print('='*W)


if __name__ == "__main__":
    main()
