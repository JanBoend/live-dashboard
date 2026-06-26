-- schema.sql — Trade log and equity tracker schema

CREATE TABLE IF NOT EXISTS trades (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT NOT NULL,
    strategy     TEXT NOT NULL,
    symbol       TEXT NOT NULL,
    side         TEXT NOT NULL,       -- 'long' or 'short'
    action       TEXT NOT NULL,       -- 'OPEN' or 'CLOSE'
    entry_price  REAL,
    exit_price   REAL,
    sl           REAL,
    tp           REAL,
    lots         REAL,
    pnl          REAL,
    result       TEXT,                -- 'TP', 'SL', 'MANUAL'
    position_id  TEXT,
    reason       TEXT
);

CREATE TABLE IF NOT EXISTS equity (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    equity    REAL NOT NULL,
    balance   REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_summary (
    date        TEXT NOT NULL,
    strategy    TEXT NOT NULL,
    trades      INTEGER,
    wins        INTEGER,
    pnl         REAL,
    PRIMARY KEY (date, strategy)
);
