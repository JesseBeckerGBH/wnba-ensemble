import os
import sys
import json
import logging
import time
from dataclasses import dataclass
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s | INFERENCE | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

PIPE_PATH = "/tmp/darts_cv_telemetry.pipe"
RUST_BIN_PATH = "/app/node_darts_cv_engine/math_engine_rust/target/release/math_engine"

# Import the Real ML Ensemble
sys.path.insert(0, '/app/node_darts_cv_engine/darts_ml')
from src.models.ensemble_builder import EnsembleBuilder
import pandas as pd

class LiveDartsPredictor:
    def __init__(self, model_path="/app/node_darts_cv_engine/darts_ml/models/ensemble"):
        logger.info(f"Loading heavy ML models from {model_path}...")
        try:
            self.ensemble = EnsembleBuilder.load(model_path)
            logger.info("Ensemble successfully loaded.")
        except Exception as e:
            logger.warning(f"Could not load ML models (might not be trained yet): {e}")
            self.ensemble = None

    def predict_live_state(self, score_a, score_b, momentum_shift):
        if not self.ensemble:
            return 0.50 # Fallback
            
        # Structure the live DataFrame exactly as the XGBoost/NN expects
        df = pd.DataFrame([{
            'score_diff': score_a - score_b,
            'momentum': 1 if momentum_shift == "PLAYER_A_POINT" else (-1 if momentum_shift == "PLAYER_B_POINT" else 0),
            'total_legs': score_a + score_b
        }])
        
        # Heavy ML Inference
        probabilities = self.ensemble.predict_proba(df)
        win_prob_a = probabilities[0] if len(probabilities) > 0 else 0.50
        return float(min(win_prob_a, 0.99))

def get_current_lagging_odds(player_a, player_b):
    # This simulates our REST API polling of lagging sportsbooks
    # It takes 500ms to poll in real life, but the CV already knows the score
    return 1.95, 1.95

def call_rust_kelly_engine(win_prob, odds_a, bankroll=10000.0):
    try:
        # IPC call to compiled Rust math engine
        cmd = [
            RUST_BIN_PATH,
            "--prob", str(win_prob),
            "--odds", str(odds_a),
            "--bankroll", str(bankroll)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Assuming Rust prints a JSON output: {"optimal_wager": 250.0, "is_safe": true}
        output = json.loads(result.stdout)
        return output.get("optimal_wager", 0.0)
    except Exception as e:
        logger.error(f"Rust bridging failed: {e}")
        return 0.0

def call_cpp_execution_layer(amount):
    try:
        # Execute C++ local ledger for shadow-trading
        cmd = [
            "/app/node_darts_cv_engine/execution_layer_cpp/execution_bin",
            "--amount", str(amount)
        ]
        subprocess.run(cmd, capture_output=False, check=True)
        logger.info(f"C++ Execution boundary confirmed wager: ${amount:.2f}")
    except Exception as e:
        logger.error(f"C++ execution dropped: {e}")

def main_loop():
    logger.info("Initializing LiteSpeed Inference Brain...")
    if not os.path.exists(PIPE_PATH):
        os.mkfifo(PIPE_PATH)
        
    ensemble = LiveDartsPredictor()
    
    logger.info(f"Listening on Telemetry Pipe: {PIPE_PATH}")
    while True:
        with open(PIPE_PATH, 'r') as pipe:
            for line in pipe:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    score_a = data.get("player_a_score", 0)
                    score_b = data.get("player_b_score", 0)
                    momentum = data.get("momentum_shift", "NONE")
                    
                    # 1. LIVE ML INFERENCE
                    win_prob_a = ensemble.predict_live_state(score_a, score_b, momentum)
                    
                    # 2. FETCH LAGGING ODDS (API Call)
                    odds_a, odds_b = get_current_lagging_odds("PlayerA", "PlayerB")
                    
                    logger.info(f"Relativistic Shift Detected: Win Prob {win_prob_a:.1%} | Lagging Odds: {odds_a}")
                    
                    # 3. RUST MATH (Calculates Edge and Kelly Size)
                    wager = call_rust_kelly_engine(win_prob_a, odds_a)
                    
                    # 4. C++ EXECUTE
                    if wager > 0:
                        logger.info(f"EDGE DETECTED! Deploying {wager} via C++...")
                        call_cpp_execution_layer(wager)
                        
                except Exception as e:
                    logger.error(f"Inference error: {e}")

if __name__ == "__main__":
    main_loop()
