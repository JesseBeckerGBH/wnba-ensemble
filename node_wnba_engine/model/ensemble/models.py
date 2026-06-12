import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import StackingClassifier, RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier, XGBRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, mean_absolute_error
import pandas as pd

class ModelEnsemble:
    def __init__(self):
        # Base estimators for classification (Moneyline)
        self.clf_estimators = [
            ('dt', DecisionTreeClassifier(max_depth=5, random_state=42)),
            ('xgb', XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42, eval_metric='logloss')),
            ('rf', RandomForestClassifier(n_estimators=100, random_state=42))
        ]
        
        self.stack_clf = StackingClassifier(
            estimators=self.clf_estimators, 
            final_estimator=LogisticRegression(), 
            cv=5
        )
        
        # For predicting exact spread
        self.spread_regressor = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
        
        # Default Transition Matrix for Markov Sim (if none provided)
        # Represents possession states: ends in [0, 1, 2, 3] points
        self.default_trans_matrix = np.array([
            [0.45, 0.10, 0.35, 0.10],  # From state 0
            [0.40, 0.15, 0.35, 0.10],  # From state 1
            [0.35, 0.15, 0.40, 0.10],  # From state 2
            [0.30, 0.15, 0.40, 0.15]   # From state 3
        ])

    def train_moneyline(self, df, features):
        """Train Stacking Classifier for Moneyline (Home Win probability)"""
        print("\n--- Training Moneyline Ensemble ---")
        train = df[df['season'] < 2024]
        test = df[df['season'] >= 2024]
        
        if len(test) == 0: # Fallback if dates aren't split properly
            train, test = train_test_split(df, test_size=0.2, random_state=42, shuffle=False)

        X_train, y_train = train[features], train['home_win']
        X_test, y_test = test[features], test['home_win']

        self.stack_clf.fit(X_train, y_train)
        preds = self.stack_clf.predict(X_test)
        probs = self.stack_clf.predict_proba(X_test)[:, 1]
        
        acc = accuracy_score(y_test, preds)
        print(f"Moneyline Accuracy on Test Set (2024+): {acc:.4f}")
        return acc

    def train_spread(self, df, features):
        """Train XGBoost Regressor for Spread prediction"""
        print("\n--- Training Spread Regressor ---")
        train = df[df['season'] < 2024]
        test = df[df['season'] >= 2024]
        
        if len(test) == 0:
            train, test = train_test_split(df, test_size=0.2, random_state=42, shuffle=False)

        X_train, y_train = train[features], train['spread']
        X_test, y_test = test[features], test['spread']

        self.spread_regressor.fit(X_train, y_train)
        preds = self.spread_regressor.predict(X_test)
        
        mae = mean_absolute_error(y_test, preds)
        print(f"Spread MAE on Test Set (2024+): {mae:.2f} points")
        return mae

    def markov_sim(self, trans_matrix=None, n_poss=80, start_state=0):
        """Simulate a single game for one team using Markov Chains"""
        if trans_matrix is None:
            trans_matrix = self.default_trans_matrix
            
        scores = []
        state = start_state
        for _ in range(n_poss):
            state = np.random.choice([0, 1, 2, 3], p=trans_matrix[state])
            scores.append(state)
        return sum(scores)

    def simulate_over_under(self, n_sims=10000, target_total=160.5):
        """Runs Monte Carlo using Markov Chain to predict O/U probability"""
        print(f"\n--- Running {n_sims} Markov Sims for O/U {target_total} ---")
        # Simulating home and away possessions (rough avg is ~80 poss/game per team in WNBA)
        sims = [self.markov_sim() + self.markov_sim() for _ in range(n_sims)]
        
        ou_prob = np.mean(np.array(sims) > target_total)
        avg_total = np.mean(sims)
        print(f"Simulated Average Total: {avg_total:.1f}")
        print(f"Probability over {target_total}: {ou_prob:.2%}")
        return ou_prob

if __name__ == "__main__":
    from data_prep import load_and_prep_data
    df, feats = load_and_prep_data()
    
    ensemble = ModelEnsemble()
    if feats:
        ensemble.train_moneyline(df, feats)
        ensemble.train_spread(df, feats)
    ensemble.simulate_over_under()
