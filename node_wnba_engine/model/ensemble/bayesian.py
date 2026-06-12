import numpy as np
import pandas as pd
import arviz as az
import warnings

warnings.filterwarnings('ignore', category=UserWarning)

try:
    import pymc as pm
    PYMC_AVAILABLE = True
except ImportError:
    PYMC_AVAILABLE = False
    print("Warning: PyMC module not found or failed to load. Bayesian priors will be mocked. "
          "To fix, ensure PyMC and its C-compiler backend (PyTensor) are correctly installed.")

class BayesianPriors:
    def __init__(self):
        self.trace = None
        
    def fit_bayesian_logistic(self, df, features, n_samples=1000):
        """
        Fits a Bayesian Logistic Regression model to find priors for Moneyline.
        Uses a strong prior for Home Advantage based on historical WNBA averages.
        """
        if not PYMC_AVAILABLE:
            print("PyMC unavailable. Skipping actual Bayesian fitting.")
            return None

        print(f"\n--- Fitting Bayesian Logistic Regression ({n_samples} samples) ---")
        
        # Simple sample to keep compilation time reasonable locally
        df_sample = df.sample(min(len(df), 500), random_state=42)
        X_train = df_sample[features].values
        y_train = df_sample['home_win'].values
        
        with pm.Model() as bayes_ml:
            # Priors for feature coefficients
            beta = pm.Normal('beta', mu=0, sigma=1, shape=len(features))
            
            # Prior for Home Advantage (e.g. ~3 points translates to log-odds shift)
            # In WNBA, home advantage exists but might be slightly less than NBA.
            home_adv = pm.Normal('home_adv', mu=0.5, sigma=0.5)
            
            # Likelihood
            logits = pm.math.dot(X_train, beta) + home_adv
            p = pm.Deterministic('p', pm.math.sigmoid(logits))
            
            y_obs = pm.Bernoulli('y_obs', p=p, observed=y_train)
            
            # Sample from posterior
            print("Sampling...")
            try:
                self.trace = pm.sample(draws=n_samples, tune=500, cores=1, progressbar=False, return_inferencedata=True)
            except Exception as e:
                print(f"PyMC sampling failed: {e}")
                return None
                
        # Generate summary 
        summary = az.summary(self.trace, var_names=['home_adv'])
        print("\nBayesian Summary (Home Advantage):")
        print(summary)
        
        return self.trace

    def extract_priors(self, df, features):
        """
        Returns the mean of the posterior distributions to be injected 
        as priors into another model or analysis.
        """
        if not PYMC_AVAILABLE:
            # Provide sensible dummy priors if PyMC isn't installed
            print("Using fallback dummy priors for home advantage.")
            return {
                'beta_priors': {f: 0.01 for f in features},
                'home_adv_prior': 0.35
            }

        if self.trace is None:
            print("Model not fitted yet. Fitting now...")
            self.trace = self.fit_bayesian_logistic(df, features)
            
        if self.trace is None:
            return None
            
        beta_means = self.trace.posterior['beta'].mean(dim=['chain', 'draw']).values
        home_adv_mean = self.trace.posterior['home_adv'].mean(dim=['chain', 'draw']).values
        
        return {
            'beta_priors': dict(zip(features, beta_means)),
            'home_adv_prior': float(home_adv_mean)
        }

if __name__ == "__main__":
    from data_prep import load_and_prep_data
    df, features = load_and_prep_data()
    
    # Just take 2 features for a quick test run to avoid long PyMC compile times
    test_feats = features[:2] if len(features) >= 2 else features
    
    bayes = BayesianPriors()
    priors = bayes.extract_priors(df, test_feats)
    print("\nExtracted Priors:", priors)
