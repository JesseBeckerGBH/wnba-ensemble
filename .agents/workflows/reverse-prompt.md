---
description: Ask 5 clarifying questions before starting any build to surface deep preferences
---

# Workflow: Reverse Prompting
When the user invokes this workflow, DO NOT immediately execute their initial request. Instead, rigorously follow these steps:

1. **Analyze the Request:** Read the user's original goal and understand the domain. Identify ambiguities, edge cases, and missing context regarding constraints, aesthetics, performance considerations, and user experience.
2. **Generate 5 Questions:** Formulate exactly 5 highly specific, non-obvious clarifying questions to ask the user. Questions should realistically cover:
    - Overall architecture or technology constraints
    - Specific feature edge cases
    - Design, UX, or aesthetic preferences
    - Success criteria / Definition of Done
    - Performance or scaling concerns
3. **Wait for Answers:** Present the 5 questions to the user and STOP. Do not proceed with coding until the user has directly answered.
4. **Synthesize & Execute:** Once the user answers, combine their original request with their detailed answers. Summarize the complete "Prompt Contract" internally, and then build the solution.
