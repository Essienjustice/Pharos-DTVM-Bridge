from __future__ import annotations

import time
from collections.abc import Iterable


def print_progressive_logs(
    logs: Iterable[str],
    *,
    presentation: bool = False,
    delay: float = 0.0,
) -> None:
    for line in logs:
        print(line)
        if presentation:
            time.sleep(delay)
