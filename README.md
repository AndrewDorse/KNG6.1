# KNG6 — strategy-1: streak12_cheap19 (live)

Dockerized Polymarket **BTC Up/Down** bot: by default **15m windows only** (`KNG6_WINDOW_MINUTES=15`). Set `KNG6_WINDOW_MINUTES=5,15` for **5m + 15m** in parallel (separate Gamma slugs, separate tape state). When the **streak → cheap** rule fires (backtest id **`X_streak12_076_cheap19`**: **12** consecutive seconds with `max(up,down) ≥ 0.76`, then first second with either leg **≤ 0.19**), the bot sends **one FAK market buy** for **`KNG6_NOTIONAL_USD`** (default **$1**) on the chosen outcome token.

**Calibration (PALADIN `sim_streak076_sweep_last_n.py`, newest 100 public 15m windows, 99 non-tie):** EV ≈ **+11.75** USD/window, PnL sum ≈ **+1163**, **55** hits, WR on hits ≈ **43.6%** (replay mids; not a guarantee live).

**Defaults:** poll **0.25s** (`KNG6_POLL_INTERVAL_SECONDS`) to reduce missed seconds, **max 1** buy per slug, no buy in the last **20s** of the window.

**Logs (quiet):** HTTP libraries are capped at WARNING so Docker logs are not flooded with per-request lines. Runtime lines are **`KNG6 INIT`** (once), **`KNG6 DEAL START`** (side, size USD, signal mid), **`KNG6 WINDOW END`** when the slug rolls after a deal (**SUCCESS** / **LOSS** / **TIE** from last tape mids vs side bought). Rare failures: **`KNG6 DEAL ABORT`**.

## Relation to other repos

| Repo | Role |
|------|------|
| **KNG3** | SHAMAN v1 (Paladin) deploy image |
| **KNG4** | PRST1 scalp |
| **KNG6** | **Strategy-1** streak12_cheap19 one-shot buy (**use this**; KNG5 name was dropped) |

## Local run

```powershell
cd C:\Users\Lenovo\Documents\Git\KNG6
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python -m kng6
```

Keep `POLY_DRY_RUN=true` until logs look correct.

## Docker

```powershell
copy .env.example .env
docker compose --env-file .env build
docker compose --env-file .env up -d
docker compose logs -f kng6
```

Set `POLY_DRY_RUN=false` only when ready for real orders (`py_clob_client_v2` FAK).

## Go-live preflight (host)

1. **`.env`:** `POLY_PRIVATE_KEY`, `POLY_FUNDER` (0x + 40 hex), relayer fields if you use them; **`POLY_DRY_RUN=false`** only when you intend real FAK buys.  
2. **`KNG6_WINDOW_MINUTES`:** `15` for 15m-only (matches code default); remove or change if you still want `5,15`.  
3. **Image:** `docker compose --env-file .env build` then `up -d`; confirm logs show **`KNG6 INIT`** with `dry_run=False` before leaving unattended.

## Push to GitHub

1. Create an **empty** repo named `KNG6` on GitHub (no README) under your account.  
2. From this folder:

```powershell
cd C:\Users\Lenovo\Documents\Git\KNG6
git remote remove origin 2>$null
git remote add origin https://github.com/<YOU>/KNG6.git
git push -u origin main
```

If `origin` already points at `AndrewDorse/KNG6`, change the URL after the repo exists, or create that repo on GitHub first.

## Disclaimer

Prediction markets are risky. Experimental software. No warranty.
