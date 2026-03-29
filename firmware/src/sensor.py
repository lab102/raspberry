from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import threading
import time


@dataclass
class SensorState:
    pin: int
    frequency_hz: float = 0.0
    sample_window_seconds: float = 1.0
    pulse_count_in_window: int = 0
    last_rising_edge_at: float | None = None


class SensorFrequencyMonitor:
    def __init__(self, gpio_adapter: object, pin: int, sample_window_seconds: float) -> None:
        self._gpio_adapter = gpio_adapter
        self._pin = pin
        self._sample_window_seconds = max(sample_window_seconds, 0.2)
        self._lock = threading.Lock()
        self._pulse_times: deque[float] = deque()
        self._state = SensorState(pin=pin, sample_window_seconds=self._sample_window_seconds)

    def setup(self) -> None:
        self._gpio_adapter.setup_input(self._pin, callback=self.record_rising_edge)

    def record_rising_edge(self) -> None:
        now = time.monotonic()
        with self._lock:
            self._pulse_times.append(now)
            self._state.last_rising_edge_at = now
            self._trim_locked(now)
            self._update_frequency_locked()

    def get_state(self) -> dict[str, int | float | None]:
        with self._lock:
            now_monotonic = time.monotonic()
            now_unix = time.time()
            self._trim_locked(now_monotonic)
            self._update_frequency_locked()
            return {
                "pin": self._state.pin,
                "frequency_hz": round(self._state.frequency_hz, 3),
                "sample_window_seconds": self._state.sample_window_seconds,
                "pulse_count_in_window": self._state.pulse_count_in_window,
                "last_rising_edge_age_seconds": self._calculate_last_edge_age_locked(),
                "measured_at_unix_ms": round(now_unix * 1000),
            }

    def _trim_locked(self, now: float) -> None:
        oldest_allowed = now - self._sample_window_seconds
        while self._pulse_times and self._pulse_times[0] < oldest_allowed:
            self._pulse_times.popleft()

    def _update_frequency_locked(self) -> None:
        self._state.pulse_count_in_window = len(self._pulse_times)
        self._state.frequency_hz = len(self._pulse_times) / self._sample_window_seconds

    def _calculate_last_edge_age_locked(self) -> float | None:
        if self._state.last_rising_edge_at is None:
            return None
        return round(time.monotonic() - self._state.last_rising_edge_at, 3)
