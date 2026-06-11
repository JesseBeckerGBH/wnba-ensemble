"""LightGBM model implementation."""

import numpy as np
import pandas as pd
import lightgbm as lgb
from typing import Dict, Any, Optional
from loguru import logger

from .base_model import BaseModel


class LightGBMModel(BaseModel):
    """LightGBM gradient boosting model."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LightGBM model.
        
        Args:
            config: Model configuration
        """
        super().__init__("LightGBM", config)
        
        # Extract LightGBM parameters from config
        self.params = {
            'n_estimators': config.get('n_estimators', 200),
            'max_depth': config.get('max_depth', 6),
            'learning_rate': config.get('learning_rate', 0.05),
            'num_leaves': config.get('num_leaves', 31),
            'random_state': config.get('random_state', 42),
            'objective': 'binary',
            'metric': 'binary_logloss',
            'verbosity': -1
        }
        
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[tuple] = None,
        early_stopping_rounds: int = 10
    ) -> 'LightGBMModel':
        """
        Train LightGBM model.
        
        Args:
            X: Training features
            y: Training target
            eval_set: Optional validation set (X_val, y_val)
            early_stopping_rounds: Early stopping patience
            
        Returns:
            Self for method chaining
        """
        logger.info(f"Training {self.model_name} on {len(X)} samples")
        
        # Initialize model
        self.model = lgb.LGBMClassifier(**self.params)
        
        # Prepare eval set if provided
        if eval_set is not None:
            X_val, y_val = eval_set
            eval_set_formatted = [(X_val, y_val)]
            
            self.model.fit(
                X, y,
                eval_set=eval_set_formatted,
                callbacks=[lgb.early_stopping(early_stopping_rounds, verbose=False)]
            )
        else:
            self.model.fit(X, y)
        
        self.is_trained = True
        
        # Store feature importance
        self.feature_importance_ = self.model.feature_importances_
        
        logger.info(f"{self.model_name} training complete")
        
        return self
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict probabilities.
        
        Args:
            X: Features
            
        Returns:
            Array of probabilities for class 1
        """
        if not self.is_trained:
            raise ValueError(f"{self.model_name} must be trained before prediction")
        
        # LightGBM returns probabilities for both classes
        probas = self.model.predict_proba(X)
        
        # Return probability of class 1 (player1 wins)
        return probas[:, 1]
    
    def get_feature_importance(self, feature_names: Optional[list] = None) -> pd.DataFrame:
        """
        Get feature importance as DataFrame.
        
        Args:
            feature_names: Optional list of feature names
            
        Returns:
            DataFrame with feature importance
        """
        if self.feature_importance_ is None:
            return pd.DataFrame()
        
        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(len(self.feature_importance_))]
        
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': self.feature_importance_
        }).sort_values('importance', ascending=False)
        
        return importance_df
