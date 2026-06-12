#!/usr/bin/env python3
"""
D:/WNBA/scripts/todays_bets.py

Daily WNBA bet sheet — moneyline + totals.

Fetches today's/upcoming WNBA games from The Odds API (or BetsAPI),
runs dual-target ML predictions, and prints a ranked bet sheet
showing edge vs bookmaker odds with Kelly stake recommendations.

Usage:
    py -3.13 scripts/todays_bets.py --bankroll 1000
    py -3.13 scripts/todays_bets.py --bankroll 500 --min-edge 0.06
    py -3.13 scripts/todays_bets.py --dry-run   # manual MANUAL_GAMES list
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
from datetime import datetime

import duckdb
from dotenv import load_dotenv

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
load_dotenv(str(_ROOT / ".env"))

# ── Thresholds (matches wf_v2 backtest parameters) ───────────────────────────
MIN_EDGE     = 0.05   # minimum edge to show a bet
MIN_PROB     = 0.55   # minimum model probability
AUC_GATE     = 0.58   # warn if model AUC < this
MAX_BET_FRAC = 0.10   # hard cap: max 10% of bankroll per bet

# Manual fallback for --dry-run
MANUAL_GAMES = [
    {"home": "Las Vegas Aces", "away": "New York Liberty",
     "ml_home": 1.65, "ml_away": 2.30,
     "total_line": 162.5, "over_odds": 1.91, "under_odds": 1.91},
]

DB_PATH = os.getenv("WNBA_DB_PATH", str(_ROOT / "db" / "wnba.duckdb"))


def grade_bet(edge: float, prob: float) -> str:
    if edge >= 0.12 and prob >= 0.68:
        return "A+"
    elif edge >= 0.08 and prob >= 0.62:
        return "A"
    elif edge >= 0.05 and prob >= 0.58:
        return "B"
    else:
        return "C"


import subprocess
import json

def kelly_stake(edge: float, odds: float, prob: float, bankroll: float) -> float:
    # Offload calculus to Rust Math Matrix
    rust_bin = str(_ROOT.parent / 'math_engine_rust' / 'target' / 'release' / 'math_engine_rust.exe')
    if not os.path.exists(rust_bin):
        # Fallback if rust binary isn't built yet, though it should be
        rust_bin = str(_ROOT.parent / 'math_engine_rust' / 'target' / 'release' / 'math_engine_rust')
    
    # args: <true_prob> <dec_odds> <kelly_slider> <bankroll>
    # Hardcoding kelly slider to 0.25 (Quarter Kelly) as it was in the python logic
    cmd = [rust_bin, str(prob), str(odds), "0.25", str(bankroll)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Parse the JSON response
        rust_json = json.loads(res.stdout.strip())
        wager_amount = float(rust_json.get("wager_amount", 0.0))
        return wager_amount
    except Exception as e:
        print(f"[!] RUST IPC ERROR: {e} | STDOUT: {e.stdout if hasattr(e, 'stdout') else ''}")
        return 0.0


def _sep(w=110):
    print("─" * w)


def run(args):
    # ── Load models ───────────────────────────────────────────────────────────
    from model.stack_train import load_latest_model
    from model.predict import predict

    try:
        ml_meta  = load_latest_model("moneyline")
        tot_meta = load_latest_model("totals")
    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("Run: py -3.13 model/stack_train.py")
        return

    ml_auc  = ml_meta.get("auc_test", 0.0)
    tot_auc = tot_meta.get("auc_test", 0.0)

    print(f"\n[models]")
    print(f"  Moneyline: {ml_meta['version']}   AUC={ml_auc:.4f}   Brier={ml_meta.get('brier_test',0):.4f}   "
          f"n={ml_meta.get('n_train',0)} games")
    print(f"  Totals:    {tot_meta['version']}   AUC={tot_auc:.4f}   Brier={tot_meta.get('brier_test',0):.4f}   "
          f"n={tot_meta.get('n_train',0)} games")

    for label, auc in [("Moneyline", ml_auc), ("Totals", tot_auc)]:
        if auc < AUC_GATE:
            print(f"  ⚠  WARNING: {label} AUC {auc:.3f} < gate {AUC_GATE}. Retrain recommended.")
        else:
            print(f"  ✓ {label} passes AUC gate ({auc:.3f} >= {AUC_GATE})")

    # ── Fetch games ───────────────────────────────────────────────────────────
    games = []
    if args.dry_run:
        print("\n[dry-run] Using MANUAL_GAMES list")
        games = MANUAL_GAMES
    else:
        try:
            from scripts.odds_client import theodds_get_upcoming
            print("\n[odds] Fetching upcoming WNBA games from The Odds API...")
            raw = theodds_get_upcoming()
            for ev in raw:
                if ev.get("home_ml") and ev.get("away_ml"):
                    games.append({
                        "home":       ev["home"],
                        "away":       ev["away"],
                        "ml_home":    ev["home_ml"],
                        "ml_away":    ev["away_ml"],
                        "total_line": ev.get("total_line"),
                        "over_odds":  ev.get("over_odds"),
                        "under_odds": ev.get("under_odds"),
                        "start":      ev.get("start", ""),
                    })
            print(f"  {len(raw)} games found, {len(games)} have ML odds")
        except Exception as e:
            print(f"\n[odds] Error: {e}")
            print("  Check ODDS_API_KEY in .env or use --dry-run")
            return

    if not games:
        print("No games with odds found.")
        return

    # ── Run predictions ───────────────────────────────────────────────────────
    bets = []
    for g in games:
        try:
            r = predict(
                home_team   = g["home"],
                away_team   = g["away"],
                ml_home     = g.get("ml_home"),
                ml_away     = g.get("ml_away"),
                total_line  = g.get("total_line"),
                over_odds   = g.get("over_odds"),
                under_odds  = g.get("under_odds"),
            )
        except Exception as ex:
            print(f"  WARN: {g['home']} vs {g['away']} — {ex}")
            continue

        # ── Moneyline bets ─────────────────────────────────────────────────
        if ml_auc >= AUC_GATE:
            for team, prob, edge, odds in [
                (g["home"], r.get("home_win_prob", 0), r.get("ml_edge_home", -1), g.get("ml_home")),
                (g["away"], r.get("away_win_prob", 0), r.get("ml_edge_away", -1), g.get("ml_away")),
            ]:
                if edge is None or edge < MIN_EDGE or prob < MIN_PROB or not odds:
                    continue
                stake = kelly_stake(edge, odds, prob, args.bankroll)
                bets.append({
                    "type":     "ML",
                    "grade":    grade_bet(edge, prob),
                    "matchup":  f"{g['home']} vs {g['away']}",
                    "pick":     team,
                    "prob":     prob,
                    "impl":     1.0 / odds,
                    "edge":     edge,
                    "odds":     odds,
                    "stake":    stake,
                    "start":    g.get("start", ""),
                })

        # ── Totals bets ────────────────────────────────────────────────────
        if tot_auc >= AUC_GATE and g.get("total_line"):
            for direction, prob, edge, odds in [
                ("Over",  r.get("over_prob",  0), r.get("tot_edge_over",  -1), g.get("over_odds")),
                ("Under", r.get("under_prob", 0), r.get("tot_edge_under", -1), g.get("under_odds")),
            ]:
                if edge is None or edge < MIN_EDGE or prob < MIN_PROB or not odds:
                    continue
                stake = kelly_stake(edge, odds, prob, args.bankroll)
                bets.append({
                    "type":     "TOT",
                    "grade":    grade_bet(edge, prob),
                    "matchup":  f"{g['home']} vs {g['away']}",
                    "pick":     f"{direction} {g['total_line']}",
                    "prob":     prob,
                    "impl":     1.0 / odds,
                    "edge":     edge,
                    "odds":     odds,
                    "stake":    stake,
                    "start":    g.get("start", ""),
                })

    # ── Print bet sheet ───────────────────────────────────────────────────────
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n{'='*110}")
    print(f"  WNBA BET SHEET    {ts}    Bankroll: £{args.bankroll:,.0f}")
    print(f"  Min edge: {MIN_EDGE:.0%}   Min prob: {MIN_PROB:.0%}   AUC gate: {AUC_GATE}   Max stake: {MAX_BET_FRAC:.0%}/bet")
    print(f"{'='*110}")

    if not bets:
        print(f"\n  No qualifying bets (edge < {MIN_EDGE:.0%} or prob < {MIN_PROB:.0%} for all games).\n")
        return

    grade_order = {"A+": 0, "A": 1, "B": 2, "C": 3}
    bets.sort(key=lambda x: (grade_order[x["grade"]], -x["edge"]))

    print(f"\n  {'Gr':3s} {'T':3s} {'Pick':22s} {'Matchup':40s} "
          f"{'Prob':6s} {'Impl':6s} {'Edge':6s} {'Odds':6s} {'Stake':8s}  {'Start'}")
    _sep()

    for b in bets:
        print(
            f"  {b['grade']:3s} {b['type']:3s} {b['pick']:22s} {b['matchup']:40s} "
            f"{b['prob']:5.1%} {b['impl']:5.1%} {b['edge']:+5.1%} "
            f"{b['odds']:5.2f} £{b['stake']:7.2f}  {b['start'][:16]}"
        )

    _sep()
    total_stake = sum(b["stake"] for b in bets)
    expected    = sum(b["stake"] * b["edge"] for b in bets)
    print(f"\n  {len(bets)} qualifying bet(s)   "
          f"Total stake: £{total_stake:,.2f}   "
          f"Expected profit: £{expected:,.2f}\n")
    print("  Grade key:  A+ = edge≥12% & prob≥68%   "
          "A = edge≥8% & prob≥62%   "
          "B = edge≥5% & prob≥58%\n")


def main():
    global MIN_EDGE
    p = argparse.ArgumentParser(description="WNBA daily bet sheet")
    p.add_argument("--bankroll",   type=float, default=1000.0)
    p.add_argument("--min-edge",   type=float, default=MIN_EDGE)
    p.add_argument("--dry-run",    action="store_true")
    args = p.parse_args()
    MIN_EDGE = args.min_edge
    run(args)


if __name__ == "__main__":
    main()
