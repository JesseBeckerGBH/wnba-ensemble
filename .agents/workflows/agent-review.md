---
description: Spawn a sub-review process to rigorously critique and simplify the code
---

# Workflow: Agent Review
When invoked, you must trigger a strict quality assurance and peer review process on the current code or feature before finalizing it.

1. **Context Isolation:** Identify the specific files or logic blocks that were just created or modified.
2. **Simulate Reviewer:** Adopt a completely fresh persona with zero context bias—you are now a ruthless, senior principal engineer performing a code review.
    - *Directives:* Look for security vulnerabilities, unnecessary complexity, performance bottlenecks, and deviations from the rules in `GEMINI.md`. Do not praise the code.
3. **Generate Critiques:** Provide a bulleted list of harsh but fair critiques regarding the implementation.
4. **Address Feedback:** Swap back to your builder persona. Read the critiques. For each valid critique, modify the code immediately to implement the suggested fix.
5. **Final Report:** Present the user with a summary of what was reviewed, what issues were flagged by the "reviewer," and how you ultimately fixed them.
