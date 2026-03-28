from __future__ import annotations

import threading
import time


class MockGPIOAdapter:
    def __init__(self) -> None:
        self._outputs: dict[int, bool] = {}
        self._input_callbacks: dict[int, object] = {}
        self._mock_sensor_hz: dict[int, float] = {}
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
        self._mock_sensor_hz.setdefault(pin, 0.0)
        print(f"[mock-gpio] setup input pin {pin}")

    def set_mock_input_frequency(self, pin: int, frequency_hz: float) -> None:
        self._mock_sensor_hz[pin] = max(frequency_hz, 0.0)

    def cleanup(self) -> None:
        self._running = False
        self._pulse_thread.join(timeout=1)

    def _pulse_loop(self) -> None:
        next_fire_at: dict[int, float] = {}

        while self._running:
            now = time.monotonic()
            with self._runner_lock:
                frequencies = list(self._mock_sensor_hz.items())

            for pin, frequency_hz in frequencies:
                if frequency_hz <= 0:
                    next_fire_at.pop(pin, None)
                    continue

                interval = 1 / frequency_hz
                scheduled = next_fire_at.get(pin, now + interval)
                if now < scheduled:
                    next_fire_at[pin] = scheduled
                    continue

                callback = self._input_callbacks.get(pin)
                if callable(callback):
                    callback()

                next_fire_at[pin] = now + interval

            time.sleep(0.001)
