#!/usr/bin/env python3
"""
node_nba_engine/scripts/nba_inference_loop.py

24/7 paper trading loop for NBA predictions.
Polls odds → runs model → sizes bets via Rust math engine → executes via C++ layer.

Paper trades are logged to the DuckDB paper_trades table.
"""

import os
import sys
import time
import json
import uuid
import logging
import subprocess
import pathlib
from datetime import datetime

import duckdb
from dotenv import load_dotenv

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
load_dotenv(str(_ROOT / ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("NBA_NODE")

MIN_PROB          = 0.55
AUC_GATE          = 0.58
POLLING_SECS      = 3600   # 1 hour between polls
PAPER_MODE        = os.getenv("PAPER_TRADING_MODE", "TRUE").upper() == "TRUE"
BANKROLL          = float(os.getenv("PAPER_STARTING_BANKROLL", "10000.00"))
DB_PATH           = os.getenv("NBA_DB_PATH", str(_ROOT / "db" / "nba.duckdb"))


def get_rust_bin() -> str:
    rust_dir = _ROOT.parent / "math_engine_rust" / "target" / "release"
    exe = rust_dir / "math_engine_rust.exe"
    elf = rust_dir / "math_engine_rust"
    return str(exe) if exe.exists() else str(elf)


def get_cpp_bin() -> str:
    cpp_dir = _ROOT.parent / "execution_layer_cpp"
    exe = cpp_dir / "execution_bin.exe"
    elf = cpp_dir / "execution_bin"
    return str(exe) if exe.exists() else str(elf)


def log_paper_trade(game_id: str, market: str, pick: str,
                    odds: float, prob: float, edge: float, wager: float):
    """Log a paper trade to DuckDB."""
    try:
        conn = duckdb.connect(DB_PATH)
        conn.execute(
            """
            INSERT INTO paper_trades
                (trade_id, game_id, market, pick, odds, model_prob, edge, wager)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [str(uuid.uuid4()), game_id, market, pick, odds, prob, edge, wager],
        )
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log paper trade: {e}")


def main():
    logger.info("=" * 60)
    logger.info("  🏀 NBA RoadRunner — Polyglot Inference Node")
    logger.info(f"  Mode: {'PAPER' if PAPER_MODE else 'LIVE'}")
    logger.info(f"  Bankroll: ${BANKROLL:,.2f}")
    logger.info("=" * 60)

    from model.stack_train import load_latest_model
    from model.predict import predict

    try:
        ml_meta  = load_latest_model("moneyline")
        tot_meta = load_latest_model("totals")
    except FileNotFoundError as e:
        logger.error(f"Models not found: {e}")
        logger.error("Run: python model/stack_train.py")
        sys.exit(1)

    ml_auc  = ml_meta.get("auc_test", 0.0)
    tot_auc = tot_meta.get("auc_test", 0.0)

    logger.info(f"ML model AUC: {ml_auc:.3f} | TOT model AUC: {tot_auc:.3f}")
    if ml_auc < AUC_GATE and tot_auc < AUC_GATE:
        logger.warning(f"Both models below AUC gate ({AUC_GATE}). Edge will be minimal.")

    rust_bin = get_rust_bin()
    cpp_bin  = get_cpp_bin()
    bankroll = BANKROLL

    while True:
        logger.info("Polling Odds API...")

        try:
            from scripts.odds_client import theodds_get_upcoming
            raw = theodds_get_upcoming()
        except Exception as e:
            logger.error(f"Failed to fetch odds: {e}")
            time.sleep(POLLING_SECS)
            continue

        games = [ev for ev in raw if ev.get("home_ml") and ev.get("away_ml")]

        if not games:
            logger.info("No active lines found. Sleeping.")
        else:
            logger.info(f"Evaluating {len(games)} active lines.")
            for g in games:
                try:
                    r = predict(
                        home_team=g["home"], away_team=g["away"],
                        ml_home=g.get("home_ml"), ml_away=g.get("away_ml"),
                        total_line=g.get("total_line"),
                        over_odds=g.get("over_odds"), under_odds=g.get("under_odds"),
                    )
                except Exception as ex:
                    logger.error(f"Predict error on {g['home']}: {ex}")
                    continue

                candidates = []

                # Moneyline candidates
                if ml_auc >= AUC_GATE:
                    for t, p, odds, market in [
                        (g["home"], r.get("home_win_prob", 0), g.get("home_ml", 0), "ML_HOME"),
                        (g["away"], r.get("away_win_prob", 0), g.get("away_ml", 0), "ML_AWAY"),
                    ]:
                        if p >= MIN_PROB and odds > 1.0:
                            edge = p - (1.0 / odds)
                            candidates.append((f"{t} ML", p, odds, edge, market, g.get("game_id", "")))

                # Totals candidates
                if tot_auc >= AUC_GATE and g.get("total_line"):
                    for d, p, odds, market in [
                        ("Over", r.get("over_prob", 0), g.get("over_odds", 0), "OVER"),
                        ("Under", r.get("under_prob", 0), g.get("under_odds", 0), "UNDER"),
                    ]:
                        if p >= MIN_PROB and odds > 1.0:
                            edge = p - (1.0 / odds)
                            candidates.append((f"{d} {g['total_line']}", p, odds, edge, market, g.get("game_id", "")))

                for target, prob, odds, edge, market, game_id in candidates:
                    # Rust Kelly sizing
                    rust_cmd = [rust_bin, str(prob), str(odds), "0.25", str(bankroll)]
                    try:
                        res = subprocess.run(rust_cmd, capture_output=True, text=True, check=True)
                        rust_json = json.loads(res.stdout.strip())
                        wager = float(rust_json.get("wager_amount", 0.0))
                    except Exception as e:
                        logger.error(f"RUST IPC ERROR: {e}")
                        # Fallback: quarter-Kelly manual calculation
                        kelly_f = max(0, (prob * odds - 1) / (odds - 1)) * 0.25
                        wager = round(kelly_f * bankroll, 2)

                    if wager > 0.0:
                        logger.info(f"🎯 {target} | prob={prob:.1%} edge={edge:+.1%} "
                                    f"odds={odds:.2f} wager=${wager:.2f}")

                        # Log paper trade
                        log_paper_trade(game_id, market, target, odds, prob, edge, wager)

                        # C++ execution layer
                        cpp_cmd = [cpp_bin, target, str(wager), str(odds)]
                        try:
                            cpp_res = subprocess.run(cpp_cmd, capture_output=True, text=True, check=True)
                            for line in cpp_res.stdout.strip().split("\n"):
                                logger.info(f"  C++ | {line}")
                        except Exception as e:
                            logger.debug(f"C++ exec layer not available: {e}")

        logger.info(f"Sleeping {POLLING_SECS}s...")
        time.sleep(POLLING_SECS)


if __name__ == "__main__":
    main()
