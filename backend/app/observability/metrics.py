from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field


@dataclass
class MetricsRegistry:
    counters: Counter = field(default_factory=Counter)
    timings_ms: list[dict[str, float]] = field(default_factory=list)

    def incr(self, name: str, amount: int = 1) -> None:
        self.counters[name] += amount

    def timing(self, name: str, value_ms: float) -> None:
        self.timings_ms.append({name: round(value_ms, 2)})

    def snapshot(self) -> dict:
        return {
            "counters": dict(self.counters),
            "timings_ms": self.timings_ms[-50:],
        }


metrics = MetricsRegistry()

