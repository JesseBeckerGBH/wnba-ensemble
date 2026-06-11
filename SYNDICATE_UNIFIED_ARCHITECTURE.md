# UNIFIED SYNDICATE ARCHITECTURE (2026 Reference Blueprint)

This document represents the assimilated architectural reference for a high-tier algorithmic sports betting syndicate.

## 1. Syndicate Operations & The Polyglot Org Chart
Operating optimally requires a **Polyglot Microservice Architecture** deployed to Proxmox VE.

| Subsystem | Language | Responsibility |
| :--- | :--- | :--- |
| **Ingestion Engine** | `Go` | Parses the TimescaleDB/Kafka firehose asynchronously with extreme concurrency to beat the Latency Bottleneck. |
| **Statistical Mathematics** | `Rust` | Solves massive EV triangulations and probability trees efficiently with strict memory safety boundaries. |
| **Execution Layer** | `C++` | Directly interfaces with Sportsbook FIX APIs (e.g. Pinnacle) to snipe trades in sub-millisecond execution times. |
| **Machine Engines (XGBoost)** | `Python / Julia` | Executes the Heavy Machine Learning Model Ensembles and AI Consensus loops. |

## 2. In-Memory Subsystems vs DB Caching
To accommodate the execution speeds of the Rust and C++ layers, we replace standard I/O intensive disk caches with aggressive **In-Memory Dictionaries**. If the Proxmox RAM pool allows it, memory is strictly preserved at runtime ensuring API actions execute with absolute zero database lookup lag.

## 3. The Three-Layer Sequence
### Layer 1: Pre-Match Base Model (Probability)
Predict the absolute base state outcome via XGBoost Ensembles.

### Layer 2: Live Market Microstructure (The Options Model)
In-play pricing is driven entirely by Liquidity/Exposure and Sharp Sentiment ($\Delta$ Odds / $\Delta$ Time). The `node_consensus` triggers heavily off algorithmic residuals (Opening vs Closing variances).

### Layer 3: Risk Overlay (The Full Kelly)
*   **Methodology:** Standard Full Kelly Criterion.
*   **Protocol:** Playing strictly for explosive, maximum exponential geometric growth based on true edge, un-capped by fractional safety logic.
*   **Formula:** $f^* = (bp - q) / b$ 

---

## 4. Operational Bottleneck Mitigation
*   **Soft Book Limits:** Route via proper API-facing global exchanges utilizing C++ subroutines.
*   **Model Degradation:** Automated Julia/Python retraining hooks parsing the `ingestion_go` Kafka stream.
