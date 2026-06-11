# Professional Darts Betting Ensemble Stack

A production-grade ensemble probability estimator for professional darts (PDC, BDO, European Tour) with automated backtesting, self-calibration, and incremental learning.

## 🎯 Project Overview

This system combines multiple ML models with adaptive weighting to provide calibrated win probabilities for professional darts matches. It features:

- **4-Model Ensemble**: XGBoost, LightGBM, PyTorch Neural Network, Bayesian Ridge
- **Advanced Feature Engineering**: 40+ features including momentum, fatigue, head-to-head
- **Automated Backtesting**: Walk-forward validation with time-series integrity
- **Self-Calibration**: Isotonic regression with drift detection
- **Incremental Learning**: Online updates as new matches complete
- **Production-Ready**: Comprehensive error handling, logging, and monitoring

## 🏗️ Architecture

```
darts-betting-ensemble/
├── src/
│   ├── data/                    # Data acquisition and feature engineering
│   │   ├── darts_data_loader.py
│   │   ├── feature_engineering.py
│   │   └── etl_pipeline.py
│   ├── models/                  # ML ensemble and training
│   │   ├── ensemble_builder.py
│   │   ├── calibration.py
│   │   ├── incremental_learner.py
│   │   └── backtest_engine.py
│   ├── inference/               # Real-time predictions
│   │   ├── probability_estimator.py
│   │   ├── confidence_calculator.py
│   │   └── performance_tracker.py
│   └── utils/                   # Shared utilities
│       ├── config.py
│       ├── logger.py
│       └── metrics.py
├── data/                        # Data storage
│   ├── raw/                     # Raw match results
│   ├── processed/               # Engineered features
│   └── models/                  # Trained model artifacts
├── reports/                     # Backtest reports and visualizations
├── tests/                       # Unit and integration tests
├── cli.py                       # Command-line interface
├── main.py                      # End-to-end pipeline
├── config.yaml                  # Configuration
├── requirements.txt
├── Dockerfile
└── README.md
```

## 🚀 Quick Start

### Installation

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Run full pipeline (data → train → backtest → calibrate)
python main.py

# CLI commands
python cli.py backtest --start-date 2022-01-01 --end-date 2024-11-30
python cli.py train --retrain-all
python cli.py predict --player1 "Michael van Gerwen" --player2 "Peter Wright"
python cli.py calibrate
python cli.py monitor
```

## 📊 Core Features

### Ensemble Models

1. **XGBoost**: Gradient boosting baseline with tree-based feature importance
2. **LightGBM**: Fast gradient boosting optimized for large datasets
3. **Neural Network**: PyTorch MLP for capturing non-linear patterns
4. **Bayesian Ridge**: Probabilistic baseline with uncertainty quantification

**Combination Method**: Stacked averaging with learned meta-weights updated via online learning

### Feature Engineering (40+ Features)

**Player Performance**:
- Rolling win rates (3, 7, 30 matches)
- Average checkout rate
- 180-throw frequency
- Break-of-throw statistics

**Match Context**:
- Tournament importance
- Head-to-head history with recency weighting
- Day/time effects

**Momentum & Fatigue**:
- Recent form trajectory (exponential weighted)
- Consecutive win/loss streaks
- Match fatigue (matches in last 7 days)
- Rest days before match

**Temporal**:
- Seasonal effects
- Player age and career arc
- Consistency volatility

### Backtesting

**Time-Series Cross-Validation**:
- Walk-forward validation (strict temporal ordering)
- Zero data leakage guarantee
- Weekly retraining with cumulative data

**Metrics Tracked**:
- Brier score (calibration quality)
- Log loss (probabilistic accuracy)
- ROI vs. bookmaker odds
- Sharpe ratio
- Hit rate at confidence thresholds (50%, 60%, 70%)

**Analysis**:
- Performance by player skill tier
- Performance by match type
- Drawdown analysis
- Prediction confidence distribution

### Self-Calibration

- **Isotonic Regression**: Maps raw probabilities to true frequencies
- **Reliability Diagrams**: Visualize calibration curves
- **Drift Detection**: Monitor Brier score, trigger retraining on drift
- **Adaptive Weighting**: Adjust ensemble weights based on recent accuracy

### Incremental Learning

- **Match Update Pipeline**: Extract features → Update stats → Retrain → Recalibrate
- **Scheduled Retraining**:
  - Weekly: Full retraining on all historical data
  - Daily: Calibration updates
  - Hourly: Live probability updates

## 📈 Performance Metrics

The system tracks comprehensive metrics:

- **Calibration**: Brier score, reliability diagrams
- **Accuracy**: Log loss, hit rates
- **Profitability**: ROI, Sharpe ratio
- **Robustness**: Drawdown, confidence distribution

## 🔧 Configuration

Edit `config.yaml` to customize:

```yaml
data:
  raw_data_path: "data/raw"
  processed_data_path: "data/processed"
  
models:
  ensemble_members: ["xgboost", "lightgbm", "neural_net", "bayesian_ridge"]
  meta_learner: "stacked_averaging"
  
backtesting:
  validation_strategy: "walk_forward"
  retraining_frequency: "weekly"
  min_training_samples: 500
  
calibration:
  method: "isotonic"
  drift_threshold: 0.05
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t darts-betting-ensemble .

# Run container
docker run -v $(pwd)/data:/app/data darts-betting-ensemble
```

## 📝 Development Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Project scaffolding
- [ ] Data loader for historical matches
- [ ] Feature engineering pipeline
- [ ] Ensemble builder

### Phase 2: Backtesting & Calibration
- [ ] Walk-forward backtest engine
- [ ] Isotonic regression calibration
- [ ] Performance metrics tracking

### Phase 3: Incremental Learning
- [ ] Online model updates
- [ ] Drift detection
- [ ] Adaptive weighting

### Phase 4: Production Deployment
- [ ] REST API for live predictions
- [ ] Monitoring dashboard
- [ ] Docker containerization

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_ensemble_builder.py -v
```

## 📚 Documentation

- [Architecture Design](docs/architecture.md)
- [Feature Engineering Guide](docs/features.md)
- [Backtesting Methodology](docs/backtesting.md)
- [API Reference](docs/api.md)

## 🤝 Contributing

This is a professional betting system. Contributions should maintain production-grade quality:

- Type hints throughout
- Comprehensive error handling
- Unit tests for all modules
- Clear documentation

## 📄 License

MIT License

## ⚠️ Disclaimer

This system is for educational and research purposes. Sports betting involves risk. Always gamble responsibly.
