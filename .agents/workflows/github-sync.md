---
description: Automated GitHub Issue Tracker
---
# GitHub Action Synchronization Workflow

When I have officially mapped out a sequence of code as completed (usually corresponding with updating `task.md` or outputting `walkthrough.md` for a specific module/phase), I MUST automatically invoke this workflow to bridge my local actions up to the active remote GitHub repository.

1. Ensure the user has accurately loaded `GITHUB_ACCESS_TOKEN` and `GITHUB_TARGET_REPO` into their `.env` file environment. 
2. Formulate an actionable, clean Title representing the specific software module that was successfully completed (e.g. `[Automation] Scaffolded Polyglot Ingestion Hooks`).
3. Formulate a 2-3 sentence markdown strings outlining entirely what files were just adjusted or modified.
// turbo
4. Run the python bridge immediately using `python C:\Users\Home\.gemini\antigravity\scratch\scripts\github_issue_logger.py "<TITLE>" "<BODY>"`
