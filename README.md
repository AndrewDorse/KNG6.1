# KNG6 — streak076 cheap (live)

Dockerized Polymarket **BTC Up/Down** bot: **5-minute and 15-minute windows run in parallel** (separate Gamma slugs, separate tape state). When the **streak → cheap** rule fires (same logic as backtest `X_streak20_076_cheap19`: **20** consecutive seconds with `max(up,down) ≥ 0.76`, then first second with either leg **≤ 0.19**), the bot sends **one FAK market buy** for **`KNG6_NOTIONAL_USD`** (default **$1**) on the chosen outcome token.

**Defaults:** poll **0.25s** (`KNG6_POLL_INTERVAL_SECONDS`) to reduce missed seconds, **max 1** buy per slug, no buy in the last **20s** of the window.

## Relation to other repos

| Repo | Role |
|------|------|
| **KNG3** | SHAMAN v1 (Paladin) deploy image |
| **KNG4** | PRST1 scalp |
| **KNG6** | This streak076 one-shot buy (**use this**; KNG5 name was dropped) |

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
