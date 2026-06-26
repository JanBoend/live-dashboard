"""dashboard/app.py — Read-only trading dashboard on port 5050.

Reads trades_sample.db (or DB_PATH env var). Never writes.
Secured with HTTP Basic Auth. Auto-refresh every 30s via JavaScript meta tag.

Run: python dashboard/app.py
"""

import os
import sqlite3
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Flask, render_template, request, Response

app = Flask(__name__)

# ── Config ─────────────────────────────────────────────────────────────────────
DB_PATH        = os.environ.get("DB_PATH", "trades_sample.db")
DASH_USER      = os.environ.get("DASH_USER", "admin")
DASH_PASSWORD  = os.environ.get("DASH_PASSWORD", "changeme")
PORT           = int(os.environ.get("DASH_PORT", 5050))

STRATEGIES = ["fvg", "orb", "amd", "eu_amd", "eu_orb"]


# ── Auth ───────────────────────────────────────────────────────────────────────

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != DASH_USER or auth.password != DASH_PASSWORD:
            return Response(
                "Login required", 401,
                {"WWW-Authenticate": 'Basic realm="Trading Dashboard"'}
            )
        return f(*args, **kwargs)
    return decorated


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_latest_equity():
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT equity FROM equity ORDER BY timestamp DESC LIMIT 1"
            ).fetchone()
        return row["equity"] if row else 0.0
    except Exception:
        return 0.0


def get_today_pnl():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT COALESCE(SUM(pnl), 0) as total FROM trades "
                "WHERE action='CLOSE' AND timestamp LIKE ?",
                (today + "%",)
            ).fetchone()
        return row["total"] if row else 0.0
    except Exception:
        return 0.0


def get_day_open_equity():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT equity FROM equity WHERE timestamp LIKE ? ORDER BY timestamp ASC LIMIT 1",
                (today + "%",)
            ).fetchone()
        return row["equity"] if row else get_latest_equity()
    except Exception:
        return get_latest_equity()


def get_open_positions():
    try:
        with _conn() as c:
            rows = c.execute("""
                SELECT strategy, symbol, side, entry_price, sl, tp, lots, timestamp, position_id
                FROM trades
                WHERE action = 'OPEN'
                  AND position_id NOT IN (
                      SELECT position_id FROM trades WHERE action = 'CLOSE'
                  )
                ORDER BY timestamp DESC
            """).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_recent_trades(limit=50):
    try:
        with _conn() as c:
            rows = c.execute("""
                SELECT strategy, symbol, side, entry_price, exit_price,
                       sl, tp, lots, pnl, result, timestamp
                FROM trades
                WHERE action = 'CLOSE'
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def get_strategy_stats():
    try:
        with _conn() as c:
            rows = c.execute("""
                SELECT strategy,
                       COUNT(*) as trades,
                       SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                       ROUND(SUM(pnl), 2) as total_pnl,
                       MAX(timestamp) as last_trade
                FROM trades
                WHERE action = 'CLOSE'
                GROUP BY strategy
            """).fetchall()
        stats = {r["strategy"]: dict(r) for r in rows}
    except Exception:
        stats = {}

    result = []
    today  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for s in STRATEGIES:
        d = stats.get(s, {"trades": 0, "wins": 0, "total_pnl": 0.0, "last_trade": None})
        d["strategy"] = s
        d["wr"] = round(d["wins"] / d["trades"] * 100, 1) if d["trades"] else 0.0
        d["traded_today"] = bool(d["last_trade"] and d["last_trade"].startswith(today))
        result.append(d)
    return result


def get_equity_curve(days=30):
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        with _conn() as c:
            rows = c.execute("""
                SELECT timestamp, equity FROM equity
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (since,)).fetchall()
        return [{"t": r["timestamp"], "v": r["equity"]} for r in rows]
    except Exception:
        return []


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
@require_auth
def index():
    equity      = get_latest_equity()
    today_pnl   = get_today_pnl()
    day_open    = get_day_open_equity()
    daily_dd    = ((equity - day_open) / day_open * 100) if day_open > 0 else 0.0
    kill_switch = daily_dd <= -4.0

    return render_template(
        "index.html",
        equity       = equity,
        today_pnl    = today_pnl,
        daily_dd     = daily_dd,
        kill_switch  = kill_switch,
        open_positions = get_open_positions(),
        recent_trades  = get_recent_trades(),
        strategy_stats = get_strategy_stats(),
        equity_curve   = get_equity_curve(),
        now            = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
