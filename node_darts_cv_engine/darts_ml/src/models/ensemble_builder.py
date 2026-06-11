"""
Ensemble builder for combining multiple models.

Implements stacked averaging with adaptive weighting.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
import pickle

from .xgboost_model import XGBoostModel
from .lightgbm_model import LightGBMModel
from .neural_network import NeuralNetworkModel
from .bayesian_ridge_model import BayesianRidgeModel
from ..utils.config import get_config


class EnsembleBuilder:
    """Manage ensemble of multiple models with adaptive weighting."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ensemble builder.
        
        Args:
            config: Configuration dictionary (uses global config if None)
        """
        if config is None:
            config = get_config()
        
        self.config = config
        
        # Initialize models
        self.models = {
            'xgboost': XGBoostModel(config.get('models.xgboost', {})),
            'lightgbm': LightGBMModel(config.get('models.lightgbm', {})),
            'neural_network': NeuralNetworkModel(config.get('models.neural_network', {})),
            'bayesian_ridge': BayesianRidgeModel(config.get('models.bayesian_ridge', {}))
        }
        
        # Initialize weights (equal by default)
        initial_weights = config.get('ensemble.initial_weights', [0.25, 0.25, 0.25, 0.25])
        self.weights = np.array(initial_weights)
        
        # Weight constraints
        self.min_weight = config.get('ensemble.min_weight', 0.05)
        self.max_weight = config.get('ensemble.max_weight', 0.60)
        
        self.is_trained = False
        
    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: Optional[pd.DataFrame] = None,
        y_val: Optional[pd.Series] = None
    ) -> 'EnsembleBuilder':
        """
        Train all models in the ensemble.
        
        Args:
            X_train: Training features
            y_train: Training target
            X_val: Validation features (optional)
            y_val: Validation target (optional)
            
        Returns:
            Self for method chaining
        """
        logger.info(f"Training ensemble with {len(self.models)} models")
        
        eval_set = (X_val, y_val) if X_val is not None and y_val is not None else None
        
        # Train each model
        for model_name, model in self.models.items():
            logger.info(f"Training {model_name}...")
            
            try:
                if model_name in ['xgboost', 'lightgbm', 'neural_network'] and eval_set is not None:
                    model.fit(X_train, y_train, eval_set=eval_set)
                else:
                    model.fit(X_train, y_train)
                
                logger.info(f"{model_name} training complete")
                
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
                raise
        
        self.is_trained = True
        logger.info("Ensemble training complete")
        
        return self
    
    def predict_proba(
        self,
        X: pd.DataFrame,
        return_individual: bool = False
    ) -> np.ndarray:
        """
        Predict probabilities using weighted ensemble.
        
        Args:
            X: Features
            return_individual: If True, return individual model predictions
            
        Returns:
            Array of ensemble probabilities (or dict if return_individual=True)
        """
        if not self.is_trained:
            raise ValueError("Ensemble must be trained before prediction")
        
        # Get predictions from each model
        predictions = {}
        for model_name, model in self.models.items():
            predictions[model_name] = model.predict_proba(X)
        
        # Combine predictions using weights
        ensemble_pred = np.zeros(len(X))
        for i, (model_name, pred) in enumerate(predictions.items()):
            ensemble_pred += self.weights[i] * pred
        
        if return_individual:
            predictions['ensemble'] = ensemble_pred
            return predictions
        else:
            return ensemble_pred
    
    def update_weights(
        self,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        method: str = 'performance_based'
    ) -> None:
        """
        Update ensemble weights based on validation performance.
        
        Args:
            X_val: Validation features
            y_val: Validation target
            method: Weight update method ('performance_based' or 'inverse_error')
        """
        logger.info(f"Updating ensemble weights using method: {method}")
        
        # Get predictions from each model
        predictions = []
        for model in self.models.values():
            pred = model.predict_proba(X_val)
            predictions.append(pred)
        
        predictions = np.array(predictions)
        
        if method == 'performance_based':
            # Weight based on Brier score (lower is better)
            from sklearn.metrics import brier_score_loss
            
            scores = []
            for pred in predictions:
                score = brier_score_loss(y_val, pred)
                scores.append(score)
            
            scores = np.array(scores)
            
            # Inverse of scores (better models get higher weight)
            weights = 1 / (scores + 1e-6)
            
        elif method == 'inverse_error':
            # Weight based on inverse of absolute error
            errors = []
            for pred in predictions:
                error = np.mean(np.abs(pred - y_val))
                errors.append(error)
            
            errors = np.array(errors)
            weights = 1 / (errors + 1e-6)
        
        else:
            raise ValueError(f"Unknown weight update method: {method}")
        
        # Normalize weights to sum to 1
        weights = weights / np.sum(weights)
        
        # Apply constraints
        weights = np.clip(weights, self.min_weight, self.max_weight)
        weights = weights / np.sum(weights)  # Renormalize
        
        # Update weights
        old_weights = self.weights.copy()
        self.weights = weights
        
        logger.info(f"Weights updated:")
        for i, (model_name, old_w, new_w) in enumerate(zip(self.models.keys(), old_weights, weights)):
            logger.info(f"  {model_name}: {old_w:.3f} -> {new_w:.3f}")
    
    def get_feature_importance(
        self,
        feature_names: Optional[List[str]] = None,
        top_n: int = 20
    ) -> pd.DataFrame:
        """
        Get aggregated feature importance from tree-based models.
        
        Args:
            feature_names: List of feature names
            top_n: Number of top features to return
            
        Returns:
            DataFrame with feature importance
        """
        importances = []
        
        # Get importance from XGBoost and LightGBM
        for model_name in ['xgboost', 'lightgbm']:
            model = self.models[model_name]
            if hasattr(model, 'get_feature_importance'):
                imp_df = model.get_feature_importance(feature_names)
                if not imp_df.empty:
                    imp_df['model'] = model_name
                    importances.append(imp_df)
        
        if not importances:
            return pd.DataFrame()
        
        # Combine and average
        combined = pd.concat(importances)
        avg_importance = combined.groupby('feature')['importance'].mean().reset_index()
        avg_importance = avg_importance.sort_values('importance', ascending=False)
        
        return avg_importance.head(top_n)
    
    def save(self, path: str) -> None:
        """
        Save ensemble to disk.
        
        Args:
            path: Directory path to save ensemble
        """
        save_dir = Path(path)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Save each model
        for model_name, model in self.models.items():
            model_path = save_dir / f"{model_name}.pkl"
            model.save(str(model_path))
        
        # Save weights and metadata
        metadata = {
            'weights': self.weights,
            'is_trained': self.is_trained,
            'min_weight': self.min_weight,
            'max_weight': self.max_weight
        }
        
        metadata_path = save_dir / "ensemble_metadata.pkl"
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Saved ensemble to {save_dir}")
    
    @classmethod
    def load(cls, path: str, config: Optional[Dict[str, Any]] = None) -> 'EnsembleBuilder':
        """
        Load ensemble from disk.
        
        Args:
            path: Directory path to load ensemble from
            config: Configuration (uses global if None)
            
        Returns:
            Loaded ensemble instance
        """
        load_dir = Path(path)
        
        # Create new ensemble
        ensemble = cls(config)
        
        # Load each model
        for model_name in ensemble.models.keys():
            model_path = load_dir / f"{model_name}.pkl"
            if model_path.exists():
                ensemble.models[model_name] = ensemble.models[model_name].__class__.load(str(model_path))
        
        # Load metadata
        metadata_path = load_dir / "ensemble_metadata.pkl"
        if metadata_path.exists():
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            ensemble.weights = metadata['weights']
            ensemble.is_trained = metadata['is_trained']
            ensemble.min_weight = metadata.get('min_weight', 0.05)
            ensemble.max_weight = metadata.get('max_weight', 0.60)
        
        logger.info(f"Loaded ensemble from {load_dir}")
        
        return ensemble
    
    def __repr__(self) -> str:
        """String representation."""
        status = "trained" if self.is_trained else "untrained"
        weights_str = ", ".join([f"{w:.3f}" for w in self.weights])
        return f"Ensemble ({status}) - Weights: [{weights_str}]"
