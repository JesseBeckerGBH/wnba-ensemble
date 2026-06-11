"""XGBoost model implementation."""

import numpy as np
import pandas as pd
import xgboost as xgb
from typing import Dict, Any, Optional
from loguru import logger

from .base_model import BaseModel


class XGBoostModel(BaseModel):
    """XGBoost gradient boosting model."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize XGBoost model.
        
        Args:
            config: Model configuration
        """
        super().__init__("XGBoost", config)
        
        # Extract XGBoost parameters from config
        self.params = {
            'n_estimators': config.get('n_estimators', 200),
            'max_depth': config.get('max_depth', 6),
            'learning_rate': config.get('learning_rate', 0.05),
            'subsample': config.get('subsample', 0.8),
            'colsample_bytree': config.get('colsample_bytree', 0.8),
            'random_state': config.get('random_state', 42),
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'use_label_encoder': False
        }
        
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[tuple] = None,
        early_stopping_rounds: int = 10
    ) -> 'XGBoostModel':
        """
        Train XGBoost model.
        
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
        self.model = xgb.XGBClassifier(**self.params)
        
        # Prepare eval set and callbacks if provided
        if eval_set is not None:
            X_val, y_val = eval_set
            eval_set_formatted = [(X_val, y_val)]
            
            # Use callbacks for early stopping (new XGBoost API)
            callbacks = [xgb.callback.EarlyStopping(rounds=early_stopping_rounds, save_best=True)]
            
            self.model.fit(
                X, y,
                eval_set=eval_set_formatted,
                callbacks=callbacks,
                verbose=False
            )
        else:
            self.model.fit(X, y, verbose=False)
        
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
        
        # XGBoost returns probabilities for both classes
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
