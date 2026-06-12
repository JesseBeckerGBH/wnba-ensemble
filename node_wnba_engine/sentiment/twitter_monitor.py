#!/usr/bin/env python3
"""
D:/WNBA/sentiment/twitter_monitor.py

Twitter/X sentiment monitor for WNBA teams using twscrape.
No API key needed — uses your X account credentials.

Edge signals: player drama, injury tweets, motivation indicators,
              commissioner conflict, expansion team hype/backlash.

Setup:
    py -3.13 -m pip install twscrape
    py -3.13 sentiment/twitter_monitor.py --add-account
    Then set TWITTER_USERNAME / TWITTER_PASSWORD in .env

Usage:
    py -3.13 sentiment/twitter_monitor.py --all-upcoming
    py -3.13 sentiment/twitter_monitor.py --team "Las Vegas Aces" --test
"""

from __future__ import annotations

import argparse
import asyncio
import os
import pathlib
import sys
import uuid
from datetime import datetime, timedelta, timezone

import duckdb
from dotenv import load_dotenv

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
load_dotenv(str(_ROOT / ".env"))

DB_PATH = os.getenv("WNBA_DB_PATH", str(_ROOT / "db" / "wnba.duckdb"))

POSITIVE_SIGNALS = [
    "healthy", "back", "return", "locked in", "hot", "on fire",
    "motivated", "revenge", "prove", "disrespected", "ready",
    "dominant", "unstoppable", "mvp", "elite",
]
NEGATIVE_SIGNALS = [
    "injured", "out", "questionable", "doubtful", "limited",
    "drama", "beef", "suspended", "benched", "struggling", "slump",
    "trade", "unhappy", "distraction", "conflict",
]
DRAMA_SIGNALS = [
    "commissioner", "cathy engelbert", "strike", "boycott", "cba",
    "expansion", "toronto", "portland", "broadcast", "amazon",
    "pay equity", "charter", "discrimination",
]


def score_text(text: str) -> float:
    text_l = text.lower()
    score = 0.0
    hits = 0
    for kw in POSITIVE_SIGNALS:
        if kw in text_l:
            score += 0.3; hits += 1
    for kw in NEGATIVE_SIGNALS:
        if kw in text_l:
            score -= 0.3; hits += 1
    for kw in DRAMA_SIGNALS:
        if kw in text_l:
            score -= 0.2; hits += 1
    return max(-1.0, min(1.0, score / max(hits, 1)))


async def get_scraper():
    try:
        from twscrape import API
    except ImportError:
        raise ImportError(
            "twscrape not installed. Run: py -3.13 -m pip install twscrape"
        )
    api = API()
    username = os.getenv("TWITTER_USERNAME", "")
    password = os.getenv("TWITTER_PASSWORD", "")
    email    = os.getenv("TWITTER_EMAIL", "")

    if not username or not password:
        raise RuntimeError(
            "TWITTER_USERNAME / TWITTER_PASSWORD not set in .env\n"
            "Set these to an X account you own."
        )

    # Add account if not already present
    accounts = await api.pool.get_all()
    if not any(a.username.lower() == username.lower() for a in accounts):
        await api.pool.add_account(username, password, email, "")
        await api.pool.login_all()

    return api


async def fetch_team_tweets(
    api,
    team_name: str,
    team_abbrev: str,
    hours_back: int = 48,
    limit: int = 200,
) -> tuple[float, int]:
    """
    Fetch recent tweets about a team.
    Returns (avg_sentiment_score, tweet_count).
    """
    query   = f'("{team_name}" OR "#{team_abbrev}" OR "#WNBA") lang:en'
    cutoff  = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    scores  = []

    async for tweet in api.search(query, limit=limit):
        ts = tweet.date
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts < cutoff:
            break
        text  = tweet.rawContent or ""
        score = score_text(text)
        # Weight by engagement (likes + retweets, capped)
        weight = max(1, min((tweet.likeCount or 0) + (tweet.retweetCount or 0), 100))
        scores.extend([score] * (weight // 10 + 1))

    if not scores:
        return 0.0, 0

    import statistics
    return statistics.mean(scores), len(scores)


def write_sentiment(conn, game_id, team_id, score, count, source="twitter"):
    conn.execute(
        """
        INSERT OR REPLACE INTO sentiment
            (id, game_id, team_id, source, sentiment_score, post_count, snapshot_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        [str(uuid.uuid4()), game_id, team_id, source, score, count],
    )


async def run(args):
    api  = await get_scraper()
    conn = duckdb.connect(DB_PATH)

    if args.test:
        name = args.team or "Las Vegas Aces"
        print(f"\nTest Twitter sentiment for: {name}")
        score, count = await fetch_team_tweets(api, name, "")
        print(f"  Score: {score:+.3f}   Tweets sampled: {count}")
        conn.close()
        return

    if args.all_upcoming:
        upcoming = conn.execute("""
            SELECT g.game_id,
                   th.team_id, th.team_name, th.team_abbrev,
                   ta.team_id, ta.team_name, ta.team_abbrev
            FROM games g
            JOIN teams th ON th.team_id = g.home_team_id
            JOIN teams ta ON ta.team_id = g.away_team_id
            WHERE g.status = 'Scheduled'
              AND g.game_date BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '7 days')
        """).df()

        for _, row in upcoming.iterrows():
            for tid, name, abbr in [
                (row.team_id,   row.team_name,   row.team_abbrev),
                (row.team_id_1, row.team_name_1, row.team_abbrev_1),
            ]:
                score, count = await fetch_team_tweets(api, name, abbr)
                print(f"  {name:30s}  sentiment={score:+.3f}  tweets={count}")
                write_sentiment(conn, row.game_id, tid, score, count)

        conn.commit()
        print(f"  Enriched {len(upcoming)} games")

    conn.close()


def main():
    p = argparse.ArgumentParser(description="WNBA Twitter/X sentiment monitor")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--all-upcoming",  action="store_true")
    g.add_argument("--test",          action="store_true")
    g.add_argument("--add-account",   action="store_true",
                   help="Re-authenticate X account")
    p.add_argument("--team", help="Team name for --test mode")
    args = p.parse_args()

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
