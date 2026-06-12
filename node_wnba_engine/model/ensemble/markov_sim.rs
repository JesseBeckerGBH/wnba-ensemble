// markov_sim.rs
// Executive Layer: Fast Markov Chain simulations in Rust
// Compile with: rustc -O markov_sim.rs

use rand::Rng;

// A simple Markov simulation function tracking possession outcomes (0,1,2,3 pts)
fn markov_sim(trans: &[[f64; 4]; 4], n_poss: usize, start: usize) -> i32 {
    let mut rng = rand::thread_rng();
    let mut state = start;
    let mut score = 0;
    
    for _ in 0..n_poss {
        let probs = trans[state];
        
        // Build cumulative probabilities for selection
        let mut cum: Vec<f64> = Vec::with_capacity(4);
        let mut sum = 0.0;
        for &p in probs.iter() {
            sum += p;
            cum.push(sum);
        }
        
        let r = rng.gen::<f64>();
        
        // Find next state based on random draw
        state = cum.iter().position(|&c| r < c).unwrap_or(3); // fallback to 3 on float imprecision
        score += state as i32;
    }
    score
}

fn main() {
    // Default transition matrix
    // rows: current possession outcome (0 to 3)
    // cols: next possession outcome probabilities
    let trans_matrix: [[f64; 4]; 4] = [
        [0.45, 0.10, 0.35, 0.10], // From 0
        [0.40, 0.15, 0.35, 0.10], // From 1
        [0.35, 0.15, 0.40, 0.10], // From 2
        [0.30, 0.15, 0.40, 0.15]  // From 3
    ];

    let n_sims = 100_000;
    let target = 160.5;
    let mut over_count = 0;
    
    println!("Running {} Markov Simulations in Rust...", n_sims);
    
    // Simulating home and away possessions (~80 each for WNBA)
    for _ in 0..n_sims {
        let home_score = markov_sim(&trans_matrix, 80, 0);
        let away_score = markov_sim(&trans_matrix, 80, 0);
        
        if (home_score + away_score) as f64 > target {
            over_count += 1;
        }
    }
    
    let prob = (over_count as f64) / (n_sims as f64);
    println!("Probability over {}: {:.2}%", target, prob * 100.0);
}
