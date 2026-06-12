#!/usr/bin/env python3
"""
D:/WNBA/backtesting/backtest_walkforward.py

Walk-forward backtest for WNBA dual-target model.
Same wf_v2 pattern as darts_v2 with:
  - AUC gate (skip all bets if model AUC < 0.58)
  - Min probability filter (>= 0.55)
  - Hard bet cap (max 10% per bet)
  - Quarter-Kelly sizing

Window: 300 games train, 60 games test, step 30 games.
(Smaller than darts because WNBA has fewer games/year.)

Usage:
    py -3.13 backtesting/backtest_walkforward.py
    py -3.13 backtesting/backtest_walkforward.py --target moneyline
    py -3.13 backtesting/backtest_walkforward.py --target totals
    py -3.13 backtesting/backtest_walkforward.py --train-window 200 --test-window 40
"""

from __future__ import annotations

import argparse
import csv
import os
import pathlib
import sys
import uuid
from datetime import datetime

import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, brier_score_loss
from dotenv import load_dotenv

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
load_dotenv(str(_ROOT / ".env"))

DB_PATH     = os.getenv("WNBA_DB_PATH", str(_ROOT / "db" / "wnba.duckdb"))
RESULTS_DIR = _ROOT / "backtesting" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

from model.stack_train import (
    load_game_data, build_stacking_model,
    ML_FEATURE_COLS, TOT_FEATURE_COLS,
)

# ── Bet gate parameters (matching todays_bets.py) ────────────────────────────
AUC_GATE     = 0.58
MIN_EDGE     = 0.05
MIN_PROB     = 0.55
KELLY_FRAC   = 0.25
MAX_BET_FRAC = 0.10
INITIAL_BK   = 1000.0
VERSION      = "wf_v2"


def run_single_target(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    implied_col: str,     # column with bookmaker implied prob (1/odds)
    train_window: int,
    test_window: int,
    step: int,
) -> list[dict]:
    """
    Walk-forward backtest for a single target (moneyline or totals).
    Returns list of window result dicts.
    """
    # Only require target + implied_col to be non-null; features will be imputed
    sub = df[feature_cols + [target_col, implied_col, "game_date"]].copy()
    sub = sub.dropna(subset=[target_col, implied_col]).reset_index(drop=True)
    if len(sub) < train_window + test_window:
        print(f"  Not enough data ({len(sub)} rows) for {target_col} backtest")
        return []

    results = []
    i = 0
    while i + train_window + test_window <= len(sub):
        train_df = sub.iloc[i : i + train_window]
        test_df  = sub.iloc[i + train_window : i + train_window + test_window]

        def _to_float32(df_part, cols):
            out = df_part[cols].copy()
            for c in cols:
                out[c] = pd.to_numeric(out[c], errors="coerce")
            return out.to_numpy(dtype=np.float64, na_value=np.nan).astype(np.float32)

        X_train = _to_float32(train_df, feature_cols)
        y_train = pd.to_numeric(train_df[target_col], errors="coerce").to_numpy(dtype=np.int32, na_value=0)
        X_test  = _to_float32(test_df, feature_cols)
        y_test  = pd.to_numeric(test_df[target_col], errors="coerce").to_numpy(dtype=np.int32, na_value=0)

        # Fill NaN with train column medians
        col_medians = np.nanmedian(X_train, axis=0)
        col_medians = np.where(np.isnan(col_medians), 0.0, col_medians)
        X_train = np.where(np.isnan(X_train), col_medians, X_train)
        X_test  = np.where(np.isnan(X_test), col_medians, X_test)

        try:
            model = build_stacking_model()
            model.fit(X_train, y_train)
        except Exception as e:
            print(f"    Window {i}: training failed — {e}")
            i += step
            continue

        probs  = model.predict_proba(X_test)[:, 1]

        try:
            window_auc = roc_auc_score(y_test, probs)
        except Exception:
            window_auc = 0.0

        implied = test_df[implied_col].values
        edge    = probs - implied

        # ── Betting simulation ─────────────────────────────────────────────
        bankroll = INITIAL_BK
        wins = losses = 0
        peak = INITIAL_BK
        max_dd = 0.0
        pnl_series = []
        auc_gate_fired = False

        if window_auc < AUC_GATE:
            auc_gate_fired = True
            bet_mask = np.zeros(len(test_df), dtype=bool)
        else:
            bet_mask = (edge >= MIN_EDGE) & (probs >= MIN_PROB)

        for j in np.where(bet_mask)[0]:
            p   = float(probs[j])
            imp = float(implied[j])
            e   = float(edge[j])
            oddsval = 1.0 / imp if imp > 0 else 2.0
            b = oddsval - 1.0

            kelly_raw = (b * p - (1.0 - p)) / b if b > 0 else 0.0
            bet_frac  = min(max(kelly_raw * KELLY_FRAC, 0.0), MAX_BET_FRAC)
            stake     = bankroll * bet_frac

            won = bool(y_test[j] == 1)
            if won:
                bankroll += stake * b
                wins += 1
            else:
                bankroll -= stake
                losses += 1

            if bankroll > peak:
                peak = bankroll
            drawdown = (peak - bankroll) / peak
            if drawdown > max_dd:
                max_dd = drawdown
            pnl_series.append(bankroll)

        total_bets = wins + losses
        win_rate   = wins / total_bets if total_bets > 0 else 0.0
        roi        = (bankroll - INITIAL_BK) / INITIAL_BK
        brier      = brier_score_loss(y_test, probs)

        # Sharpe (daily-like from PnL series)
        if len(pnl_series) > 1:
            returns = np.diff(pnl_series) / np.array(pnl_series[:-1])
            std_r = np.std(returns)
            sharpe = float(np.mean(returns) / std_r * np.sqrt(len(pnl_series))) if std_r > 1e-4 else 0.0
        else:
            sharpe = 0.0

        results.append({
            "run_id":          str(uuid.uuid4())[:8],
            "version":         VERSION,
            "target":          target_col,
            "window_start":    str(train_df["game_date"].iloc[0]),
            "window_end":      str(test_df["game_date"].iloc[-1]),
            "train_games":     len(train_df),
            "test_games":      len(test_df),
            "total_bets":      total_bets,
            "wins":            wins,
            "losses":          losses,
            "win_rate":        round(win_rate, 4),
            "initial_bankroll": INITIAL_BK,
            "final_bankroll":  round(bankroll, 2),
            "total_roi":       round(roi, 4),
            "max_drawdown":    round(max_dd, 4),
            "sharpe_ratio":    round(sharpe, 4),
            "brier_score":     round(brier, 4),
            "auc":             round(window_auc, 4),
            "avg_edge":        round(float(edge[bet_mask].mean()) if bet_mask.any() else 0.0, 4),
            "min_edge_threshold": MIN_EDGE,
            "kelly_fraction":  KELLY_FRAC,
            "auc_gate":        AUC_GATE,
            "min_prob":        MIN_PROB,
            "max_bet_frac":    MAX_BET_FRAC,
            "auc_gate_fired":  int(auc_gate_fired),
        })

        i += step

    return results


def summarise(results: list[dict], target: str):
    if not results:
        print(f"  No results for {target}")
        return

    betting = [r for r in results if r["total_bets"] > 0]
    all_roi  = [r["total_roi"] for r in results]

    print(f"\n  ── {target.upper()} ────────────────────────────────────")
    print(f"  Windows: {len(results)}  |  With bets: {len(betting)}")
    print(f"  Profitable windows: {sum(1 for r in betting if r['total_roi'] > 0)}/{len(betting)}")
    if betting:
        avg_wr  = np.mean([r["win_rate"] for r in betting])
        avg_roi = np.mean([r["total_roi"] for r in betting])
        max_dd  = max(r["max_drawdown"] for r in betting)
        avg_sh  = np.mean([r["sharpe_ratio"] for r in betting])
        print(f"  Avg win rate:   {avg_wr:.1%}")
        print(f"  Avg ROI:        {avg_roi:.1%}")
        print(f"  Max drawdown:   {max_dd:.1%}")
        print(f"  Avg Sharpe:     {avg_sh:.2f}")
        gate_fires = sum(r["auc_gate_fired"] for r in results)
        print(f"  AUC gate fired: {gate_fires}/{len(results)} windows")


def main():
    p = argparse.ArgumentParser(description="WNBA walk-forward backtest")
    p.add_argument("--target",        choices=["moneyline", "totals", "both"],
                   default="both")
    p.add_argument("--train-window",  type=int, default=300)
    p.add_argument("--test-window",   type=int, default=60)
    p.add_argument("--step",          type=int, default=30)
    args = p.parse_args()

    print(f"\n[backtest] DB: {DB_PATH}")
    conn = duckdb.connect(DB_PATH)
    df   = load_game_data(conn)
    conn.close()

    if df.empty:
        print("ERROR: No feature data found. Run data/build_features.py first.")
        sys.exit(1)

    print(f"  {len(df)} game rows   "
          f"({df['season_year'].min()}–{df['season_year'].max()})")

    all_results = []
    targets = []
    if args.target in ("moneyline", "both"):
        targets.append(("moneyline", ML_FEATURE_COLS, "home_win", "impl_home"))
    if args.target in ("totals", "both"):
        # Need implied prob for totals — add it to df
        df["impl_over"] = df.apply(
            lambda r: 1.0 / r["over_odds"] if r.get("over_odds") and r["over_odds"] > 1 else np.nan,
            axis=1
        )
        targets.append(("totals", TOT_FEATURE_COLS, "total_over", "impl_over"))

    for tname, fcols, tcol, icol in targets:
        print(f"\n[{tname}] Running walk-forward "
              f"(train={args.train_window}, test={args.test_window}, step={args.step})...")
        if icol not in df.columns:
            # Add implied prob column from DB odds if possible
            print(f"  WARN: '{icol}' not in features — skipping {tname}")
            continue

        res = run_single_target(
            df, fcols, tcol, icol,
            args.train_window, args.test_window, args.step,
        )
        summarise(res, tname)
        all_results.extend(res)

    if not all_results:
        print("\nNo results to save.")
        return

    # ── Save CSV ───────────────────────────────────────────────────────────────
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"wf_{VERSION}_{ts}.csv"
    fieldnames = list(all_results[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_results)

    print(f"\n[done] Results saved: {path}")


if __name__ == "__main__":
    main()
