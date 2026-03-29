from __future__ import annotations

import threading
import time


class MockInputProfile:
    def __init__(self, base_frequency_hz: float, growth_rate_per_second: float) -> None:
        self.base_frequency_hz = max(base_frequency_hz, 0.0)
        self.growth_rate_per_second = max(growth_rate_per_second, 0.0)
        self.started_at = time.monotonic()

    def frequency_at(self, now: float) -> float:
        elapsed_seconds = max(now - self.started_at, 0.0)
        return self.base_frequency_hz * ((1 + self.growth_rate_per_second) ** elapsed_seconds)


class MockGPIOAdapter:
    def __init__(self) -> None:
        self._outputs: dict[int, bool] = {}
        self._input_callbacks: dict[int, object] = {}
        self._mock_sensor_profiles: dict[int, MockInputProfile] = {}
        self._runner_lock = threading.Lock()
        self._running = True
        self._pulse_thread = threading.Thread(target=self._pulse_loop, daemon=True)
        self._pulse_thread.start()

    def setup_output(self, pin: int) -> None:
        self._outputs[pin] = False
        print(f"[mock-gpio] setup output pin {pin}")

    def write(self, pin: int, value: bool) -> None:
        self._outputs[pin] = value
        state = "HIGH" if value else "LOW"
        print(f"[mock-gpio] pin {pin} -> {state}")

    def setup_input(self, pin: int, callback: object | None = None) -> None:
        if callback is not None:
            self._input_callbacks[pin] = callback
        self._mock_sensor_profiles.setdefault(pin, MockInputProfile(0.0, 0.0))
        print(f"[mock-gpio] setup input pin {pin}")

    def set_mock_input_frequency(self, pin: int, frequency_hz: float) -> None:
        self.configure_mock_input_ramp(pin, frequency_hz, 0.0)

    def configure_mock_input_ramp(
        self, pin: int, base_frequency_hz: float, growth_rate_per_second: float
    ) -> None:
        with self._runner_lock:
            self._mock_sensor_profiles[pin] = MockInputProfile(
                base_frequency_hz=base_frequency_hz,
                growth_rate_per_second=growth_rate_per_second,
            )

    def cleanup(self) -> None:
        self._running = False
        self._pulse_thread.join(timeout=1)

    def _pulse_loop(self) -> None:
        pulse_credit: dict[int, float] = {}
        last_tick_at = time.monotonic()

        while self._running:
            now = time.monotonic()
            elapsed = max(now - last_tick_at, 0.0)
            last_tick_at = now
            with self._runner_lock:
                profiles = list(self._mock_sensor_profiles.items())

            for pin, profile in profiles:
                frequency_hz = profile.frequency_at(now)
                if frequency_hz <= 0:
                    pulse_credit.pop(pin, None)
                    continue

                pulse_credit[pin] = pulse_credit.get(pin, 0.0) + (frequency_hz * elapsed)
                due_pulses = int(pulse_credit[pin])
                if due_pulses <= 0:
                    continue

                callback = self._input_callbacks.get(pin)
                if callable(callback):
                    for _ in range(due_pulses):
                        callback()

                pulse_credit[pin] -= due_pulses

            time.sleep(0.0005)
