"""``python -m kng6`` — live strategy-1 (streak12_cheap19: 12s max>=0.76 then cheap<=0.19) + $1 FAK (5m + 15m)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kng6.engine import Kng6LiveEngine, configure_logging
from kng6.settings import Kng6ConfigError, Kng6Settings


def main() -> int:
    try:
        settings = Kng6Settings.from_env()
    except Kng6ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2
    configure_logging(settings.log_level)
    print(
        f"KNG6 boot: lanes={[f'{m}m' for m in settings.window_minutes_list]} "
        f"poll={settings.poll_interval_seconds}s dry_run={settings.dry_run} "
        f"notional=${settings.notional_usd:.2f} streak={settings.streak_seconds}s "
        f"skew>={settings.skew_thr} cheap<={settings.cheap_thr}",
        flush=True,
    )
    Kng6LiveEngine(settings).run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
