"""Base model class for all ensemble members."""

from abc import ABC, abstractmethod
import pickle
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import pandas as pd
from loguru import logger


class BaseModel(ABC):
    """Abstract base class for all models in the ensemble."""
    
    def __init__(self, model_name: str, config: Dict[str, Any]):
        """
        Initialize base model.
        
        Args:
            model_name: Name of the model
            config: Model configuration dictionary
        """
        self.model_name = model_name
        self.config = config
        self.model: Optional[Any] = None
        self.is_trained = False
        self.feature_importance_: Optional[np.ndarray] = None
        
    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'BaseModel':
        """
        Train the model.
        
        Args:
            X: Training features
            y: Training target
            
        Returns:
            Self for method chaining
        """
        pass
    
    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict probabilities for class 1 (player1 wins).
        
        Args:
            X: Features
            
        Returns:
            Array of probabilities (0-1)
        """
        pass
    
    def predict(self, X: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """
        Predict binary outcomes.
        
        Args:
            X: Features
            threshold: Probability threshold for classification
            
        Returns:
            Array of binary predictions
        """
        probas = self.predict_proba(X)
        return (probas >= threshold).astype(int)
    
    def save(self, path: str) -> None:
        """
        Save model to disk.
        
        Args:
            path: Path to save model
        """
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'wb') as f:
            pickle.dump(self, f)
        
        logger.info(f"Saved {self.model_name} to {save_path}")
    
    @classmethod
    def load(cls, path: str) -> 'BaseModel':
        """
        Load model from disk.
        
        Args:
            path: Path to load model from
            
        Returns:
            Loaded model instance
        """
        with open(path, 'rb') as f:
            model = pickle.load(f)
        
        logger.info(f"Loaded {model.model_name} from {path}")
        return model
    
    def get_feature_importance(self) -> Optional[np.ndarray]:
        """
        Get feature importance scores.
        
        Returns:
            Array of feature importance scores or None
        """
        return self.feature_importance_
    
    def __repr__(self) -> str:
        """String representation."""
        status = "trained" if self.is_trained else "untrained"
        return f"{self.model_name} ({status})"
