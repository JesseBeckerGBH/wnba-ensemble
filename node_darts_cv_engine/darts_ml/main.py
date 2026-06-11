"""
Main pipeline for darts betting ensemble.

Orchestrates: Data loading → Feature engineering → Training → Evaluation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.sample_data_generator import SampleDataGenerator
from src.data.etl_pipeline import ETLPipeline
from src.models.ensemble_builder import EnsembleBuilder
from src.utils.config import get_config
from src.utils.logger import setup_logger, get_logger

import pandas as pd
import numpy as np
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score


def main():
    """Run end-to-end pipeline."""
    
    # Setup logging
    setup_logger(log_level="INFO", log_file="logs/main.log")
    logger = get_logger(__name__)
    
    logger.info("="*80)
    logger.info("DARTS BETTING ENSEMBLE - MAIN PIPELINE")
    logger.info("="*80)
    
    # Load configuration
    config = get_config()
    
    # Step 1: Generate sample data (for testing)
    logger.info("\n[Step 1/5] Generating sample data...")
    data_generator = SampleDataGenerator(random_seed=config.random_seed)
    sample_data_path = config.data_raw_path / "sample_matches.csv"
    
    if not sample_data_path.exists():
        data_generator.save_sample_data(str(sample_data_path), num_matches=2000)
    else:
        logger.info(f"Sample data already exists at {sample_data_path}")
    
    # Step 2: Run ETL pipeline
    logger.info("\n[Step 2/5] Running ETL pipeline...")
    etl = ETLPipeline()
    
    try:
        features_df = etl.run_full_pipeline(force_reload=False)
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}")
        return
    
    # Get data summary
    summary = etl.get_data_summary(features_df)
    logger.info("\nDataset Summary:")
    logger.info(f"  Total matches: {summary['total_matches']}")
    logger.info(f"  Date range: {summary['date_range'][0]} to {summary['date_range'][1]}")
    logger.info(f"  Number of features: {summary['num_features']}")
    logger.info(f"  Unique players: {summary['unique_players']}")
    logger.info(f"  Class balance: {summary['class_balance']}")
    
    # Step 3: Train/test split
    logger.info("\n[Step 3/5] Splitting data...")
    train_df, test_df = etl.get_train_test_split(features_df, test_size=0.2, temporal_split=True)
    
    logger.info(f"  Train set: {len(train_df)} samples")
    logger.info(f"  Test set: {len(test_df)} samples")
    
    # Prepare model inputs
    X_train, y_train = etl.prepare_model_inputs(train_df, include_target=True)
    X_test, y_test = etl.prepare_model_inputs(test_df, include_target=True)
    
    # Create validation set from training data (last 20%)
    val_split = int(len(X_train) * 0.8)
    X_val = X_train.iloc[val_split:]
    y_val = y_train.iloc[val_split:]
    X_train = X_train.iloc[:val_split]
    y_train = y_train.iloc[:val_split]
    
    logger.info(f"  Validation set: {len(X_val)} samples")
    
    # Step 4: Train ensemble
    logger.info("\n[Step 4/5] Training ensemble...")
    ensemble = EnsembleBuilder(config)
    
    try:
        ensemble.fit(X_train, y_train, X_val, y_val)
    except Exception as e:
        logger.error(f"Ensemble training failed: {e}")
        return
    
    # Update weights based on validation performance
    logger.info("\nUpdating ensemble weights...")
    ensemble.update_weights(X_val, y_val, method='performance_based')
    
    # Step 5: Evaluate on test set
    logger.info("\n[Step 5/5] Evaluating on test set...")
    
    # Get predictions
    predictions = ensemble.predict_proba(X_test, return_individual=True)
    ensemble_pred = predictions['ensemble']
    
    # Calculate metrics
    brier = brier_score_loss(y_test, ensemble_pred)
    logloss = log_loss(y_test, ensemble_pred)
    auc = roc_auc_score(y_test, ensemble_pred)
    
    logger.info("\n" + "="*80)
    logger.info("ENSEMBLE PERFORMANCE ON TEST SET")
    logger.info("="*80)
    logger.info(f"Brier Score:    {brier:.4f} (lower is better, target < 0.25)")
    logger.info(f"Log Loss:       {logloss:.4f} (lower is better, target < 0.60)")
    logger.info(f"ROC-AUC:        {auc:.4f} (higher is better, target > 0.65)")
    
    # Individual model performance
    logger.info("\nIndividual Model Performance:")
    for model_name in ['xgboost', 'lightgbm', 'neural_network', 'bayesian_ridge']:
        pred = predictions[model_name]
        model_brier = brier_score_loss(y_test, pred)
        model_logloss = log_loss(y_test, pred)
        model_auc = roc_auc_score(y_test, pred)
        
        logger.info(f"\n  {model_name.upper()}:")
        logger.info(f"    Brier Score: {model_brier:.4f}")
        logger.info(f"    Log Loss:    {model_logloss:.4f}")
        logger.info(f"    ROC-AUC:     {model_auc:.4f}")
    
    # Feature importance
    logger.info("\n" + "="*80)
    logger.info("TOP 10 MOST IMPORTANT FEATURES")
    logger.info("="*80)
    
    feature_names = list(X_train.columns)
    importance_df = ensemble.get_feature_importance(feature_names, top_n=10)
    
    if not importance_df.empty:
        for idx, row in importance_df.iterrows():
            logger.info(f"  {row['feature']:30s} {row['importance']:.4f}")
    
    # Save ensemble
    logger.info("\n" + "="*80)
    logger.info("SAVING ENSEMBLE")
    logger.info("="*80)
    
    models_path = config.models_path
    ensemble.save(str(models_path / "ensemble"))
    logger.info(f"Ensemble saved to {models_path / 'ensemble'}")
    
    logger.info("\n" + "="*80)
    logger.info("PIPELINE COMPLETE!")
    logger.info("="*80)
    logger.info(f"\nEnsemble weights: {ensemble}")
    logger.info(f"\nNext steps:")
    logger.info(f"  1. Review results in logs/main.log")
    logger.info(f"  2. Run backtesting: python cli.py backtest")
    logger.info(f"  3. Make predictions: python cli.py predict --player1 'Player A' --player2 'Player B'")


if __name__ == "__main__":
    main()
