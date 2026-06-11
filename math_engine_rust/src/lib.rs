use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct KellyPayload {
    pub true_probability: f64,
    pub decimal_odds: f64,
    pub kelly_multiplier: f64,
    pub current_bankroll: f64,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SizingResult {
    pub wager_amount: f64,
    pub is_viable: bool,
    pub log_message: String,
}

pub fn calculate_optimal_wager(payload: KellyPayload) -> SizingResult {
    // Edge calculation: Expected Value = (Probability * Decimal Odds) - 1
    let ev = (payload.true_probability * payload.decimal_odds) - 1.0;

    if ev <= 0.0 {
        return SizingResult {
            wager_amount: 0.0,
            is_viable: false,
            log_message: "Negative Expected Value threshold hit. Aborting sub-execution.".to_string(),
        };
    }

    // Institutional Full Kelly Equation Logic
    // b = Bookmaker Decimal Odds minus 1 (the fractional equivalent)
    // f = ((p * b) - 1) / (b - 1)
    let b = payload.decimal_odds - 1.0;
    let raw_kelly_fraction = ((payload.true_probability * payload.decimal_odds) - 1.0) / b;

    // Apply the React-Dashboard User "Aggression Slider" multiplier
    let adjusted_fraction = raw_kelly_fraction * payload.kelly_multiplier;
    
    // Absolute constraint: Ensure we never mathematically bet more than a 25% max bankroll cap
    let safe_fraction = adjusted_fraction.clamp(0.0, 0.25);
    let exact_wager = payload.current_bankroll * safe_fraction;

    // SECURITY PROTOCOL: Round strictly to the nearest whole dollar integer.
    // Constantly placing wagers for fractional cents flags Sportsbook AI risk models immediately.
    let formatted_wager = exact_wager.floor();

    if formatted_wager < 1.0 {
        return SizingResult {
            wager_amount: 0.0,
            is_viable: false,
            log_message: "Wager amount falls beneath $1 thresholds. Discarding mathematical anomaly.".to_string(),
        };
    }

    SizingResult {
        wager_amount: formatted_wager,
        is_viable: true,
        log_message: format!("[RUST MATRIX] Calculated true robust EV of {:.2}%. Formatted Kelly output generated.", ev * 100.0),
    }
}
