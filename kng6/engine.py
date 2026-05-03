"""Live loop: 15m lane(s), streak→cheap signal, $1 FAK market buy once per slug."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from kng6.__version__ import __version__
from kng6.clob_shim import Kng6Clob
from kng6.gamma_market import discover_active_btc_window, window_start_ts_from_slug
from kng6.settings import Kng6Settings
from kng6.strategy import signal_streak076

LOGGER = logging.getLogger("kng6")

_TIE_EPS = 1e-9


def _winner_from_last_mids(up_mid: float, down_mid: float) -> str:
    if up_mid > down_mid + _TIE_EPS:
        return "up"
    if down_mid > up_mid + _TIE_EPS:
        return "down"
    return "tie"


@dataclass
class _TapeState:
    """Forward-filled PM mids by integer elapsed second (matches pool CSV replay style)."""

    series: list[tuple[float, float]] = field(default_factory=list)
    last_elapsed: int = -1
    carry_u: float = 0.5
    carry_d: float = 0.5

    def reset(self) -> None:
        self.series.clear()
        self.last_elapsed = -1
        self.carry_u = 0.5
        self.carry_d = 0.5

    def append_observation(self, window_sec: int, elapsed: int, u: float, d: float) -> None:
        e = max(0, min(window_sec - 1, int(elapsed)))
        if self.last_elapsed < 0:
            for _ in range(e):
                self.series.append((0.5, 0.5))
            self.series.append((u, d))
            self.last_elapsed = e
            self.carry_u, self.carry_d = u, d
            return
        if e <= self.last_elapsed:
            if self.series:
                self.series[-1] = (u, d)
            self.carry_u, self.carry_d = u, d
            return
        for _ in range(self.last_elapsed + 1, e):
            self.series.append((self.carry_u, self.carry_d))
        self.series.append((u, d))
        self.carry_u, self.carry_d = u, d
        self.last_elapsed = e


@dataclass
class _LaneState:
    wm: int
    tape: _TapeState = field(default_factory=_TapeState)
    slug: str | None = None
    trades_this_slug: int = 0
    deal_side: str | None = None


class Kng6LiveEngine:
    def __init__(self, settings: Kng6Settings) -> None:
        self.s = settings
        self._clob = Kng6Clob(
            private_key=settings.private_key,
            funder=settings.funder,
            signature_type=settings.signature_type,
            relayer_api_key=settings.relayer_api_key,
            relayer_secret=settings.relayer_secret,
            relayer_passphrase=settings.relayer_passphrase,
        )
        self._lanes: dict[int, _LaneState] = {
            int(wm): _LaneState(wm=int(wm)) for wm in settings.window_minutes_list
        }
        self._init_logged = False

    def _lane(self, wm: int) -> _LaneState:
        if wm not in self._lanes:
            self._lanes[wm] = _LaneState(wm=int(wm))
        return self._lanes[wm]

    def _log_init_once(self) -> None:
        if self._init_logged:
            return
        self._init_logged = True
        lanes_s = ",".join(f"{m}m" for m in self.s.window_minutes_list)
        LOGGER.info(
            "KNG6 INIT version=%s strategy=streak12_cheap19 skew=%.2f streak_sec=%d cheap=%.2f "
            "windows=%s poll_sec=%.3f dry_run=%s notional_usd=%.2f max_trades_per_slug=%d cutoff_last_sec=%d market=%s",
            __version__,
            self.s.skew_thr,
            self.s.streak_seconds,
            self.s.cheap_thr,
            lanes_s,
            self.s.poll_interval_seconds,
            self.s.dry_run,
            self.s.notional_usd,
            self.s.max_trades_per_slug,
            self.s.new_order_cutoff_seconds,
            self.s.market_symbol,
        )

    def _finalize_previous_slug(self, lane: _LaneState, wm: int, prev_slug: str) -> None:
        if not lane.deal_side or not lane.tape.series:
            lane.deal_side = None
            return
        last_u, last_d = lane.tape.series[-1]
        win = _winner_from_last_mids(last_u, last_d)
        bought = lane.deal_side
        lane.deal_side = None
        if win == "tie":
            LOGGER.info(
                "KNG6 WINDOW END wm=%d slug=%s bought=%s outcome=tie last_up=%.4f last_down=%.4f result=TIE",
                wm,
                prev_slug,
                bought.upper(),
                last_u,
                last_d,
            )
            return
        ok = bought == win
        tag = "SUCCESS" if ok else "LOSS"
        LOGGER.info(
            "KNG6 WINDOW END wm=%d slug=%s bought=%s outcome=%s last_up=%.4f last_down=%.4f result=%s",
            wm,
            prev_slug,
            bought.upper(),
            win.upper(),
            last_u,
            last_d,
            tag,
        )

    def _tick_lane(self, wm: int) -> None:
        lane = self._lane(wm)
        ws = int(wm) * 60
        c = discover_active_btc_window(
            market_symbol=self.s.market_symbol,
            window_minutes=wm,
            timeout=self.s.request_timeout_seconds,
        )
        if c is None:
            return

        if lane.slug is not None and lane.slug != c.slug:
            self._finalize_previous_slug(lane, wm, lane.slug)
            lane.slug = c.slug
            lane.tape.reset()
            lane.trades_this_slug = 0
        elif lane.slug is None:
            lane.slug = c.slug
            lane.tape.reset()
            lane.trades_this_slug = 0

        now = time.time()
        rem = c.end_time.timestamp() - now
        if rem <= float(self.s.new_order_cutoff_seconds):
            return

        u_mid = self._clob.get_midpoint(c.up.token_id)
        d_mid = self._clob.get_midpoint(c.down.token_id)
        if u_mid is None or d_mid is None:
            return

        start = window_start_ts_from_slug(c.slug)
        if start is None:
            return
        elapsed = int(now - float(start))
        lane.tape.append_observation(ws, elapsed, float(u_mid), float(d_mid))

        if lane.trades_this_slug >= self.s.max_trades_per_slug:
            return

        side, entry_px = signal_streak076(
            lane.tape.series,
            skew_thr=self.s.skew_thr,
            streak_sec=self.s.streak_seconds,
            cheap_thr=self.s.cheap_thr,
        )
        if side is None or entry_px is None:
            return

        tok = c.up if side == "up" else c.down
        LOGGER.info(
            "KNG6 DEAL START wm=%d slug=%s side=%s size_usd=%.2f price_mid=%.4f dry_run=%s",
            wm,
            c.slug,
            side.upper(),
            float(self.s.notional_usd),
            float(entry_px),
            self.s.dry_run,
        )
        lane.deal_side = side

        if self.s.dry_run:
            lane.trades_this_slug += 1
            return

        need = float(self.s.notional_usd) * 1.02
        bal = self._clob.wallet_balance_usdc()
        if bal < need:
            lane.deal_side = None
            LOGGER.warning(
                "KNG6 DEAL ABORT wm=%d slug=%s reason=insufficient_collateral have_usd=%.2f need_usd=%.2f",
                wm,
                c.slug,
                bal,
                need,
            )
            return
        try:
            self._clob.market_buy_usdc(tok, float(self.s.notional_usd))
        except Exception as exc:  # noqa: BLE001
            lane.deal_side = None
            LOGGER.warning("KNG6 DEAL ABORT wm=%d slug=%s reason=order_failed err=%s", wm, c.slug, exc)
            return
        lane.trades_this_slug += 1

    def tick_once(self) -> None:
        for wm in self.s.window_minutes_list:
            try:
                self._tick_lane(int(wm))
            except Exception:  # noqa: BLE001
                LOGGER.exception("KNG6[%dm] tick error", int(wm))

    def run_forever(self) -> None:
        self._log_init_once()
        while True:
            try:
                self.tick_once()
            except Exception:  # noqa: BLE001
                LOGGER.exception("KNG6 tick_once error")
            time.sleep(self.s.poll_interval_seconds)


def configure_logging(level: str) -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)sZ %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    for name in (
        "urllib3",
        "urllib3.connectionpool",
        "requests",
        "requests.packages.urllib3",
        "httpx",
        "httpcore",
        "charset_normalizer",
        "py_clob_client",
        "py_clob_client_v2",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)
