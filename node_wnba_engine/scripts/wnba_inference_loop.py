#!/usr/bin/env python3
import os
import sys
import time
import json
import logging
import subprocess
import pathlib
from datetime import datetime
from dotenv import load_dotenv

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
load_dotenv(str(_ROOT / ".env"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("WNBA_NODE")

MIN_PROB = 0.55
AUC_GATE = 0.58
POOLING_INTERVAL_SECS = 3600 # 1 hour to save API hits
BANKROLL = 1000.00

def get_rust_bin() -> str:
    rust_dir = _ROOT.parent / 'math_engine_rust' / 'target' / 'release'
    exe = rust_dir / 'math_engine_rust.exe'
    elf = rust_dir / 'math_engine_rust'
    return str(exe) if exe.exists() else str(elf)

def get_cpp_bin() -> str:
    cpp_dir = _ROOT.parent / 'execution_layer_cpp'
    exe = cpp_dir / 'execution_bin.exe'
    elf = cpp_dir / 'execution_bin'
    return str(exe) if exe.exists() else str(elf)

def main():
    logger.info("Starting WNBA Polyglot Inference Node [24/7 PROXMOX LOOP]")
    
    from model.stack_train import load_latest_model
    from model.predict import predict
    
    try:
        ml_meta  = load_latest_model("moneyline")
        tot_meta = load_latest_model("totals")
    except FileNotFoundError as e:
        logger.error(f"Models not found: {e}")
        sys.exit(1)
        
    ml_auc  = ml_meta.get("auc_test", 0.0)
    tot_auc = tot_meta.get("auc_test", 0.0)
    
    logger.info(f"Loaded ML: AUC={ml_auc:.3f} | TOT: AUC={tot_auc:.3f}")
    if ml_auc < AUC_GATE and tot_auc < AUC_GATE:
        logger.warning(f"Both models below AUC Gate ({AUC_GATE}). Edge will be minimal.")

    rust_bin = get_rust_bin()
    cpp_bin = get_cpp_bin()
    
    while True:
        logger.info(f"Polling Odds API...")
        
        try:
            from scripts.odds_client import theodds_get_upcoming
            raw = theodds_get_upcoming()
        except Exception as e:
            logger.error(f"Failed to fetch odds: {e}")
            time.sleep(POOLING_INTERVAL_SECS)
            continue
            
        games = []
        for ev in raw:
            if ev.get("home_ml") and ev.get("away_ml"):
                games.append(ev)
                
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
                        over_odds=g.get("over_odds"), under_odds=g.get("under_odds")
                    )
                except Exception as ex:
                    logger.error(f"Predict error on {g['home']}: {ex}")
                    continue

                candidates = []
                
                # Moneyline
                if ml_auc >= AUC_GATE:
                    for t, p, odds in [(g["home"], r.get("home_win_prob", 0), g.get("home_ml", 0)),
                                       (g["away"], r.get("away_win_prob", 0), g.get("away_ml", 0))]:
                        if p >= MIN_PROB and odds > 1.0:
                            candidates.append((f"{t} ML", p, odds))
                
                # Totals
                if tot_auc >= AUC_GATE and g.get("total_line"):
                    for d, p, odds in [("Over", r.get("over_prob", 0), g.get("over_odds", 0)),
                                       ("Under", r.get("under_prob", 0), g.get("under_odds", 0))]:
                        if p >= MIN_PROB and odds > 1.0:
                            candidates.append((f"{d} {g['total_line']}", p, odds))
                            
                for target, prob, odds in candidates:
                    # RUST MATH ENGINE INVOCATION
                    rust_cmd = [rust_bin, str(prob), str(odds), "0.25", str(BANKROLL)]
                    try:
                        res = subprocess.run(rust_cmd, capture_output=True, text=True, check=True)
                        rust_json = json.loads(res.stdout.strip())
                        wager = float(rust_json.get("wager_amount", 0.0))
                    except Exception as e:
                        logger.error(f"RUST IPC ERROR: {e}")
                        continue
                        
                    if wager > 0.0:
                        # C++ EXECUTION LAYER INVOCATION 
                        cpp_cmd = [cpp_bin, target, str(wager), str(odds)]
                        try:
                            cpp_res = subprocess.run(cpp_cmd, capture_output=True, text=True, check=True)
                            logger.info(f"--- C++ SHADOW LAYER ---")
                            for line in cpp_res.stdout.strip().split("\n"):
                                logger.info(f"   {line}")
                        except Exception as e:
                            logger.error(f"C++ EXEC ERROR: {e}")

        logger.info(f"Loop completed. Sleeping for {POOLING_INTERVAL_SECS} seconds.")
        time.sleep(POOLING_INTERVAL_SECS)

if __name__ == "__main__":
    main()
