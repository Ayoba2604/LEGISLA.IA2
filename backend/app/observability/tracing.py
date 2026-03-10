from __future__ import annotations

import time
from contextlib import contextmanager

from backend.app.observability.metrics import metrics


@contextmanager
def trace_step(name: str):
    started = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - started) * 1000
        metrics.timing(name, elapsed_ms)
