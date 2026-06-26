"""
trade_logger.py — SQLite trade log and equity tracker.

Tables:
  trades       — every open/close with full details
  equity       — equity snapshot every 30 minutes
  daily_summary — end-of-day P&L per strategy
"""

import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", "trades_sample.db")


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    TEXT NOT NULL,
                strategy     TEXT NOT NULL,
                symbol       TEXT NOT NULL,
                side         TEXT NOT NULL,
                action       TEXT NOT NULL,   -- OPEN or CLOSE
                entry_price  REAL,
                exit_price   REAL,
                sl           REAL,
                tp           REAL,
                lots         REAL,
                pnl          REAL,
                result       TEXT,            -- TP, SL, MANUAL
                position_id  TEXT,
                reason       TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS equity (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                equity    REAL NOT NULL,
                balance   REAL NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                date        TEXT NOT NULL,
                strategy    TEXT NOT NULL,
                trades      INTEGER,
                wins        INTEGER,
                pnl         REAL,
                PRIMARY KEY (date, strategy)
            )
        """)


def log_open(strategy, symbol, side, entry, sl, tp, lots, position_id, reason=""):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as c:
        c.execute("""
            INSERT INTO trades (timestamp, strategy, symbol, side, action,
                                entry_price, sl, tp, lots, position_id, reason)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (ts, strategy, symbol, side, "OPEN", entry, sl, tp, lots, str(position_id), reason))


def log_close(position_id, pnl, result, exit_price=0.0):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as c:
        c.execute("""
            UPDATE trades
            SET exit_price=?, pnl=?, result=?, action='CLOSE',
                timestamp=?
            WHERE position_id=? AND action='OPEN'
        """, (exit_price, pnl, result, ts, str(position_id)))


def log_equity(equity, balance):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with _conn() as c:
        c.execute("INSERT INTO equity (timestamp, equity, balance) VALUES (?,?,?)",
                  (ts, equity, balance))


def daily_pnl():
    """Return today's total P&L."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _conn() as c:
        row = c.execute("""
            SELECT COALESCE(SUM(pnl), 0)
            FROM trades
            WHERE action='CLOSE' AND timestamp LIKE ?
        """, (today + "%",)).fetchone()
    return row[0] if row else 0.0


def open_trade_count():
    with _conn() as c:
        row = c.execute("SELECT COUNT(*) FROM trades WHERE action='OPEN'").fetchone()
    return row[0] if row else 0


def print_summary():
    """Print a quick P&L summary to console."""
    with _conn() as c:
        rows = c.execute("""
            SELECT strategy,
                   COUNT(*) as n,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                   ROUND(SUM(pnl), 2) as pnl
            FROM trades
            WHERE action='CLOSE'
            GROUP BY strategy
            ORDER BY pnl DESC
        """).fetchall()

    print(f"\n  {'Strategy':<12} {'Trades':>7} {'WR%':>6} {'P&L':>9}")
    print(f"  {'-'*12} {'-'*7} {'-'*6} {'-'*9}")
    for r in rows:
        wr = r[2] / r[1] * 100 if r[1] > 0 else 0
        print(f"  {r[0]:<12} {r[1]:>7} {wr:>6.1f} {r[3]:>+9.2f}")
