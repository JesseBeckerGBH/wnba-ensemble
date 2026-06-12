import os
import sys

# Ensure imports work when run directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_prep import load_and_prep_data
from models import ModelEnsemble
from bayesian import BayesianPriors

def run_pipeline():
    print("==============================================")
    print("   WNBA Ensemble Betting Pipeline (DOE Stack) ")
    print("==============================================\n")
    
    # 1. Load Data (Mock or Real)
    df, features = load_and_prep_data()
    print(f"\n[Data Prep] Processed {len(df)} games using {len(features)} engineered features.")
    
    if len(features) == 0:
        print("Error: No valid features generated. Exiting.")
        return

    # 2. Ensemble Modeling
    ensemble = ModelEnsemble()
    
    print("\n[Models] Training Stacking Classifier (Moneyline)...")
    ml_acc = ensemble.train_moneyline(df, features)
    
    print("\n[Models] Training Regressor (Spread)...")
    spread_mae = ensemble.train_spread(df, features)
    
    print("\n[Models] Running Markov Chains (Totals)...")
    ou_prob = ensemble.simulate_over_under(n_sims=5000, target_total=160.5)

    # 3. Bayesian Priors
    print("\n[Bayesian] Computing Priors via PyMC...")
    bayes = BayesianPriors()
    # Sample subset of features for speed during pipeline testing
    top_3_features = features[:3] 
    priors = bayes.extract_priors(df, top_3_features)
    
    print("\n==============================================")
    print("               PIPELINE COMPLETE              ")
    print("==============================================")
    print(f"Moneyline Base Accuracy:   {ml_acc:.2%}")
    print(f"Spread Average Error:      {spread_mae:.1f} pts")
    if priors:
        print(f"Calculated Home Adv Prior: {priors['home_adv_prior']:.3f}")

if __name__ == "__main__":
    run_pipeline()
