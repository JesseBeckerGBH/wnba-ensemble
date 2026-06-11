"""PyTorch neural network model implementation."""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from typing import Dict, Any, Optional, List
from loguru import logger

from .base_model import BaseModel


class MLPClassifier(nn.Module):
    """Multi-layer perceptron for binary classification."""
    
    def __init__(
        self,
        input_dim: int,
        hidden_layers: List[int] = [128, 64, 32],
        dropout: float = 0.3
    ):
        """
        Initialize MLP.
        
        Args:
            input_dim: Number of input features
            hidden_layers: List of hidden layer sizes
            dropout: Dropout rate
        """
        super(MLPClassifier, self).__init__()
        
        layers = []
        prev_dim = input_dim
        
        # Build hidden layers
        for hidden_dim in hidden_layers:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim
        
        # Output layer
        layers.append(nn.Linear(prev_dim, 1))
        layers.append(nn.Sigmoid())
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        """Forward pass."""
        return self.network(x)


class NeuralNetworkModel(BaseModel):
    """PyTorch neural network model."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize neural network model.
        
        Args:
            config: Model configuration
        """
        super().__init__("NeuralNetwork", config)
        
        self.hidden_layers = config.get('hidden_layers', [128, 64, 32])
        self.dropout = config.get('dropout', 0.3)
        self.learning_rate = config.get('learning_rate', 0.001)
        self.batch_size = config.get('batch_size', 64)
        self.epochs = config.get('epochs', 100)
        self.early_stopping_patience = config.get('early_stopping_patience', 10)
        self.random_state = config.get('random_state', 42)
        
        # Set random seeds for reproducibility
        torch.manual_seed(self.random_state)
        np.random.seed(self.random_state)
        
        # Device (CPU or GPU)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[tuple] = None
    ) -> 'NeuralNetworkModel':
        """
        Train neural network.
        
        Args:
            X: Training features
            y: Training target
            eval_set: Optional validation set (X_val, y_val)
            
        Returns:
            Self for method chaining
        """
        logger.info(f"Training {self.model_name} on {len(X)} samples (device: {self.device})")
        
        # Convert to numpy
        X_np = X.values.astype(np.float32)
        y_np = y.values.astype(np.float32)
        
        # Initialize model
        input_dim = X_np.shape[1]
        self.model = MLPClassifier(
            input_dim=input_dim,
            hidden_layers=self.hidden_layers,
            dropout=self.dropout
        ).to(self.device)
        
        # Loss and optimizer
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Create data loader
        train_dataset = TensorDataset(
            torch.FloatTensor(X_np),
            torch.FloatTensor(y_np)
        )
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.batch_size,
            shuffle=True
        )
        
        # Validation data if provided
        if eval_set is not None:
            X_val, y_val = eval_set
            X_val_np = X_val.values.astype(np.float32)
            y_val_np = y_val.values.astype(np.float32)
            
            val_dataset = TensorDataset(
                torch.FloatTensor(X_val_np),
                torch.FloatTensor(y_val_np)
            )
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.batch_size,
                shuffle=False
            )
        else:
            val_loader = None
        
        # Training loop
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(self.epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            
            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)
                
                # Forward pass
                optimizer.zero_grad()
                outputs = self.model(batch_X).squeeze()
                loss = criterion(outputs, batch_y)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            train_loss /= len(train_loader)
            
            # Validation phase
            if val_loader is not None:
                self.model.eval()
                val_loss = 0.0
                
                with torch.no_grad():
                    for batch_X, batch_y in val_loader:
                        batch_X = batch_X.to(self.device)
                        batch_y = batch_y.to(self.device)
                        
                        outputs = self.model(batch_X).squeeze()
                        loss = criterion(outputs, batch_y)
                        val_loss += loss.item()
                
                val_loss /= len(val_loader)
                
                # Early stopping
                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= self.early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break
                
                if (epoch + 1) % 10 == 0:
                    logger.debug(f"Epoch {epoch+1}/{self.epochs}: "
                               f"Train Loss={train_loss:.4f}, Val Loss={val_loss:.4f}")
            else:
                if (epoch + 1) % 10 == 0:
                    logger.debug(f"Epoch {epoch+1}/{self.epochs}: Train Loss={train_loss:.4f}")
        
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
        
        self.model.eval()
        
        X_np = X.values.astype(np.float32)
        X_tensor = torch.FloatTensor(X_np).to(self.device)
        
        with torch.no_grad():
            probas = self.model(X_tensor).squeeze().cpu().numpy()
        
        return probas
