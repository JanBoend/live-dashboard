# seed_sample_data.py
"""Generate synthetic trade data for demo purposes. No real trades included."""
import sqlite3
import random
import os
from datetime import datetime, timedelta

DB = "trades_sample.db"

STRATEGIES = ["fvg", "orb", "amd", "eu_amd", "eu_orb"]
SYMBOLS    = {"fvg": "QQQ", "orb": "QQQ", "amd": "QQQ",
              "eu_amd": "EURUSD", "eu_orb": "EURUSD"}
SHARPES    = {"fvg": 1.02, "orb": 1.14, "amd": 1.36, "eu_amd": 1.40, "eu_orb": 0.92}

random.seed(42)

if os.path.exists(DB):
    os.remove(DB)

conn = sqlite3.connect(DB)
conn.executescript(open("schema.sql").read())

capital = 10_000.0
now = datetime(2025, 1, 2, 14, 30)
pos_id = 1

for day in range(365):
    date = now + timedelta(days=day)
    if date.weekday() >= 5:
        continue

    for strat in STRATEGIES:
        win_rate = 0.45 + SHARPES[strat] * 0.05
        rr = 3.0

        if random.random() < 0.6:
            entry_t = date + timedelta(hours=random.uniform(1, 4))
            exit_t  = entry_t + timedelta(hours=random.uniform(1, 6))
            side    = random.choice(["long", "short"])
            ep      = round(random.uniform(400, 500), 2)
            risk    = ep * 0.005
            sl      = ep - risk if side == "long" else ep + risk
            tp      = ep + risk * rr if side == "long" else ep - risk * rr
            won     = random.random() < win_rate
            xp      = tp if won else sl
            pnl     = (capital * 0.005 * rr) if won else -(capital * 0.005)
            result  = "TP" if won else "SL"
            capital += pnl

            conn.execute(
                "INSERT INTO trades (timestamp,strategy,symbol,side,action,"
                "entry_price,exit_price,sl,tp,lots,pnl,result,position_id,reason) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (entry_t.strftime("%Y-%m-%d %H:%M:%S"), strat, SYMBOLS[strat],
                 side, "OPEN", ep, None, round(sl, 2), round(tp, 2),
                 0.1, None, None, str(pos_id), "")
            )
            conn.execute(
                "INSERT INTO trades (timestamp,strategy,symbol,side,action,"
                "entry_price,exit_price,sl,tp,lots,pnl,result,position_id,reason) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (exit_t.strftime("%Y-%m-%d %H:%M:%S"), strat, SYMBOLS[strat],
                 side, "CLOSE", ep, round(xp, 2), round(sl, 2), round(tp, 2),
                 0.1, round(pnl, 2), result, str(pos_id), "")
            )
            pos_id += 1

    conn.execute(
        "INSERT INTO equity (timestamp,equity,balance) VALUES (?,?,?)",
        (date.strftime("%Y-%m-%d %H:%M:%S"), round(capital, 2), round(capital, 2))
    )

conn.commit()
conn.close()
print(f"Sample data seeded. Final equity: ${capital:,.2f}")
