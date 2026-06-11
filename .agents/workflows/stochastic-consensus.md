---
description: Evaluates multiple approaches to find the optimal or high-frequency correct logic
---

# Workflow: Stochastic Consensus
When absolute precision and hallucination elimination is required (like in complex math, critical logic, or intricate debugging), use this workflow.

1. **Information Gathering:** State the exact problem that needs to be solved.
2. **Parallel Generation:** Internally generate 3 to 5 independent, distinct solutions or logical paths for the problem. Do not let one path logically influence the other. Act as if 5 separate models are solving the problem blindly.
3. **Evaluate Consensus (Mode/Median):** 
    - Compare all 5 generated solutions.
    - Identify the logic or answer that appears most frequently (the mode consensus).
    - If solutions wildly differ with numbers, analyze the common denominators or average the approaches to find the safest median solution.
4. **Select Winner:** Ruthlessly discard the outlier solutions. Select the consensus solution as the verified truth.
5. **Execute/Return:** Present the winning solution to the user. Briefly explain the outlier paths that were discarded to prove the robustness of the derivation.
