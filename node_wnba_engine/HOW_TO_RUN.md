# WNBA Betting Model — Quick Start

## One-time setup

```
cd D:\WNBA
py -3.13 -m pip install -r requirements.txt
```

Apply the DB schema:
```
py -3.13 -c "import duckdb; duckdb.connect('db/wnba.duckdb').execute(open('db/schema.sql').read())"
```

---

## Step 1 — Load historical data (do once)

```
py -3.13 data\ingest_wnba.py --seasons 2019 2020 2021 2022 2023 2024 --boxscores
```

This downloads all WNBA game results + box scores back to 2019 via nba_api (free).
Takes ~20 minutes the first time (one API call per game for box scores).

Without box scores (much faster, fewer features):
```
py -3.13 data\ingest_wnba.py --seasons 2019 2020 2021 2022 2023 2024
```

---

## Step 2 — Build features

```
py -3.13 data\build_features.py
```

Computes rolling form, Elo, H2H, efficiency metrics for every game.

---

## Step 3 — Train the model

```
py -3.13 model\stack_train.py
```

Trains two models:
- **Moneyline**: predicts home win probability
- **Totals**: predicts over/under direction

---

## Step 4 — Run the backtest (optional but recommended)

```
py -3.13 backtesting\backtest_walkforward.py
```

Walk-forward validation across all historical seasons.
Results saved to `backtesting/results/`.

---

## Step 5 — Daily workflow (during season, May–October)

```
py -3.13 data\ingest_wnba.py --seasons 2026
py -3.13 data\build_features.py --season 2026
py -3.13 model\stack_train.py
py -3.13 scripts\todays_bets.py --bankroll 1000
```

Or run `scripts\daily_ingest.bat` (set up in Windows Task Scheduler to run at 06:00).

---

## Predict a single game

```
py -3.13 model\predict.py ^
  --home "Las Vegas Aces" ^
  --away "New York Liberty" ^
  --ml-home 1.65 ^
  --ml-away 2.30 ^
  --total-line 162.5 ^
  --over-odds 1.91 ^
  --under-odds 1.91
```

---

## Sentiment monitoring

Reddit (free — needs REDDIT_CLIENT_ID in .env):
```
py -3.13 sentiment\reddit_monitor.py --all-upcoming
```

Twitter/X (free with your X account — needs TWITTER_USERNAME in .env):
```
py -3.13 sentiment\twitter_monitor.py --all-upcoming
```

---

## Surface odds (The Odds API — existing key)

```
py -3.13 scripts\odds_client.py --upcoming
```

---

## MCP server (Claude Code integration)

```
cd D:\WNBA\mcp
npm install
npm run build
```

Add to Claude Code settings (claude_desktop_config.json or .claude/settings.json):
```json
{
  "mcpServers": {
    "wnba": {
      "command": "node",
      "args": ["D:/WNBA/mcp/dist/index.js"]
    }
  }
}
```

Then ask Claude: *"Run the WNBA bet sheet for today"*

---

## 2026 Expansion Teams

Toronto Tempo and Portland Fire join in 2026. They have no historical data.
The model uses league average features for them — predictions will be less reliable
for the first 10-15 games. Reduce stake or skip until they have a track record.
