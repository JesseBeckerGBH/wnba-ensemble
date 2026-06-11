"""
ETL pipeline for darts betting ensemble.

Orchestrates data loading, feature engineering, and data preparation.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Tuple
from loguru import logger

from .darts_data_loader import DartsDataLoader
from .feature_engineering import FeatureEngineer
from ..utils.config import get_config


class ETLPipeline:
    """End-to-end ETL pipeline for darts match data."""
    
    def __init__(self):
        """Initialize ETL pipeline."""
        self.config = get_config()
        self.data_loader = DartsDataLoader()
        self.feature_engineer = FeatureEngineer()
        
        self.processed_path = self.config.data_processed_path
        self.processed_path.mkdir(parents=True, exist_ok=True)
    
    def run_full_pipeline(
        self,
        force_reload: bool = False,
        scrape_new_data: bool = False
    ) -> pd.DataFrame:
        """
        Run complete ETL pipeline.
        
        Args:
            force_reload: Force reload even if processed data exists
            scrape_new_data: Scrape new data from web sources
            
        Returns:
            DataFrame with engineered features
        """
        logger.info("Starting ETL pipeline")
        
        # Check if processed data already exists
        processed_file = self.processed_path / "features.parquet"
        
        if processed_file.exists() and not force_reload:
            logger.info(f"Loading existing processed data from {processed_file}")
            return pd.read_parquet(processed_file)
        
        # Step 1: Load raw data
        if scrape_new_data:
            logger.info("Scraping new data from web sources")
            # Scrape PDC data
            pdc_df = self.data_loader.scrape_pdc_results(
                start_year=2020,
                end_year=None,
                max_pages=50
            )
        
        # Load all available data
        raw_df = self.data_loader.load_all_sources()
        
        if raw_df.empty:
            logger.error("No data loaded - cannot proceed with ETL")
            raise ValueError("No data available for processing")
        
        # Step 2: Engineer features
        logger.info("Engineering features")
        features_df = self.feature_engineer.engineer_features(raw_df, include_target=True)
        
        if features_df.empty:
            logger.error("Feature engineering produced no results")
            raise ValueError("Feature engineering failed")
        
        # Step 3: Save processed data
        logger.info(f"Saving processed features to {processed_file}")
        features_df.to_parquet(processed_file, index=False)
        
        # Also save as CSV for inspection
        csv_file = self.processed_path / "features.csv"
        features_df.to_csv(csv_file, index=False)
        logger.info(f"Also saved as CSV: {csv_file}")
        
        logger.info(f"ETL pipeline complete: {len(features_df)} samples with {len(features_df.columns)} features")
        
        return features_df
    
    def get_train_test_split(
        self,
        features_df: Optional[pd.DataFrame] = None,
        test_size: float = 0.2,
        temporal_split: bool = True
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data into train and test sets.
        
        Args:
            features_df: Features DataFrame (loads from disk if None)
            test_size: Fraction of data for testing
            temporal_split: If True, use temporal split (last X% of data)
                          If False, use random split
            
        Returns:
            Tuple of (train_df, test_df)
        """
        if features_df is None:
            processed_file = self.processed_path / "features.parquet"
            if not processed_file.exists():
                raise FileNotFoundError(f"No processed data found at {processed_file}")
            features_df = pd.read_parquet(processed_file)
        
        if temporal_split:
            # Temporal split: train on older data, test on recent data
            features_df = features_df.sort_values('date')
            split_idx = int(len(features_df) * (1 - test_size))
            
            train_df = features_df.iloc[:split_idx].copy()
            test_df = features_df.iloc[split_idx:].copy()
            
            logger.info(f"Temporal split: Train={len(train_df)} (up to {train_df['date'].max()}), "
                       f"Test={len(test_df)} (from {test_df['date'].min()})")
        else:
            # Random split (not recommended for time series)
            from sklearn.model_selection import train_test_split
            train_df, test_df = train_test_split(
                features_df,
                test_size=test_size,
                random_state=self.config.random_seed
            )
            logger.info(f"Random split: Train={len(train_df)}, Test={len(test_df)}")
        
        return train_df, test_df
    
    def prepare_model_inputs(
        self,
        df: pd.DataFrame,
        include_target: bool = True
    ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """
        Prepare features and target for model training.
        
        Args:
            df: Features DataFrame
            include_target: Whether to return target variable
            
        Returns:
            Tuple of (X, y) where X is features and y is target
            If include_target=False, returns (X, None)
        """
        # Get feature columns (exclude metadata)
        feature_cols = self.feature_engineer.get_feature_names()
        
        # Filter to only existing columns
        available_features = [col for col in feature_cols if col in df.columns]
        
        X = df[available_features].copy()
        
        # Handle missing values (fill with 0 or median)
        X = X.fillna(0)
        
        if include_target and 'target' in df.columns:
            y = df['target'].copy()
            return X, y
        else:
            return X, None
    
    def get_data_summary(self, df: Optional[pd.DataFrame] = None) -> Dict[str, any]:
        """
        Get summary statistics of the dataset.
        
        Args:
            df: DataFrame to summarize (loads from disk if None)
            
        Returns:
            Dictionary with summary statistics
        """
        if df is None:
            processed_file = self.processed_path / "features.parquet"
            if not processed_file.exists():
                raise FileNotFoundError(f"No processed data found at {processed_file}")
            df = pd.read_parquet(processed_file)
        
        summary = {
            'total_matches': len(df),
            'date_range': (df['date'].min(), df['date'].max()),
            'num_features': len(self.feature_engineer.get_feature_names()),
            'unique_players': len(set(df['player1'].unique()) | set(df['player2'].unique())),
            'unique_tournaments': df['tournament'].nunique(),
            'class_balance': df['target'].value_counts().to_dict() if 'target' in df.columns else None,
            'missing_values': df.isnull().sum().sum(),
        }
        
        return summary
