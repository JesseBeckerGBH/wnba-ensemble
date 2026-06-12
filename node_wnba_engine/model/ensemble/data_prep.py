import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import numpy as np

def load_and_prep_data(filepath='d:\\WNBA\\data\\wnba_data_2015_2025.csv'):
    """
    Loads raw data and engineers features including rolling averages and Elo.
    Returns the processed dataframe and the feature columns used for modeling.
    """
    try:
        df = pd.read_csv(filepath)
        print(f"Loaded data from {filepath}")
    except FileNotFoundError:
        print(f"File {filepath} not found. Generating mock data for testing...")
        df = generate_mock_data()

    # Base targets
    df['home_win'] = (df['home_points'] > df['away_points']).astype(int)
    df['spread'] = df['home_points'] - df['away_points']
    df['total'] = df['home_points'] + df['away_points']

    # Rolling avgs (last 5 games per team) for basic box score stats
    stats_to_roll = ['fg_pct', 'reb', 'ast', 'to']
    for stat in stats_to_roll:
        # Check if columns exist in mock/real data, skip if not
        if f'home_{stat}' in df.columns and f'away_{stat}' in df.columns:
            df[f'home_{stat}_roll5'] = df.groupby('home_team')[f'home_{stat}'].rolling(5, min_periods=1).mean().reset_index(0, drop=True)
            df[f'away_{stat}_roll5'] = df.groupby('away_team')[f'away_{stat}'].rolling(5, min_periods=1).mean().reset_index(0, drop=True)

    # Simple Elo implementation
    def update_elo(winner_elo, loser_elo, k=32):
        expected = 1 / (1 + 10**((loser_elo - winner_elo) / 400))
        return winner_elo + k * (1 - expected), loser_elo + k * (expected - 1)

    # Initialize Elo
    elo_dict = {}
    df['home_elo_pre'] = 1500.0
    df['away_elo_pre'] = 1500.0

    # Sort chronologically if a date column exists
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)

    for idx, row in df.iterrows():
        ht = row['home_team']
        at = row['away_team']
        
        # Get current elo or initialize
        h_elo = elo_dict.get(ht, 1500.0)
        a_elo = elo_dict.get(at, 1500.0)
        
        df.at[idx, 'home_elo_pre'] = h_elo
        df.at[idx, 'away_elo_pre'] = a_elo
        
        # Update Elo post-game
        if row['home_win'] == 1:
            new_h_elo, new_a_elo = update_elo(h_elo, a_elo)
        else:
            new_a_elo, new_h_elo = update_elo(a_elo, h_elo)
            
        elo_dict[ht] = new_h_elo
        elo_dict[at] = new_a_elo

    # Normalize engineered features
    scaler = MinMaxScaler()
    features = [col for col in df.columns if 'roll' in col or 'elo' in col or 'rest' in col]
    
    if features:
        # Fill NAs from rolling means (first few games)
        df[features] = df[features].fillna(df[features].mean())
        df[features] = scaler.fit_transform(df[features])
    
    return df, features

def generate_mock_data(n_games=1000):
    """Generates mock WNBA data to test the pipeline before real data scraping is complete."""
    np.random.seed(42)
    teams = [f"Team_{i}" for i in range(1, 13)] # 12 WNBA teams
    
    data = []
    # Generate ~80 games per team
    for i in range(n_games):
        matchup = np.random.choice(teams, 2, replace=False)
        date = pd.Timestamp('2020-01-01') + pd.Timedelta(days=i//3) # Rough chronological
        
        # Base stats
        home_pts = int(np.random.normal(82, 10))
        away_pts = int(np.random.normal(80, 10))
        
        data.append({
            'date': date,
            'season': date.year,
            'home_team': matchup[0],
            'away_team': matchup[1],
            'home_points': home_pts,
            'away_points': away_pts,
            'home_fg_pct': np.random.normal(0.44, 0.05),
            'away_fg_pct': np.random.normal(0.43, 0.05),
            'home_reb': int(np.random.normal(35, 5)),
            'away_reb': int(np.random.normal(34, 5)),
            'home_ast': int(np.random.normal(20, 4)),
            'away_ast': int(np.random.normal(19, 4)),
            'home_to': int(np.random.normal(14, 3)),
            'away_to': int(np.random.normal(14, 3)),
            'home_rest_days': np.random.choice([1, 2, 3, 4]),
            'away_rest_days': np.random.choice([1, 2, 3, 4])
        })
        
    df = pd.DataFrame(data)
    # Ensure some 2024 test data for splits
    df.loc[n_games-200:, 'season'] = 2024
    
    return df

if __name__ == "__main__":
    df, features = load_and_prep_data()
    print(f"Data Prep Complete. Shape: {df.shape}")
    print(f"Engineered Features used: {features}")
