use clap::Parser;
use serde::Serialize;
use serde_json::json;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    #[arg(long)]
    prob: f64,
    #[arg(long)]
    odds: f64,
    #[arg(long)]
    bankroll: f64,
}

#[derive(Serialize)]
struct MathResult {
    optimal_wager: f64,
    is_safe: bool,
    edge: f64,
}

fn main() {
    let args = Args::parse();
    
    // Decimal odds -> Implied probability
    let implied_prob = 1.0 / args.odds;
    let edge = args.prob - implied_prob;
    
    let mut optimal_wager = 0.0;
    let mut is_safe = false;

    // Fractional Kelly (1/4 Kelly for volatility management as per Perplexity logic)
    if edge > 0.04 { // 4% threshold minimum
        let b = args.odds - 1.0;
        let p = args.prob;
        let q = 1.0 - p;
        
        let full_kelly_fraction = (b * p - q) / b;
        let quarter_kelly = full_kelly_fraction * 0.25;
        
        if quarter_kelly > 0.0 {
            // Calculate absolute dollar amount and round down strictly (risk management)
            optimal_wager = (quarter_kelly * args.bankroll).floor();
            is_safe = true;
        }
    }
    
    let result = MathResult {
        optimal_wager,
        is_safe,
        edge,
    };
    
    println!("{}", json!(result));
}
