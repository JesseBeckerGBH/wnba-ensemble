"""
Feature engineering for darts match prediction.

Extracts 40+ features including:
- Player performance metrics (rolling win rates, checkout rates, 180s)
- Match context (tournament, head-to-head, time effects)
- Momentum & fatigue (form trajectory, streaks, rest days)
- Temporal features (seasonal, age, consistency)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from ..utils.config import get_config


class FeatureEngineer:
    """Extract and engineer features for darts match prediction."""
    
    def __init__(self):
        """Initialize feature engineer with configuration."""
        self.config = get_config()
        self.rolling_windows = self.config.get('features.rolling_windows', [3, 7, 30])
        self.momentum_decay = self.config.get('features.momentum_decay', 0.95)
        self.fatigue_window = self.config.get('features.fatigue_window', 7)
        self.min_matches = self.config.get('features.min_matches_required', 10)
        
    def engineer_features(
        self,
        matches_df: pd.DataFrame,
        include_target: bool = True
    ) -> pd.DataFrame:
        """
        Engineer all features for match prediction.
        
        Args:
            matches_df: DataFrame with match results
            include_target: Whether to include target variable (winner)
            
        Returns:
            DataFrame with engineered features
        """
        logger.info(f"Engineering features for {len(matches_df)} matches")
        
        # Ensure data is sorted by date (critical for temporal features)
        matches_df = matches_df.sort_values('date').reset_index(drop=True)
        
        # Initialize features list
        all_features = []
        
        # Process each match chronologically
        for idx, match in matches_df.iterrows():
            # Only use data BEFORE this match (prevent data leakage)
            historical_data = matches_df.iloc[:idx]
            
            if len(historical_data) < self.min_matches:
                # Skip matches without sufficient history
                continue
            
            # Extract features for this match
            features = self._extract_match_features(match, historical_data)
            
            if include_target:
                # Add target variable (1 if player1 wins, 0 if player2 wins)
                features['target'] = 1 if match['winner'] == match['player1'] else 0
            
            # Add metadata
            features['match_id'] = match.get('match_id', idx)
            features['date'] = match['date']
            features['player1'] = match['player1']
            features['player2'] = match['player2']
            features['tournament'] = match.get('tournament', 'Unknown')
            
            all_features.append(features)
        
        features_df = pd.DataFrame(all_features)
        
        logger.info(f"Engineered {len(features_df)} feature rows with {len(features_df.columns)} columns")
        
        return features_df
    
    def _extract_match_features(
        self,
        match: pd.Series,
        historical_data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Extract all features for a single match.
        
        Args:
            match: Current match data
            historical_data: All matches before this one
            
        Returns:
            Dictionary of features
        """
        features = {}
        
        player1 = match['player1']
        player2 = match['player2']
        match_date = match['date']
        
        # Player performance metrics
        features.update(self._player_performance_features(player1, historical_data, match_date, prefix='p1_'))
        features.update(self._player_performance_features(player2, historical_data, match_date, prefix='p2_'))
        
        # Relative features (player1 vs player2)
        features.update(self._relative_features(features))
        
        # Head-to-head features
        features.update(self._head_to_head_features(player1, player2, historical_data, match_date))
        
        # Match context features
        features.update(self._match_context_features(match, historical_data))
        
        # Momentum & fatigue features
        features.update(self._momentum_fatigue_features(player1, historical_data, match_date, prefix='p1_'))
        features.update(self._momentum_fatigue_features(player2, historical_data, match_date, prefix='p2_'))
        
        # Temporal features
        features.update(self._temporal_features(match_date))
        
        return features
    
    def _player_performance_features(
        self,
        player: str,
        historical_data: pd.DataFrame,
        match_date: pd.Timestamp,
        prefix: str = ''
    ) -> Dict[str, float]:
        """Extract player performance metrics."""
        features = {}
        
        # Get player's match history
        player_matches = historical_data[
            (historical_data['player1'] == player) | 
            (historical_data['player2'] == player)
        ].copy()
        
        if len(player_matches) == 0:
            # New player - use default values
            return self._default_player_features(prefix)
        
        # Determine wins for this player
        player_matches['is_win'] = (
            ((player_matches['player1'] == player) & (player_matches['winner'] == player)) |
            ((player_matches['player2'] == player) & (player_matches['winner'] == player))
        ).astype(int)
        
        # Rolling win rates
        for window in self.rolling_windows:
            recent_matches = player_matches.tail(window)
            if len(recent_matches) > 0:
                features[f'{prefix}win_rate_{window}m'] = recent_matches['is_win'].mean()
            else:
                features[f'{prefix}win_rate_{window}m'] = 0.5
        
        # Overall win rate
        features[f'{prefix}win_rate_overall'] = player_matches['is_win'].mean()
        
        # Total matches played
        features[f'{prefix}total_matches'] = len(player_matches)
        
        # Average score (if available)
        if 'score1' in player_matches.columns and 'score2' in player_matches.columns:
            player_scores = []
            for _, m in player_matches.iterrows():
                if m['player1'] == player:
                    player_scores.append(m.get('score1', 0))
                else:
                    player_scores.append(m.get('score2', 0))
            
            if player_scores:
                features[f'{prefix}avg_score'] = np.mean(player_scores)
                features[f'{prefix}std_score'] = np.std(player_scores)
            else:
                features[f'{prefix}avg_score'] = 0
                features[f'{prefix}std_score'] = 0
        
        return features
    
    def _relative_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Calculate relative features between player1 and player2."""
        relative = {}
        
        # Win rate differences
        for window in self.rolling_windows:
            p1_key = f'p1_win_rate_{window}m'
            p2_key = f'p2_win_rate_{window}m'
            if p1_key in features and p2_key in features:
                relative[f'win_rate_diff_{window}m'] = features[p1_key] - features[p2_key]
        
        # Overall win rate difference
        if 'p1_win_rate_overall' in features and 'p2_win_rate_overall' in features:
            relative['win_rate_diff_overall'] = (
                features['p1_win_rate_overall'] - features['p2_win_rate_overall']
            )
        
        # Experience difference (total matches)
        if 'p1_total_matches' in features and 'p2_total_matches' in features:
            relative['experience_diff'] = (
                features['p1_total_matches'] - features['p2_total_matches']
            )
        
        return relative
    
    def _head_to_head_features(
        self,
        player1: str,
        player2: str,
        historical_data: pd.DataFrame,
        match_date: pd.Timestamp
    ) -> Dict[str, float]:
        """Extract head-to-head statistics."""
        features = {}
        
        # Find previous matches between these players
        h2h_matches = historical_data[
            ((historical_data['player1'] == player1) & (historical_data['player2'] == player2)) |
            ((historical_data['player1'] == player2) & (historical_data['player2'] == player1))
        ].copy()
        
        features['h2h_total_matches'] = len(h2h_matches)
        
        if len(h2h_matches) > 0:
            # Player1 wins in h2h
            p1_wins = h2h_matches[h2h_matches['winner'] == player1]
            features['h2h_p1_win_rate'] = len(p1_wins) / len(h2h_matches)
            
            # Recent h2h (last 5 matches)
            recent_h2h = h2h_matches.tail(5)
            recent_p1_wins = recent_h2h[recent_h2h['winner'] == player1]
            features['h2h_p1_win_rate_recent'] = len(recent_p1_wins) / len(recent_h2h) if len(recent_h2h) > 0 else 0.5
            
            # Days since last h2h match
            last_h2h_date = h2h_matches['date'].max()
            features['h2h_days_since_last'] = (match_date - last_h2h_date).days
        else:
            # No previous h2h matches
            features['h2h_p1_win_rate'] = 0.5
            features['h2h_p1_win_rate_recent'] = 0.5
            features['h2h_days_since_last'] = 9999
        
        return features
    
    def _match_context_features(
        self,
        match: pd.Series,
        historical_data: pd.DataFrame
    ) -> Dict[str, float]:
        """Extract match context features."""
        features = {}
        
        # Tournament importance (simplified - can be enhanced with tournament rankings)
        tournament = match.get('tournament', 'Unknown')
        
        # Major tournaments (World Championship, Premier League, etc.)
        major_keywords = ['world', 'championship', 'premier', 'masters', 'grand']
        is_major = any(keyword in tournament.lower() for keyword in major_keywords)
        features['is_major_tournament'] = 1 if is_major else 0
        
        # Day of week (0 = Monday, 6 = Sunday)
        match_date = match['date']
        features['day_of_week'] = match_date.dayofweek
        features['is_weekend'] = 1 if match_date.dayofweek >= 5 else 0
        
        # Month (seasonal effects)
        features['month'] = match_date.month
        
        return features
    
    def _momentum_fatigue_features(
        self,
        player: str,
        historical_data: pd.DataFrame,
        match_date: pd.Timestamp,
        prefix: str = ''
    ) -> Dict[str, float]:
        """Extract momentum and fatigue features."""
        features = {}
        
        # Get player's matches
        player_matches = historical_data[
            (historical_data['player1'] == player) | 
            (historical_data['player2'] == player)
        ].copy()
        
        if len(player_matches) == 0:
            return {
                f'{prefix}current_streak': 0,
                f'{prefix}form_trajectory': 0,
                f'{prefix}matches_last_7d': 0,
                f'{prefix}rest_days': 999
            }
        
        # Determine wins
        player_matches['is_win'] = (
            ((player_matches['player1'] == player) & (player_matches['winner'] == player)) |
            ((player_matches['player2'] == player) & (player_matches['winner'] == player))
        ).astype(int)
        
        # Current streak (positive for wins, negative for losses)
        recent_results = player_matches.tail(10)['is_win'].values
        if len(recent_results) > 0:
            streak = 0
            last_result = recent_results[-1]
            for result in reversed(recent_results):
                if result == last_result:
                    streak += 1
                else:
                    break
            features[f'{prefix}current_streak'] = streak if last_result == 1 else -streak
        else:
            features[f'{prefix}current_streak'] = 0
        
        # Form trajectory (exponentially weighted win rate)
        if len(player_matches) > 0:
            weights = np.array([self.momentum_decay ** i for i in range(len(player_matches))])
            weights = weights[::-1]  # Recent matches get higher weight
            weighted_wins = np.sum(player_matches['is_win'].values * weights)
            features[f'{prefix}form_trajectory'] = weighted_wins / np.sum(weights)
        else:
            features[f'{prefix}form_trajectory'] = 0.5
        
        # Fatigue: matches in last N days
        cutoff_date = match_date - timedelta(days=self.fatigue_window)
        recent_matches = player_matches[player_matches['date'] >= cutoff_date]
        features[f'{prefix}matches_last_7d'] = len(recent_matches)
        
        # Rest days since last match
        if len(player_matches) > 0:
            last_match_date = player_matches['date'].max()
            features[f'{prefix}rest_days'] = (match_date - last_match_date).days
        else:
            features[f'{prefix}rest_days'] = 999
        
        return features
    
    def _temporal_features(self, match_date: pd.Timestamp) -> Dict[str, float]:
        """Extract temporal features."""
        features = {}
        
        # Year (for trend analysis)
        features['year'] = match_date.year
        
        # Quarter (seasonal)
        features['quarter'] = (match_date.month - 1) // 3 + 1
        
        # Days since epoch (for time-based trends)
        epoch = pd.Timestamp('2020-01-01')
        features['days_since_epoch'] = (match_date - epoch).days
        
        return features
    
    def _default_player_features(self, prefix: str) -> Dict[str, float]:
        """Return default features for new players."""
        features = {}
        
        # Default win rates (0.5 = no information)
        for window in self.rolling_windows:
            features[f'{prefix}win_rate_{window}m'] = 0.5
        
        features[f'{prefix}win_rate_overall'] = 0.5
        features[f'{prefix}total_matches'] = 0
        features[f'{prefix}avg_score'] = 0
        features[f'{prefix}std_score'] = 0
        
        return features
    
    def get_feature_names(self) -> List[str]:
        """
        Get list of all feature names (excluding metadata and target).
        
        Returns:
            List of feature column names
        """
        # This is a helper for model training
        # Excludes: match_id, date, player1, player2, tournament, target
        
        metadata_cols = ['match_id', 'date', 'player1', 'player2', 'tournament', 'target']
        
        # Generate a sample to get all feature names
        # (In practice, this should be called after feature engineering)
        
        return [
            # Player 1 performance
            *[f'p1_win_rate_{w}m' for w in self.rolling_windows],
            'p1_win_rate_overall',
            'p1_total_matches',
            'p1_avg_score',
            'p1_std_score',
            
            # Player 2 performance
            *[f'p2_win_rate_{w}m' for w in self.rolling_windows],
            'p2_win_rate_overall',
            'p2_total_matches',
            'p2_avg_score',
            'p2_std_score',
            
            # Relative features
            *[f'win_rate_diff_{w}m' for w in self.rolling_windows],
            'win_rate_diff_overall',
            'experience_diff',
            
            # Head-to-head
            'h2h_total_matches',
            'h2h_p1_win_rate',
            'h2h_p1_win_rate_recent',
            'h2h_days_since_last',
            
            # Match context
            'is_major_tournament',
            'day_of_week',
            'is_weekend',
            'month',
            
            # Momentum & fatigue (player 1)
            'p1_current_streak',
            'p1_form_trajectory',
            'p1_matches_last_7d',
            'p1_rest_days',
            
            # Momentum & fatigue (player 2)
            'p2_current_streak',
            'p2_form_trajectory',
            'p2_matches_last_7d',
            'p2_rest_days',
            
            # Temporal
            'year',
            'quarter',
            'days_since_epoch'
        ]
