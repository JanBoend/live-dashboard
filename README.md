# live-dashboard

Read-only Flask dashboard for monitoring a live systematic trading system.
Part of a live trading system running on IC Markets via cTrader.
Broker integration code is private — this repo covers the dashboard and trade logger only.

## Features

- Equity curve with daily PnL bar chart
- Per-strategy breakdown: trades, win rate, total PnL
- Open positions table (live)
- Trade history with strategy filter
- HTTP Basic Auth, auto-refresh every 30s
- Runs as a systemd service on a VPS

## Quick start

```bash
pip install -r requirements.txt
python seed_sample_data.py   # generates trades_sample.db with synthetic data
python dashboard/app.py      # open http://localhost:5050
```

Default credentials (demo): `admin` / `changeme`

Set your own via environment variables:

```bash
export DASH_USER=myuser
export DASH_PASSWORD=mypassword
export DB_PATH=trades_sample.db
python dashboard/app.py
```

## Schema

See `schema.sql`. Three tables: `trades`, `equity`, `daily_summary`.

The `trade_logger.py` module is called by the live bot on every open/close event via `log_open()` and `log_close()`.

## Deployment

See `deploy/dashboard.service` for systemd configuration. Copy to `/etc/systemd/system/`, set environment variables, then:

```bash
systemctl enable dashboard
systemctl start dashboard
```

## Live system

Strategies ([icm-strategies](https://github.com/[username]/icm-strategies)) run live using the backtesting engine ([quant-engine](https://github.com/[username]/quant-engine)).
Broker integration via cTrader is private and not included in this repo.
