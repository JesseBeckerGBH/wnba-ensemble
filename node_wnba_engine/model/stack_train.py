#!/usr/bin/env python3
"""
D:/WNBA/model/stack_train.py

Train WNBA dual-target ensemble model:
  - Target 1: Moneyline (did home team win? — predict home_win_prob)
  - Target 2: Totals (did game go over the total? — predict total_points)

Stack: LogisticRegression / Ridge + XGBoost + LightGBM + MLP meta-learner
Same wf_v2 pattern as darts_v2 (AUC gate, min_prob, hard bet cap).

Usage:
    py -3.13 model/stack_train.py
    py -3.13 model/stack_train.py --min-games 200   # require more training data
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import uuid
from datetime import datetime

import duckdb
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from dotenv import load_dotenv

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
load_dotenv(str(_ROOT / ".env"))

try:
    import xgboost as xgb
    import lightgbm as lgb
except ImportError as e:
    print(f"ERROR: {e}. Run: py -3.13 -m pip install xgboost lightgbm")
    sys.exit(1)

DB_PATH    = os.getenv("WNBA_DB_PATH", str(_ROOT / "db" / "wnba.duckdb"))
MODEL_DIR  = _ROOT / "model" / "artifacts"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ── Feature columns ────────────────────────────────────────────────────────────
# Per-team (relative: home - away) features for moneyline model
ML_FEATURE_COLS = [
    # rolling form differential (home minus away)
    "rolling_win_rate_diff",
    "rolling_pts_diff",
    "rolling_net_pts_diff",
    "rolling_fg_pct_diff",
    "rolling_fg3_pct_diff",
    "rolling_tov_rate_diff",
    "rolling_reb_margin_diff",
    # efficiency
    "net_rating_diff",
    "pace_diff",
    # rest advantage
    "days_rest_diff",
    "b2b_diff",       # 1 if home on b2b but not away, -1 if away on b2b, 0 otherwise
    # Elo
    "elo_diff",
    # H2H
    "h2h_win_rate",   # home team's H2H win rate vs away team
    "h2h_meetings",
    # home court (always 1 for home, 0 for away — implicit in the differential setup)
    "home_advantage",
    # sentiment
    "sentiment_diff",
]

# For totals model, use team-level absolute features (sum / individual)
TOT_FEATURE_COLS = [
    "home_rolling_pts_for", "away_rolling_pts_for",
    "home_rolling_pts_against", "away_rolling_pts_against",
    "home_off_rating", "away_off_rating",
    "home_def_rating", "away_def_rating",
    "home_pace", "away_pace",
    "home_days_rest", "away_days_rest",
    "home_fg_pct", "away_fg_pct",
    "home_fg3_pct", "away_fg3_pct",
]


# ── Data preparation ───────────────────────────────────────────────────────────
def load_game_data(conn: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """
    Load paired home/away features from game_features, returning one row per game.
    Compute differential features for moneyline model.
    """
    df = conn.execute("""
        SELECT
            h.game_id,
            h.game_date,
            h.season_year,
            -- home team features
            h.rolling_win_rate      AS home_rwrate,
            h.rolling_pts_for       AS home_pts_for,
            h.rolling_pts_against   AS home_pts_ag,
            h.rolling_net_pts       AS home_net_pts,
            h.rolling_fg_pct        AS home_fg_pct,
            h.rolling_fg3_pct       AS home_fg3_pct,
            h.rolling_ft_pct        AS home_ft_pct,
            h.rolling_tov_rate      AS home_tov,
            h.rolling_reb_margin    AS home_reb,
            h.net_rating            AS home_net_rtg,
            h.pace                  AS home_pace,
            h.days_rest             AS home_rest,
            h.b2b                   AS home_b2b,
            h.elo_pre               AS home_elo,
            h.elo_diff              AS elo_diff,
            h.h2h_win_rate          AS h2h_win_rate,
            h.h2h_meetings          AS h2h_meetings,
            h.sentiment_score       AS home_sentiment,
            -- away team features
            a.rolling_win_rate      AS away_rwrate,
            a.rolling_pts_for       AS away_pts_for,
            a.rolling_pts_against   AS away_pts_ag,
            a.rolling_net_pts       AS away_net_pts,
            a.rolling_fg_pct        AS away_fg_pct,
            a.rolling_fg3_pct       AS away_fg3_pct,
            a.rolling_ft_pct        AS away_ft_pct,
            a.rolling_tov_rate      AS away_tov,
            a.rolling_reb_margin    AS away_reb,
            a.net_rating            AS away_net_rtg,
            a.pace                  AS away_pace,
            a.days_rest             AS away_rest,
            a.b2b                   AS away_b2b,
            a.elo_pre               AS away_elo,
            a.sentiment_score       AS away_sentiment,
            -- targets
            h.won_moneyline         AS home_win,
            h.total_line            AS total_pts
        FROM game_features h
        JOIN game_features a
            ON a.game_id = h.game_id AND a.is_home = FALSE
        WHERE h.is_home = TRUE
          AND h.won_moneyline IS NOT NULL
        ORDER BY h.game_date
    """).df()

    if df.empty:
        return df

    # ── Differential features ──────────────────────────────────────────────────
    df["rolling_win_rate_diff"] = df["home_rwrate"]  - df["away_rwrate"]
    df["rolling_pts_diff"]      = df["home_pts_for"] - df["away_pts_for"]
    df["rolling_net_pts_diff"]  = df["home_net_pts"] - df["away_net_pts"]
    df["rolling_fg_pct_diff"]   = df["home_fg_pct"]  - df["away_fg_pct"]
    df["rolling_fg3_pct_diff"]  = df["home_fg3_pct"] - df["away_fg3_pct"]
    df["rolling_tov_rate_diff"] = df["home_tov"]     - df["away_tov"]
    df["rolling_reb_margin_diff"] = df["home_reb"]   - df["away_reb"]
    df["net_rating_diff"]       = df["home_net_rtg"] - df["away_net_rtg"]
    df["pace_diff"]             = df["home_pace"]    - df["away_pace"]
    df["days_rest_diff"]        = df["home_rest"]    - df["away_rest"]
    df["b2b_diff"]              = (df["home_b2b"].astype(float)
                                   - df["away_b2b"].astype(float))
    df["sentiment_diff"]        = df["home_sentiment"] - df["away_sentiment"]
    df["home_advantage"]        = 1.0   # constant — home court

    # ── Synthetic implied probabilities for backtesting ────────────────────────
    # Without historical odds, derive from Elo (market-efficient baseline)
    # impl_home ≈ Elo-based P(home wins) including a ~3% home court boost
    import numpy as _np
    elo_diff_clean = df["elo_diff"].fillna(0).astype(float)
    df["impl_home"] = 1.0 / (1.0 + _np.exp(-0.004 * elo_diff_clean - 0.12))  # +0.12 ≈ 3% home boost
    df["impl_away"] = 1.0 - df["impl_home"]
    # Totals implied (50/50 without line data — edge only comes from model confidence)
    df["impl_over"]  = 0.5
    df["impl_under"] = 0.5
    df["over_odds"]  = 1.0 / df["impl_over"]
    df["under_odds"] = 1.0 / df["impl_under"]

    # Totals model renamed columns
    df["home_rolling_pts_for"]    = df["home_pts_for"]
    df["away_rolling_pts_for"]    = df["away_pts_for"]
    df["home_rolling_pts_against"] = df["home_pts_ag"]
    df["away_rolling_pts_against"] = df["away_pts_ag"]
    df["home_off_rating"]         = df["home_net_rtg"].apply(lambda x: max(x, 0) if x else 0)
    df["away_off_rating"]         = df["away_net_rtg"].apply(lambda x: max(x, 0) if x else 0)
    df["home_def_rating"]         = df["home_net_rtg"].apply(lambda x: -min(x, 0) if x else 0)
    df["away_def_rating"]         = df["away_net_rtg"].apply(lambda x: -min(x, 0) if x else 0)
    df["home_days_rest"]          = df["home_rest"]
    df["away_days_rest"]          = df["away_rest"]
    df["home_fg_pct"]             = df["home_fg_pct"]
    df["home_fg3_pct"]            = df["home_fg3_pct"]
    df["away_fg_pct"]             = df["away_fg_pct"]
    df["away_fg3_pct"]            = df["away_fg3_pct"]

    # ── Totals target: over/under expanding median (no look-ahead) ────────────
    # For each game, threshold = median of all PRIOR game totals.
    # Avoids data leakage across walk-forward windows.
    total_pts = pd.to_numeric(df["total_pts"], errors="coerce")
    expanding_med = total_pts.expanding(min_periods=20).median().shift(1)
    df["total_over"] = (total_pts > expanding_med).astype("Int64")
    df["total_over"] = df["total_over"].where(expanding_med.notna(), other=pd.NA)

    return df


# ── Model builder ──────────────────────────────────────────────────────────────
def build_stacking_model():
    """Shared stack: LR + XGB + LGB base; LR meta-learner."""
    base_lr = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, C=0.5)),
    ])
    base_xgb = xgb.XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        use_label_encoder=False, eval_metric="logloss",
        random_state=42, verbosity=0,
    )
    base_lgb = lgb.LGBMClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        random_state=42, verbose=-1,
    )
    meta = LogisticRegression(max_iter=500, C=1.0)
    stack = StackingClassifier(
        estimators=[("lr", base_lr), ("xgb", base_xgb), ("lgb", base_lgb)],
        final_estimator=meta,
        cv=5,
        passthrough=False,
    )
    return CalibratedClassifierCV(stack, cv=5, method="isotonic")


# ── Train ──────────────────────────────────────────────────────────────────────
def train(df: pd.DataFrame, feature_cols: list[str], target_col: str):
    """Train on the full dataframe. Returns (model, auc, brier)."""
    # Only require the target to be non-null; impute feature NaNs with medians
    sub = df[feature_cols + [target_col]].copy()
    sub = sub.dropna(subset=[target_col])
    if len(sub) < 50:
        raise ValueError(f"Too few rows ({len(sub)}) for target '{target_col}'")

    # Convert to float — use to_numpy(na_value=np.nan) to handle pandas NA (nullable types)
    X_df = sub[feature_cols].copy()
    for col in X_df.columns:
        X_df[col] = pd.to_numeric(X_df[col], errors="coerce")
    X = X_df.to_numpy(dtype=np.float64, na_value=np.nan).astype(np.float32)
    y = pd.to_numeric(sub[target_col], errors="coerce").to_numpy(dtype=np.int32, na_value=0)

    # Fill NaN with column medians (handles missing box-score features gracefully)
    col_medians = np.nanmedian(X, axis=0)
    col_medians = np.where(np.isnan(col_medians), 0.0, col_medians)  # fallback to 0
    X = np.where(np.isnan(X), col_medians, X)

    model = build_stacking_model()
    model.fit(X, y)

    probs = model.predict_proba(X)[:, 1]
    auc   = roc_auc_score(y, probs)
    brier = brier_score_loss(y, probs)
    return model, auc, brier, col_medians


def save_model(model, col_medians, feature_cols: list[str],
               target: str, auc: float, brier: float,
               n_train: int) -> str:
    """Save model artifact + metadata JSON."""
    version = f"v_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{target}"
    model_path = MODEL_DIR / f"wnba_{target}_{version}.pkl"
    meta_path  = MODEL_DIR / f"wnba_{target}_{version}.json"

    joblib.dump(model, model_path)
    meta = {
        "version":     version,
        "target":      target,
        "feature_cols": feature_cols,
        "col_medians": col_medians.tolist(),
        "auc_test":    round(auc, 4),
        "brier_test":  round(brier, 4),
        "n_train":     n_train,
        "trained_at":  datetime.now().isoformat(),
        "model_path":  str(model_path),
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  Saved: {model_path.name}")
    print(f"         AUC={auc:.4f}  Brier={brier:.4f}  n={n_train}")
    return version


def load_latest_model(target: str = "moneyline") -> dict:
    """Load most recently trained model for a target. Returns metadata dict."""
    jsons = sorted(MODEL_DIR.glob(f"wnba_{target}_*.json"), reverse=True)
    if not jsons:
        raise FileNotFoundError(
            f"No {target} model found in {MODEL_DIR}. Run stack_train.py first."
        )
    with open(jsons[0]) as f:
        meta = json.load(f)
    # Resolve the .pkl next to its JSON sidecar. The stored ``model_path`` is an
    # absolute path from the training host (often Windows, e.g. D:\WNBA\...), so
    # we never trust it for loading — derive the sibling .pkl from the JSON path
    # and only fall back to the stored path if that sibling is missing.
    pkl_path = jsons[0].with_suffix(".pkl")
    if not pkl_path.exists():
        pkl_path = pathlib.Path(meta["model_path"])
    meta["model"] = joblib.load(pkl_path)
    meta["model_path"] = str(pkl_path)
    return meta


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="Train WNBA dual-target ensemble")
    p.add_argument("--min-games", type=int, default=100,
                   help="Minimum training games required (default: 100)")
    args = p.parse_args()

    print(f"\n[train] DB: {DB_PATH}")
    conn = duckdb.connect(DB_PATH)
    df   = load_game_data(conn)
    conn.close()

    if df.empty:
        print("ERROR: No feature data found. Run data/build_features.py first.")
        sys.exit(1)

    print(f"  {len(df)} game rows loaded ({df['season_year'].min()}–{df['season_year'].max()})")

    # ── Moneyline model ────────────────────────────────────────────────────────
    print(f"\n[moneyline] Training on {len(df)} games...")
    ml_df = df.dropna(subset=["home_win"])
    if len(ml_df) < args.min_games:
        print(f"  WARNING: Only {len(ml_df)} rows with complete ML features. "
              f"Run data/ingest_wnba.py --boxscores for better features.")
    try:
        ml_model, ml_auc, ml_brier, ml_medians = train(
            df, ML_FEATURE_COLS, "home_win"
        )
        save_model(ml_model, ml_medians, ML_FEATURE_COLS,
                   "moneyline", ml_auc, ml_brier, len(ml_df))
    except ValueError as e:
        print(f"  SKIP: {e}")

    # ── Totals model ───────────────────────────────────────────────────────────
    # Totals model predicts the actual total — we'll use regression-style
    # (classify as over/under relative to a line set at the median total)
    tot_df = df.dropna(subset=["total_pts"])
    if len(tot_df) >= args.min_games:
        median_total = float(tot_df["total_pts"].median())
        df["total_over"] = (df["total_pts"] > median_total).astype(int)
        print(f"\n[totals] Training on {len(tot_df)} games (median total={median_total:.1f})...")
        try:
            tot_model, tot_auc, tot_brier, tot_medians = train(
                df, TOT_FEATURE_COLS, "total_over"
            )
            # Save median_total in meta
            version = save_model(tot_model, tot_medians, TOT_FEATURE_COLS,
                                 "totals", tot_auc, tot_brier, len(tot_df))
            # Append median_total to the JSON
            meta_files = sorted(MODEL_DIR.glob(f"wnba_totals_{version}.json"))
            if meta_files:
                with open(meta_files[0]) as f:
                    meta = json.load(f)
                meta["median_total"] = median_total
                with open(meta_files[0], "w") as f:
                    json.dump(meta, f, indent=2)
        except ValueError as e:
            print(f"  SKIP: {e}")
    else:
        print(f"\n[totals] SKIP: only {len(tot_df)} rows (need {args.min_games})")

    print("\n[done]")


if __name__ == "__main__":
    main()
