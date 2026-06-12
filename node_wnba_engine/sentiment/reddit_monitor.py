#!/usr/bin/env python3
"""
D:/WNBA/sentiment/reddit_monitor.py

Reddit sentiment monitor for WNBA teams.

Scrapes r/WNBA + team subreddits for posts mentioning players/teams
in the 48 hours before a game. Computes a weighted sentiment score
per team and writes to the sentiment table.

Edge thesis: player motivation signals, team drama, injury rumours,
             commissioner/player conflict narrative.

Usage:
    py -3.13 sentiment/reddit_monitor.py --game-id 0022400123
    py -3.13 sentiment/reddit_monitor.py --all-upcoming   # enrich all upcoming games
    py -3.13 sentiment/reddit_monitor.py --test           # print top posts, don't write

Requires: REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET in .env
Create a free app at: https://www.reddit.com/prefs/apps
"""

from __future__ import annotations

import argparse
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

# Reddit subreddits to monitor
SUBREDDITS = [
    "WNBA",
    "WNBALive",
    "sportsbook",
    "sportsbetting",
    # Team subreddits (active ones)
    "NYLiberty",
    "LasVegasAces",
    "SeattleStorm",
    "MinnesotaLynx",
    "ChicagoSky",
    "PhoenixMercury",
    "ConnecticutSun",
    "AtlantaDream",
]

# Keywords that indicate strong positive/negative sentiment
POSITIVE_SIGNALS = [
    "hot", "on fire", "dominant", "motivated", "healthy", "locked in",
    "back", "return", "healthy scratch off", "best in class", "mvp",
    "undervalued", "value", "disrespected", "prove", "revenge",
]
NEGATIVE_SIGNALS = [
    "injured", "out", "questionable", "limited", "drama", "beef",
    "suspended", "benched", "struggling", "slump", "conflict",
    "unhappy", "trade request", "distraction", "fired", "quit",
]
# WNBA-specific drama signals (2025-2026 context)
DRAMA_SIGNALS = [
    "commissioner", "cathy engelbert", "players association", "cba",
    "expansion", "toronto", "portland", "relocation", "ownership",
    "broadcast deal", "abc", "ion", "amazon",
    "pay equity", "maternity", "charter flight",
]


def get_reddit_client():
    client_id     = os.getenv("REDDIT_CLIENT_ID", "")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET", "")
    user_agent    = os.getenv("REDDIT_USER_AGENT", "wnba-sentiment/1.0")

    if not client_id or not client_secret:
        raise RuntimeError(
            "REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET not set in .env\n"
            "Create a free app at https://www.reddit.com/prefs/apps"
        )

    try:
        import praw
    except ImportError:
        raise ImportError("praw not installed. Run: py -3.13 -m pip install praw")

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def score_text(text: str) -> float:
    """
    Simple lexicon-based sentiment score: -1.0 to +1.0.
    Weighted: drama signals add more variance (±0.5 per hit),
    positive/negative signals add ±0.3.
    """
    text_l = text.lower()
    score = 0.0
    hits  = 0

    for kw in POSITIVE_SIGNALS:
        if kw in text_l:
            score += 0.3
            hits  += 1
    for kw in NEGATIVE_SIGNALS:
        if kw in text_l:
            score -= 0.3
            hits  += 1
    for kw in DRAMA_SIGNALS:
        if kw in text_l:
            score -= 0.2  # drama tends to be a negative signal for the team/league
            hits  += 1

    return max(-1.0, min(1.0, score / max(hits, 1)))


def fetch_team_sentiment(
    reddit,
    team_name: str,
    team_abbrev: str,
    hours_back: int = 48,
    limit: int = 100,
) -> tuple[float, int]:
    """
    Fetch recent posts mentioning a team from monitored subreddits.
    Returns (avg_sentiment_score, post_count).
    """
    query   = f'"{team_name}" OR "{team_abbrev}"'
    cutoff  = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    scores  = []

    for sub_name in SUBREDDITS:
        try:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.search(query, sort="new", time_filter="week", limit=limit):
                post_time = datetime.fromtimestamp(post.created_utc, timezone.utc)
                if post_time < cutoff:
                    continue
                text  = f"{post.title} {post.selftext}"
                score = score_text(text)
                # Weight by post score (upvotes)
                weight = max(1, min(post.score, 50))
                scores.extend([score] * weight)
        except Exception:
            pass

    if not scores:
        return 0.0, 0

    import statistics
    return statistics.mean(scores), len(scores)


def write_sentiment(
    conn: duckdb.DuckDBPyConnection,
    game_id: str,
    team_id: str,
    score: float,
    post_count: int,
    source: str = "reddit",
):
    conn.execute(
        """
        INSERT OR REPLACE INTO sentiment
            (id, game_id, team_id, source, sentiment_score, post_count, snapshot_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        [str(uuid.uuid4()), game_id, team_id, source, score, post_count],
    )


def enrich_upcoming(conn, reddit, dry_run: bool = False) -> int:
    """Enrich all upcoming games scheduled within the next 7 days."""
    upcoming = conn.execute("""
        SELECT g.game_id, g.game_date,
               th.team_id AS home_id, th.team_name AS home_name, th.team_abbrev AS home_abbr,
               ta.team_id AS away_id, ta.team_name AS away_name, ta.team_abbrev AS away_abbr
        FROM games g
        JOIN teams th ON th.team_id = g.home_team_id
        JOIN teams ta ON ta.team_id = g.away_team_id
        WHERE g.status = 'Scheduled'
          AND g.game_date BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '7 days')
    """).df()

    enriched = 0
    for _, row in upcoming.iterrows():
        for team_id, name, abbr in [
            (row.home_id, row.home_name, row.home_abbr),
            (row.away_id, row.away_name, row.away_abbr),
        ]:
            score, count = fetch_team_sentiment(reddit, name, abbr)
            print(f"  {name:30s} sentiment={score:+.3f}  posts={count}")
            if not dry_run:
                write_sentiment(conn, row.game_id, team_id, score, count)
        enriched += 1

    return enriched


def main():
    p = argparse.ArgumentParser(description="WNBA Reddit sentiment monitor")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--game-id",       help="Enrich a specific game by ID")
    g.add_argument("--all-upcoming",  action="store_true",
                   help="Enrich all upcoming games (next 7 days)")
    g.add_argument("--test",          action="store_true",
                   help="Test mode: score a team without writing to DB")
    p.add_argument("--team",          help="Team name for --test mode")
    args = p.parse_args()

    reddit = get_reddit_client()
    conn   = duckdb.connect(DB_PATH)

    if args.test:
        team = args.team or "Las Vegas Aces"
        print(f"\nTest sentiment for: {team}")
        score, count = fetch_team_sentiment(reddit, team, "")
        print(f"  Score: {score:+.3f}   Posts sampled: {count}")

    elif args.all_upcoming:
        print("\n[reddit] Enriching all upcoming games...")
        n = enrich_upcoming(conn, reddit)
        print(f"  Enriched {n} games")
        conn.commit()

    elif args.game_id:
        game = conn.execute("""
            SELECT g.home_team_id, g.away_team_id,
                   th.team_name, th.team_abbrev,
                   ta.team_name, ta.team_abbrev
            FROM games g
            JOIN teams th ON th.team_id = g.home_team_id
            JOIN teams ta ON ta.team_id = g.away_team_id
            WHERE g.game_id = ?
        """, [args.game_id]).fetchone()

        if not game:
            print(f"Game {args.game_id} not found")
        else:
            home_id, away_id, hname, habbr, aname, aabbr = game
            for tid, name, abbr in [
                (home_id, hname, habbr),
                (away_id, aname, aabbr),
            ]:
                score, count = fetch_team_sentiment(reddit, name, abbr)
                print(f"  {name:30s}  sentiment={score:+.3f}  posts={count}")
                write_sentiment(conn, args.game_id, tid, score, count)
            conn.commit()
            print("  Saved to DB")

    conn.close()


if __name__ == "__main__":
    main()
