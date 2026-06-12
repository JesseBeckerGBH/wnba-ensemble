-- ─────────────────────────────────────────────────────────────────────────────
-- WNBA Betting DB — DuckDB schema
-- Run: py -3.13 -c "import duckdb; duckdb.connect('db/wnba.duckdb').execute(open('db/schema.sql').read())"
-- ─────────────────────────────────────────────────────────────────────────────

-- Teams (includes 2026 expansion: Toronto, Portland)
CREATE TABLE IF NOT EXISTS teams (
    team_id      VARCHAR PRIMARY KEY,
    team_name    VARCHAR NOT NULL,
    team_abbrev  VARCHAR,
    city         VARCHAR,
    conference   VARCHAR,  -- 'Eastern' / 'Western'
    joined_year  INTEGER,  -- 2026 for Toronto + Portland
    is_expansion BOOLEAN DEFAULT FALSE
);

-- Players
CREATE TABLE IF NOT EXISTS players (
    player_id   VARCHAR PRIMARY KEY,
    player_name VARCHAR NOT NULL,
    team_id     VARCHAR,
    position    VARCHAR,
    is_active   BOOLEAN DEFAULT TRUE
);

-- Games (all regular season + playoffs)
CREATE TABLE IF NOT EXISTS games (
    game_id       VARCHAR PRIMARY KEY,
    season_year   INTEGER NOT NULL,
    game_date     DATE NOT NULL,
    home_team_id  VARCHAR NOT NULL,
    away_team_id  VARCHAR NOT NULL,
    home_score    INTEGER,
    away_score    INTEGER,
    total_points  INTEGER GENERATED ALWAYS AS (home_score + away_score) VIRTUAL,
    home_win      BOOLEAN,
    is_playoffs   BOOLEAN DEFAULT FALSE,
    status        VARCHAR DEFAULT 'Final'  -- 'Final' / 'Live' / 'Scheduled'
);

CREATE INDEX IF NOT EXISTS idx_games_date    ON games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_season  ON games(season_year);
CREATE INDEX IF NOT EXISTS idx_games_home    ON games(home_team_id);
CREATE INDEX IF NOT EXISTS idx_games_away    ON games(away_team_id);

-- Per-team box score stats per game
CREATE TABLE IF NOT EXISTS team_game_stats (
    game_id     VARCHAR NOT NULL,
    team_id     VARCHAR NOT NULL,
    is_home     BOOLEAN,
    pts         INTEGER,
    fgm         INTEGER, fga INTEGER, fg_pct  REAL,
    fg3m        INTEGER, fg3a INTEGER, fg3_pct REAL,
    ftm         INTEGER, fta INTEGER, ft_pct  REAL,
    oreb        INTEGER, dreb INTEGER, reb     INTEGER,
    ast         INTEGER, stl INTEGER,  blk     INTEGER,
    tov         INTEGER, pf  INTEGER,
    plus_minus  REAL,
    PRIMARY KEY (game_id, team_id)
);

-- Per-player box score stats per game
CREATE TABLE IF NOT EXISTS player_game_stats (
    game_id     VARCHAR NOT NULL,
    player_id   VARCHAR NOT NULL,
    team_id     VARCHAR NOT NULL,
    min_played  REAL,
    pts         INTEGER,
    reb         INTEGER, ast INTEGER, stl INTEGER, blk INTEGER,
    tov         INTEGER,
    fg_pct      REAL, fg3_pct REAL, ft_pct REAL,
    plus_minus  REAL,
    PRIMARY KEY (game_id, player_id)
);

-- Odds (moneyline + totals)
CREATE TABLE IF NOT EXISTS odds (
    game_id       VARCHAR NOT NULL,
    source        VARCHAR NOT NULL,   -- 'theodds' / 'betsapi'
    bookmaker     VARCHAR,
    home_ml       REAL,               -- decimal odds, home win
    away_ml       REAL,               -- decimal odds, away win
    total_line    REAL,               -- e.g. 162.5
    over_odds     REAL,               -- decimal odds, over
    under_odds    REAL,               -- decimal odds, under
    fetched_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (game_id, source, bookmaker)
);

-- Sentiment snapshots (pre-game)
CREATE TABLE IF NOT EXISTS sentiment (
    id            VARCHAR PRIMARY KEY,  -- uuid
    game_id       VARCHAR NOT NULL,
    team_id       VARCHAR NOT NULL,
    source        VARCHAR NOT NULL,    -- 'reddit' / 'twitter'
    sentiment_score REAL,              -- -1.0 (very negative) to +1.0 (very positive)
    post_count    INTEGER,
    snapshot_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Precomputed ML features per game per team
CREATE TABLE IF NOT EXISTS game_features (
    game_id              VARCHAR NOT NULL,
    team_id              VARCHAR NOT NULL,
    opp_team_id          VARCHAR,
    game_date            DATE,
    season_year          INTEGER,
    is_home              BOOLEAN,
    -- rolling form (last 10 games)
    rolling_win_rate     REAL,
    rolling_pts_for      REAL,
    rolling_pts_against  REAL,
    rolling_net_pts      REAL,
    rolling_fg_pct       REAL,
    rolling_fg3_pct      REAL,
    rolling_ft_pct       REAL,
    rolling_tov_rate     REAL,
    rolling_reb_margin   REAL,
    -- pace / efficiency
    pace                 REAL,  -- possessions per 40 min
    off_rating           REAL,  -- pts per 100 possessions
    def_rating           REAL,  -- opp pts per 100 possessions
    net_rating           REAL,  -- off - def
    -- rest
    days_rest            INTEGER,
    b2b                  BOOLEAN,  -- back-to-back game
    -- Elo
    elo_pre              REAL,
    opp_elo_pre          REAL,
    elo_diff             REAL,
    -- H2H (season + trailing 2 years)
    h2h_win_rate         REAL,
    h2h_avg_total        REAL,
    h2h_meetings         INTEGER,
    -- sentiment (most recent snapshot before game)
    sentiment_score      REAL,
    -- target labels (filled after game)
    won_moneyline        BOOLEAN,  -- did this team win?
    total_over           BOOLEAN,  -- did combined score exceed line?
    total_line           REAL,
    PRIMARY KEY (game_id, team_id)
);

-- Model predictions
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id    VARCHAR PRIMARY KEY,
    game_id          VARCHAR NOT NULL,
    predicted_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version    VARCHAR,
    home_win_prob    REAL,
    away_win_prob    REAL,
    ml_edge_home     REAL,
    ml_edge_away     REAL,
    predicted_total  REAL,
    total_edge_over  REAL,
    total_edge_under REAL,
    home_ml_odds     REAL,
    away_ml_odds     REAL,
    total_line       REAL,
    over_odds        REAL,
    under_odds       REAL
);

-- Walk-forward backtest results
CREATE TABLE IF NOT EXISTS backtest_results (
    run_id            VARCHAR PRIMARY KEY,
    model_version     VARCHAR,
    window_start      DATE,
    window_end        DATE,
    train_games       INTEGER,
    test_games        INTEGER,
    -- moneyline backtest
    ml_total_bets     INTEGER,
    ml_wins           INTEGER,
    ml_win_rate       REAL,
    ml_roi            REAL,
    ml_auc            REAL,
    ml_auc_gate_fired BOOLEAN,
    -- totals backtest
    tot_total_bets    INTEGER,
    tot_wins          INTEGER,
    tot_win_rate      REAL,
    tot_roi           REAL,
    tot_auc           REAL,
    tot_auc_gate_fired BOOLEAN,
    -- combined
    total_roi         REAL,
    max_drawdown      REAL,
    sharpe_ratio      REAL,
    initial_bankroll  REAL,
    final_bankroll    REAL,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Views ─────────────────────────────────────────────────────────────────────

-- Latest odds per game (best available moneyline)
CREATE OR REPLACE VIEW best_odds AS
SELECT
    game_id,
    MAX(home_ml)    AS best_home_ml,
    MAX(away_ml)    AS best_away_ml,
    AVG(total_line) AS avg_total_line,
    MAX(over_odds)  AS best_over_odds,
    MAX(under_odds) AS best_under_odds,
    COUNT(*)        AS bookmaker_count
FROM odds
GROUP BY game_id;

-- Season standings with Elo
CREATE OR REPLACE VIEW team_season_summary AS
SELECT
    g.season_year,
    t.team_id,
    t.team_name,
    COUNT(*)                                                     AS games_played,
    SUM(CASE WHEN g.home_team_id = t.team_id AND g.home_win THEN 1
             WHEN g.away_team_id = t.team_id AND NOT g.home_win THEN 1
             ELSE 0 END)                                         AS wins,
    ROUND(AVG(tgs.pts), 1)                                       AS avg_pts_for,
    ROUND(AVG(CASE WHEN tgs2.pts IS NOT NULL THEN tgs2.pts END), 1) AS avg_pts_against
FROM games g
JOIN teams t ON t.team_id IN (g.home_team_id, g.away_team_id)
JOIN team_game_stats tgs ON tgs.game_id = g.game_id AND tgs.team_id = t.team_id
LEFT JOIN team_game_stats tgs2
    ON tgs2.game_id = g.game_id
   AND tgs2.team_id != t.team_id
WHERE g.home_score IS NOT NULL
GROUP BY g.season_year, t.team_id, t.team_name;
