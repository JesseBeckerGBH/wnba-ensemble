"""
Sample data generator for testing the darts betting ensemble.

Generates realistic synthetic darts match data for development and testing.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List
from pathlib import Path


class SampleDataGenerator:
    """Generate synthetic darts match data for testing."""
    
    def __init__(self, random_seed: int = 42):
        """Initialize generator with random seed."""
        np.random.seed(random_seed)
        self.random_seed = random_seed
        
        # Sample player names
        self.players = [
            "Michael van Gerwen", "Peter Wright", "Gerwyn Price",
            "Michael Smith", "James Wade", "Gary Anderson",
            "Rob Cross", "Nathan Aspinall", "Jonny Clayton",
            "Dimitri Van den Bergh", "Jose de Sousa", "Krzysztof Ratajski",
            "Dirk van Duijvenbode", "Dave Chisnall", "Joe Cullen",
            "Chris Dobey", "Danny Noppert", "Ryan Searle",
            "Luke Humphries", "Ross Smith"
        ]
        
        # Sample tournaments
        self.tournaments = [
            "World Championship", "Premier League", "UK Open",
            "European Championship", "Grand Slam", "World Matchplay",
            "Players Championship", "Masters", "World Grand Prix",
            "Challenge Tour"
        ]
        
        # Player skill levels (0-1, higher = better)
        self.player_skills = {
            player: np.random.beta(5, 2) for player in self.players
        }
    
    def generate_matches(
        self,
        num_matches: int = 1000,
        start_date: str = "2020-01-01",
        end_date: str = "2024-11-30"
    ) -> pd.DataFrame:
        """
        Generate synthetic match data.
        
        Args:
            num_matches: Number of matches to generate
            start_date: Start date for matches
            end_date: End date for matches
            
        Returns:
            DataFrame with match results
        """
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        matches = []
        
        for i in range(num_matches):
            # Random date within range
            days_diff = (end - start).days
            random_days = np.random.randint(0, days_diff)
            match_date = start + timedelta(days=random_days)
            
            # Random players
            player1, player2 = np.random.choice(self.players, size=2, replace=False)
            
            # Determine winner based on skill levels with some randomness
            skill1 = self.player_skills[player1]
            skill2 = self.player_skills[player2]
            
            # Probability player1 wins (logistic function of skill difference)
            skill_diff = skill1 - skill2
            prob_p1_wins = 1 / (1 + np.exp(-5 * skill_diff))
            
            # Add tournament importance factor
            tournament = np.random.choice(self.tournaments)
            is_major = any(kw in tournament for kw in ['World', 'Premier', 'Grand'])
            
            # Major tournaments: higher-skilled players more likely to win
            if is_major:
                prob_p1_wins = prob_p1_wins * 1.2 if skill1 > skill2 else prob_p1_wins * 0.8
                prob_p1_wins = np.clip(prob_p1_wins, 0.1, 0.9)
            
            # Determine winner
            p1_wins = np.random.random() < prob_p1_wins
            winner = player1 if p1_wins else player2
            
            # Generate scores (higher skill = higher score)
            base_score1 = int(np.random.normal(skill1 * 10, 2))
            base_score2 = int(np.random.normal(skill2 * 10, 2))
            
            # Winner gets higher score
            if p1_wins:
                score1 = max(base_score1, base_score2 + 1)
                score2 = base_score2
            else:
                score1 = base_score1
                score2 = max(base_score2, base_score1 + 1)
            
            match = {
                'match_id': i,
                'date': match_date,
                'tournament': tournament,
                'player1': player1,
                'player2': player2,
                'score1': max(0, score1),
                'score2': max(0, score2),
                'winner': winner,
                'source': 'synthetic'
            }
            
            matches.append(match)
        
        # Create DataFrame and sort by date
        df = pd.DataFrame(matches)
        df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def save_sample_data(
        self,
        output_path: str,
        num_matches: int = 1000
    ) -> None:
        """
        Generate and save sample data to CSV.
        
        Args:
            output_path: Path to save CSV file
            num_matches: Number of matches to generate
        """
        df = self.generate_matches(num_matches)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_file, index=False)
        print(f"Generated {len(df)} sample matches and saved to {output_file}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"Unique players: {len(set(df['player1']) | set(df['player2']))}")
        print(f"Unique tournaments: {df['tournament'].nunique()}")


if __name__ == "__main__":
    # Generate sample data for testing
    generator = SampleDataGenerator()
    generator.save_sample_data(
        "data/raw/sample_matches.csv",
        num_matches=2000
    )
