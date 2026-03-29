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
    period_count_in_window: int = 0
    measured_duration_seconds: float = 0.0
    last_rising_edge_at_ns: int | None = None


class SensorFrequencyMonitor:
    def __init__(self, gpio_adapter: object, pin: int, sample_window_seconds: float) -> None:
        self._gpio_adapter = gpio_adapter
        self._pin = pin
        self._sample_window_seconds = max(sample_window_seconds, 0.2)
        self._sample_window_ns = int(self._sample_window_seconds * 1_000_000_000)
        self._lock = threading.Lock()
        self._pulse_times_ns: deque[int] = deque()
        self._state = SensorState(pin=pin, sample_window_seconds=self._sample_window_seconds)

    def setup(self) -> None:
        self._gpio_adapter.setup_input(self._pin, callback=self.record_rising_edge)

    def record_rising_edge(self) -> None:
        now_ns = time.perf_counter_ns()
        with self._lock:
            self._pulse_times_ns.append(now_ns)
            self._state.last_rising_edge_at_ns = now_ns
            self._trim_locked(now_ns)
            self._update_frequency_locked()

    def get_state(self) -> dict[str, int | float | None]:
        with self._lock:
            now_perf_ns = time.perf_counter_ns()
            now_unix_ms = time.time_ns() // 1_000_000
            self._trim_locked(now_perf_ns)
            self._update_frequency_locked()
            return {
                "pin": self._state.pin,
                "frequency_hz": round(self._state.frequency_hz, 3),
                "sample_window_seconds": self._state.sample_window_seconds,
                "pulse_count_in_window": self._state.pulse_count_in_window,
                "period_count_in_window": self._state.period_count_in_window,
                "measured_duration_seconds": round(self._state.measured_duration_seconds, 6),
                "last_rising_edge_age_seconds": self._calculate_last_edge_age_locked(now_perf_ns),
                "measured_at_unix_ms": now_unix_ms,
            }

    def _trim_locked(self, now_ns: int) -> None:
        oldest_allowed_ns = now_ns - self._sample_window_ns
        while self._pulse_times_ns and self._pulse_times_ns[0] < oldest_allowed_ns:
            self._pulse_times_ns.popleft()

    def _update_frequency_locked(self) -> None:
        pulse_count = len(self._pulse_times_ns)
        self._state.pulse_count_in_window = pulse_count
        if pulse_count < 2:
            self._state.period_count_in_window = 0
            self._state.measured_duration_seconds = 0.0
            self._state.frequency_hz = 0.0
            return

        period_count = pulse_count - 1
        measured_duration_ns = self._pulse_times_ns[-1] - self._pulse_times_ns[0]
        measured_duration_seconds = measured_duration_ns / 1_000_000_000
        self._state.period_count_in_window = period_count
        self._state.measured_duration_seconds = max(measured_duration_seconds, 0.0)
        if measured_duration_ns <= 0:
            self._state.frequency_hz = 0.0
            return

        self._state.frequency_hz = period_count / measured_duration_seconds

    def _calculate_last_edge_age_locked(self, now_perf_ns: int) -> float | None:
        if self._state.last_rising_edge_at_ns is None:
            return None
        return round((now_perf_ns - self._state.last_rising_edge_at_ns) / 1_000_000_000, 6)
