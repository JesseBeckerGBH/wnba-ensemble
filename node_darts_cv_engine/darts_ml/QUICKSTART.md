# Darts Betting Ensemble - Quick Start Guide

## Installation

```powershell
# Navigate to project directory
cd C:\Users\Home\.gemini\antigravity\scratch\darts-betting-ensemble

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Run the Full Pipeline

This will generate sample data, engineer features, train the ensemble, and evaluate:

```powershell
python main.py
```

Expected output:
- Sample data generated (2000 matches)
- Features engineered (40+ features per match)
- 4 models trained (XGBoost, LightGBM, Neural Network, Bayesian Ridge)
- Ensemble weights optimized
- Performance metrics on test set
- Model saved to `models/ensemble/`

### 2. Use the CLI

```powershell
# Train the ensemble
python cli.py train

# Monitor current model
python cli.py monitor

# Predict a match (placeholder - needs feature extraction)
python cli.py predict --player1 "Michael van Gerwen" --player2 "Peter Wright"
```

## Project Status

### ✅ Completed (Phases 1-2)

- **Data Layer**: Web scrapers, Kaggle integration, feature engineering
- **Model Layer**: 4 models + ensemble with adaptive weighting
- **Infrastructure**: Configuration, logging, ETL pipeline

### 🚧 In Progress (Phase 3)

- Backtesting engine with walk-forward validation
- Calibration with isotonic regression
- Drift detection

### 📋 Planned (Phases 4-5)

- Incremental learning
- REST API
- Docker deployment

## Next Steps

1. **Test the pipeline**: Run `python main.py` to verify everything works
2. **Review logs**: Check `logs/main.log` for detailed execution logs
3. **Inspect data**: Look at `data/processed/features.csv` to see engineered features
4. **Check models**: Saved models are in `models/ensemble/`

## Troubleshooting

**Missing dependencies?**
```powershell
pip install -r requirements.txt
```

**Import errors?**
Make sure you're in the project root directory when running commands.

**Need real data?**
Replace the sample data generator with actual scrapers or Kaggle datasets in `src/data/darts_data_loader.py`.
