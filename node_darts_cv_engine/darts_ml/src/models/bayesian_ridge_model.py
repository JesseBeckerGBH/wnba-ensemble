"""Bayesian Ridge Regression model implementation."""

import numpy as np
import pandas as pd
from sklearn.linear_model import BayesianRidge
from typing import Dict, Any
from loguru import logger

from .base_model import BaseModel


class BayesianRidgeModel(BaseModel):
    """Bayesian Ridge Regression for probabilistic predictions."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Bayesian Ridge model.
        
        Args:
            config: Model configuration
        """
        super().__init__("BayesianRidge", config)
        
        # Extract parameters from config
        self.params = {
            'n_iter': config.get('n_iter', 300),
            'alpha_1': config.get('alpha_1', 1e-6),
            'alpha_2': config.get('alpha_2', 1e-6),
            'lambda_1': config.get('lambda_1', 1e-6),
            'lambda_2': config.get('lambda_2', 1e-6),
        }
        
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'BayesianRidgeModel':
        """
        Train Bayesian Ridge model.
        
        Args:
            X: Training features
            y: Training target
            
        Returns:
            Self for method chaining
        """
        logger.info(f"Training {self.model_name} on {len(X)} samples")
        
        # Initialize model
        self.model = BayesianRidge(**self.params)
        
        # Fit model
        self.model.fit(X, y)
        
        self.is_trained = True
        
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
        
        # Bayesian Ridge returns continuous predictions
        # We need to convert to probabilities [0, 1]
        predictions = self.model.predict(X)
        
        # Clip to [0, 1] range
        probas = np.clip(predictions, 0, 1)
        
        return probas
    
    def predict_with_uncertainty(self, X: pd.DataFrame) -> tuple:
        """
        Predict with uncertainty estimates.
        
        Args:
            X: Features
            
        Returns:
            Tuple of (predictions, standard_deviations)
        """
        if not self.is_trained:
            raise ValueError(f"{self.model_name} must be trained before prediction")
        
        # Get predictions and standard deviations
        predictions, std_devs = self.model.predict(X, return_std=True)
        
        # Clip predictions to [0, 1]
        probas = np.clip(predictions, 0, 1)
        
        return probas, std_devs
