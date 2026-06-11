mod lib;
use lib::{calculate_optimal_wager, KellyPayload};
use std::env;
use std::process;

fn main() {
    let args: Vec<String> = env::args().collect();
    
    // Validating input matrix length from Polyglot connections
    if args.len() < 5 {
        eprintln!("[!] ERROR: Rust Math Engine parameters failed payload constraint syntax.");
        eprintln!("    Required Context: <true_prob> <dec_odds> <kelly_slider> <bankroll>");
        process::exit(1);
    }

    // Cast parameter boundaries into immutable 64-bit precision floats
    let true_prob: f64 = args[1].parse().unwrap_or(0.0);
    let dec_odds: f64 = args[2].parse().unwrap_or(0.0);
    let kelly_mult: f64 = args[3].parse().unwrap_or(0.0);
    let bankroll: f64 = args[4].parse().unwrap_or(0.0);

    let payload = KellyPayload {
        true_probability: true_prob,
        decimal_odds: dec_odds,
        kelly_multiplier: kelly_mult,
        current_bankroll: bankroll,
    };

    // Synthesize against raw Lib logic
    let result = calculate_optimal_wager(payload);

    // Marshal the return block into serialized JSON to successfully route back to C++ / Python streams
    match serde_json::to_string(&result) {
        Ok(json_output) => println!("{}", json_output),
        Err(e) => {
            eprintln!("[!] CRITICAL SERIALIZATION ERROR IN MATH ENGINE: {}", e);
            process::exit(1);
        }
    }
}
