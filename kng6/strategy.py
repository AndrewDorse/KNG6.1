"""Strategy-1 skew→cheap — PM mids only (matches PALADIN ``_first_cheap_after_skew_streak``; live defaults 0.82/22/0.19)."""

from __future__ import annotations

from typing import Literal

Side = Literal["up", "down"]


def cheap_side_at(u: float, d: float, thr: float) -> Side | None:
    bu, bd = u <= thr, d <= thr
    if bu and bd:
        return "up" if u <= d else "down"
    if bu:
        return "up"
    if bd:
        return "down"
    return None


def first_cheap_after_skew_streak(
    series: list[tuple[float, float]],
    *,
    skew_thr: float,
    streak: int,
    cheap_thr: float,
) -> tuple[Side | None, float | None]:
    """After ``streak`` consecutive seconds with max(up,down)>=skew_thr, first later cheap hit."""
    run = 0
    armed_until = -1
    for _t, (u, d) in enumerate(series):
        if max(u, d) >= skew_thr:
            run += 1
        else:
            run = 0
        if run >= streak:
            armed_until = _t
    if armed_until < 0:
        return None, None
    for t in range(armed_until + 1, len(series)):
        u, d = series[t]
        c = cheap_side_at(u, d, cheap_thr)
        if c is not None:
            return c, (u if c == "up" else d)
    return None, None


def signal_streak076(
    series: list[tuple[float, float]],
    *,
    skew_thr: float,
    streak_sec: int,
    cheap_thr: float,
) -> tuple[Side | None, float | None]:
    """Entry signal for strategy-1 (defaults: 0.82 / 22 / 0.19). Name ``signal_streak076`` kept for imports."""
    return first_cheap_after_skew_streak(
        series, skew_thr=skew_thr, streak=streak_sec, cheap_thr=cheap_thr
    )
