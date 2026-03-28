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
            self._trim_locked(time.monotonic())
            self._update_frequency_locked()
            return {
                "pin": self._state.pin,
                "frequency_hz": round(self._state.frequency_hz, 3),
                "sample_window_seconds": self._state.sample_window_seconds,
                "pulse_count_in_window": self._state.pulse_count_in_window,
                "last_rising_edge_age_seconds": self._calculate_last_edge_age_locked(),
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


class SensorStepperSynchronizer:
    def __init__(
        self,
        sensor_monitor: SensorFrequencyMonitor,
        stepper_controller: object,
        direction: str,
        steps_per_hz: float,
        max_steps_per_second: float,
    ) -> None:
        self._sensor_monitor = sensor_monitor
        self._stepper_controller = stepper_controller
        self._lock = threading.Lock()
        self._direction = direction
        self._steps_per_hz = max(steps_per_hz, 0.0)
        self._max_steps_per_second = max(max_steps_per_second, 1.0)
        self._enabled = False
        self._running = True
        self._target_steps_per_second = 0.0
        self._thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._thread.start()

    def get_state(self) -> dict[str, float | bool | str]:
        with self._lock:
            return {
                "enabled": self._enabled,
                "direction": self._direction,
                "steps_per_hz": round(self._steps_per_hz, 3),
                "max_steps_per_second": round(self._max_steps_per_second, 2),
                "target_steps_per_second": round(self._target_steps_per_second, 2),
            }

    def update_settings(
        self,
        *,
        enabled: bool | None = None,
        direction: str | None = None,
        steps_per_hz: float | None = None,
        max_steps_per_second: float | None = None,
    ) -> dict[str, float | bool | str]:
        with self._lock:
            if enabled is not None:
                self._enabled = enabled
            if direction is not None:
                normalized = direction.lower()
                if normalized not in {"forward", "reverse"}:
                    raise ValueError("direction must be 'forward' or 'reverse'")
                self._direction = normalized
            if steps_per_hz is not None:
                if steps_per_hz < 0:
                    raise ValueError("steps_per_hz must be zero or greater")
                self._steps_per_hz = steps_per_hz
            if max_steps_per_second is not None:
                if max_steps_per_second <= 0:
                    raise ValueError("max_steps_per_second must be greater than zero")
                self._max_steps_per_second = max_steps_per_second

        return self.get_state()

    def shutdown(self) -> None:
        self._running = False
        self._thread.join(timeout=1)

    def _sync_loop(self) -> None:
        while self._running:
            with self._lock:
                enabled = self._enabled
                direction = self._direction
                steps_per_hz = self._steps_per_hz
                max_steps_per_second = self._max_steps_per_second

            sensor_state = self._sensor_monitor.get_state()
            sensor_hz = float(sensor_state["frequency_hz"])
            target_steps_per_second = min(sensor_hz * steps_per_hz, max_steps_per_second)
            if not enabled:
                target_steps_per_second = 0.0

            self._stepper_controller.set_continuous_motion(direction, target_steps_per_second)

            with self._lock:
                self._target_steps_per_second = target_steps_per_second

            time.sleep(0.1)
