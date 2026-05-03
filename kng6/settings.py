"""KNG6 environment (Polymarket CLOB + Gamma + streak12_cheap19 / strategy-1 params)."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass


class Kng6ConfigError(RuntimeError):
    pass


def _strip(s: str | None) -> str:
    return (s or "").strip().strip('"').strip("'")


def _env_float(name: str, default: float) -> float:
    raw = _strip(os.getenv(name))
    if not raw:
        return default
    return float(raw)


def _env_int(name: str, default: int) -> int:
    raw = _strip(os.getenv(name))
    if not raw:
        return default
    return int(float(raw))


def _env_bool(name: str, default: bool) -> bool:
    raw = _strip(os.getenv(name))
    if not raw:
        return default
    return raw.lower() in ("1", "true", "yes", "y", "on")


def _parse_window_minutes_list(raw: str | None) -> tuple[int, ...]:
    s = _strip(raw)
    if not s:
        return (15,)
    out: list[int] = []
    for part in s.split(","):
        p = part.strip()
        if not p:
            continue
        try:
            v = int(float(p))
        except ValueError as exc:
            raise Kng6ConfigError(
                f"KNG6_WINDOW_MINUTES must be comma-separated integers (got {raw!r})"
            ) from exc
        if v > 0 and v not in out:
            out.append(v)
    return tuple(out) if out else (15,)


@dataclass(frozen=True, slots=True)
class Kng6Settings:
    private_key: str
    funder: str
    signature_type: int
    relayer_api_key: str
    relayer_secret: str
    relayer_passphrase: str
    dry_run: bool
    poll_interval_seconds: float
    request_timeout_seconds: float
    market_symbol: str
    window_minutes_list: tuple[int, ...]
    notional_usd: float
    max_trades_per_slug: int
    new_order_cutoff_seconds: int
    skew_thr: float
    streak_seconds: int
    cheap_thr: float
    log_level: str

    @classmethod
    def from_env(cls) -> Kng6Settings:
        pk = _strip(os.getenv("POLY_PRIVATE_KEY"))
        fu = _strip(os.getenv("POLY_FUNDER"))
        if not pk:
            raise Kng6ConfigError("POLY_PRIVATE_KEY is required.")
        if not fu or not re.fullmatch(r"0x[a-fA-F0-9]{40}", fu):
            raise Kng6ConfigError("POLY_FUNDER must be 0x + 40 hex.")
        return cls(
            private_key=pk,
            funder=fu,
            signature_type=_env_int("POLY_SIGNATURE_TYPE", 1),
            relayer_api_key=_strip(os.getenv("RELAYER_API_KEY")),
            relayer_secret=_strip(os.getenv("RELAYER_SECRET")),
            relayer_passphrase=_strip(os.getenv("RELAYER_PASSPHRASE")),
            dry_run=_env_bool("POLY_DRY_RUN", True),
            poll_interval_seconds=_env_float("KNG6_POLL_INTERVAL_SECONDS", 0.25),
            request_timeout_seconds=_env_float("KNG6_REQUEST_TIMEOUT_SECONDS", 12.0),
            market_symbol=_strip(os.getenv("KNG6_MARKET_SYMBOL")) or "BTC",
            window_minutes_list=_parse_window_minutes_list(os.getenv("KNG6_WINDOW_MINUTES")),
            notional_usd=_env_float("KNG6_NOTIONAL_USD", 1.0),
            max_trades_per_slug=max(1, _env_int("KNG6_MAX_TRADES_PER_SLUG", 1)),
            new_order_cutoff_seconds=max(0, _env_int("KNG6_NEW_ORDER_CUTOFF_SECONDS", 20)),
            skew_thr=_env_float("KNG6_SKEW_THR", 0.76),
            streak_seconds=max(1, _env_int("KNG6_STREAK_SECONDS", 12)),
            cheap_thr=_env_float("KNG6_CHEAP_THR", 0.19),
            log_level=_strip(os.getenv("KNG6_LOG_LEVEL")) or "INFO",
        )
