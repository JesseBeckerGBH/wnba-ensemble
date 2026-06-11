"""
Command-line interface for darts betting ensemble.

Provides commands for training, prediction, backtesting, and monitoring.
"""

import click
from rich.console import Console
from rich.table import Table
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.ensemble_builder import EnsembleBuilder
from src.data.etl_pipeline import ETLPipeline
from src.utils.config import get_config
from src.utils.logger import setup_logger, get_logger

console = Console()


@click.group()
def cli():
    """Darts Betting Ensemble - Command Line Interface"""
    setup_logger(log_level="INFO")


@cli.command()
@click.option('--force-reload', is_flag=True, help='Force reload data from sources')
def train(force_reload):
    """Train the ensemble model."""
    console.print("\n[bold blue]Training Ensemble Model[/bold blue]\n")
    
    logger = get_logger(__name__)
    config = get_config()
    
    # Load data
    console.print("Loading data...")
    etl = ETLPipeline()
    features_df = etl.run_full_pipeline(force_reload=force_reload)
    
    # Split data
    train_df, test_df = etl.get_train_test_split(features_df, test_size=0.2)
    X_train, y_train = etl.prepare_model_inputs(train_df)
    X_test, y_test = etl.prepare_model_inputs(test_df)
    
    # Create validation set
    val_split = int(len(X_train) * 0.8)
    X_val = X_train.iloc[val_split:]
    y_val = y_train.iloc[val_split:]
    X_train = X_train.iloc[:val_split]
    y_train = y_train.iloc[:val_split]
    
    # Train ensemble
    console.print("Training ensemble...")
    ensemble = EnsembleBuilder(config)
    ensemble.fit(X_train, y_train, X_val, y_val)
    
    # Update weights
    ensemble.update_weights(X_val, y_val)
    
    # Save
    models_path = config.models_path / "ensemble"
    ensemble.save(str(models_path))
    
    console.print(f"\n[green]✓[/green] Ensemble trained and saved to {models_path}")
    console.print(f"\nWeights: {ensemble}")


@cli.command()
@click.option('--player1', required=True, help='First player name')
@click.option('--player2', required=True, help='Second player name')
@click.option('--tournament', default='Unknown', help='Tournament name')
def predict(player1, player2, tournament):
    """Predict match probability."""
    console.print(f"\n[bold blue]Predicting: {player1} vs {player2}[/bold blue]\n")
    
    config = get_config()
    models_path = config.models_path / "ensemble"
    
    if not models_path.exists():
        console.print("[red]Error:[/red] No trained model found. Run 'train' first.")
        return
    
    # Load ensemble
    ensemble = EnsembleBuilder.load(str(models_path))
    
    # TODO: Feature extraction for live match
    # For now, show placeholder
    console.print("[yellow]Note:[/yellow] Live feature extraction not yet implemented.")
    console.print("This would extract features for the specified players and predict probability.")
    
    console.print(f"\nEnsemble loaded: {ensemble}")


@cli.command()
def monitor():
    """Show current model performance."""
    console.print("\n[bold blue]Model Performance Monitor[/bold blue]\n")
    
    config = get_config()
    models_path = config.models_path / "ensemble"
    
    if not models_path.exists():
        console.print("[red]Error:[/red] No trained model found.")
        return
    
    # Load ensemble
    ensemble = EnsembleBuilder.load(str(models_path))
    
    # Display weights
    table = Table(title="Ensemble Weights")
    table.add_column("Model", style="cyan")
    table.add_column("Weight", style="green")
    
    model_names = ['XGBoost', 'LightGBM', 'Neural Network', 'Bayesian Ridge']
    for name, weight in zip(model_names, ensemble.weights):
        table.add_row(name, f"{weight:.3f}")
    
    console.print(table)


@cli.command()
def backtest():
    """Run backtesting (placeholder)."""
    console.print("\n[bold blue]Backtesting[/bold blue]\n")
    console.print("[yellow]Backtesting engine coming in Phase 3![/yellow]")
    console.print("This will run walk-forward validation and generate performance reports.")


@cli.command()
def calibrate():
    """Calibrate model probabilities (placeholder)."""
    console.print("\n[bold blue]Calibration[/bold blue]\n")
    console.print("[yellow]Calibration engine coming in Phase 3![/yellow]")
    console.print("This will apply isotonic regression to improve probability calibration.")


if __name__ == "__main__":
    cli()
