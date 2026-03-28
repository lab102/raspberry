from __future__ import annotations

from dataclasses import dataclass
import threading
import time


@dataclass
class StepperState:
    position_steps: int = 0
    enabled: bool = False
    is_moving: bool = False
    last_direction: str = "forward"
    last_step_count: int = 0
    total_steps_moved: int = 0
    mode: str = "idle"
    target_steps_per_second: float = 0.0


class StepperMotorController:
    _HALF_STEP_SEQUENCE = (
        (1, 0, 0, 0),
        (1, 1, 0, 0),
        (0, 1, 0, 0),
        (0, 1, 1, 0),
        (0, 0, 1, 0),
        (0, 0, 1, 1),
        (0, 0, 0, 1),
        (1, 0, 0, 1),
    )

    def __init__(
        self,
        gpio_adapter: object,
        pins: tuple[int, int, int, int],
        step_delay_ms: float,
        steps_per_revolution: int,
    ) -> None:
        self._gpio_adapter = gpio_adapter
        self._pins = pins
        self._step_delay_seconds = max(step_delay_ms, 0.5) / 1000
        self._steps_per_revolution = max(steps_per_revolution, 1)
        self._sequence_index = 0
        self._lock = threading.Lock()
        self._state = StepperState()
        self._manual_move_active = False
        self._continuous_direction = "forward"
        self._target_steps_per_second = 0.0
        self._running = True
        self._worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self._worker_thread.start()

    def setup(self) -> None:
        for pin in self._pins:
            self._gpio_adapter.setup_output(pin)
            self._gpio_adapter.write(pin, False)

    def get_state(self) -> dict[str, int | bool | str]:
        with self._lock:
            return {
                "position_steps": self._state.position_steps,
                "position_degrees": round(
                    (self._state.position_steps % self._steps_per_revolution)
                    * 360
                    / self._steps_per_revolution,
                    2,
                ),
                "enabled": self._state.enabled,
                "is_moving": self._state.is_moving,
                "last_direction": self._state.last_direction,
                "last_step_count": self._state.last_step_count,
                "total_steps_moved": self._state.total_steps_moved,
                "mode": self._state.mode,
                "target_steps_per_second": round(self._state.target_steps_per_second, 2),
                "step_delay_ms": round(self._step_delay_seconds * 1000, 2),
                "steps_per_revolution": self._steps_per_revolution,
                "pins": self._pins,
            }

    def move(self, direction: str, steps: int) -> dict[str, int | bool | str]:
        normalized_direction = direction.lower()
        if normalized_direction not in {"forward", "reverse"}:
            raise ValueError("direction must be 'forward' or 'reverse'")
        if steps <= 0:
            raise ValueError("steps must be greater than zero")

        with self._lock:
            if self._state.is_moving or self._state.mode == "sync":
                raise RuntimeError("Stepper motor is already moving.")
            self._state.is_moving = True
            self._state.enabled = True
            self._state.last_direction = normalized_direction
            self._state.last_step_count = steps
            self._state.mode = "manual"
            self._state.target_steps_per_second = 0.0
            self._manual_move_active = True

        step_increment = 1 if normalized_direction == "forward" else -1

        try:
            for _ in range(steps):
                self._apply_next_phase(step_increment)
                time.sleep(self._step_delay_seconds)
        finally:
            with self._lock:
                self._state.is_moving = False
                self._state.mode = "hold" if self._state.enabled else "idle"
                self._manual_move_active = False

        return self.get_state()

    def set_continuous_motion(self, direction: str, steps_per_second: float) -> dict[str, int | bool | str | float]:
        normalized_direction = direction.lower()
        if normalized_direction not in {"forward", "reverse"}:
            raise ValueError("direction must be 'forward' or 'reverse'")
        if steps_per_second < 0:
            raise ValueError("steps_per_second must be zero or greater")

        with self._lock:
            if self._manual_move_active:
                raise RuntimeError("Cannot enable sync while a manual move is active.")

            self._continuous_direction = normalized_direction
            self._target_steps_per_second = steps_per_second
            self._state.last_direction = normalized_direction
            self._state.enabled = steps_per_second > 0
            self._state.is_moving = steps_per_second > 0
            self._state.mode = "sync" if steps_per_second > 0 else "idle"
            self._state.target_steps_per_second = steps_per_second

        if steps_per_second == 0:
            self._de_energize_outputs()

        return self.get_state()

    def release(self) -> dict[str, int | bool | str]:
        with self._lock:
            self._target_steps_per_second = 0.0
            self._state.enabled = False
            self._state.is_moving = False
            self._state.mode = "idle"
            self._state.target_steps_per_second = 0.0

        self._de_energize_outputs()

        return self.get_state()

    def shutdown(self) -> None:
        self._running = False
        self._worker_thread.join(timeout=1)
        self._de_energize_outputs()

    def _run_worker(self) -> None:
        last_step_at = time.monotonic()

        while self._running:
            with self._lock:
                if self._manual_move_active:
                    target_steps_per_second = 0.0
                else:
                    target_steps_per_second = self._target_steps_per_second
                    direction = self._continuous_direction

            if target_steps_per_second <= 0:
                time.sleep(0.01)
                last_step_at = time.monotonic()
                continue

            interval = max(1 / target_steps_per_second, self._step_delay_seconds)
            now = time.monotonic()
            wait_time = interval - (now - last_step_at)
            if wait_time > 0:
                time.sleep(min(wait_time, 0.01))
                continue

            self._apply_next_phase(1 if direction == "forward" else -1)
            last_step_at = time.monotonic()

    def _apply_next_phase(self, step_increment: int) -> None:
        with self._lock:
            self._sequence_index = (
                self._sequence_index + step_increment
            ) % len(self._HALF_STEP_SEQUENCE)
            phase = self._HALF_STEP_SEQUENCE[self._sequence_index]

        for pin, value in zip(self._pins, phase):
            self._gpio_adapter.write(pin, bool(value))

        with self._lock:
            self._state.position_steps += step_increment
            self._state.total_steps_moved += 1

    def _de_energize_outputs(self) -> None:
        for pin in self._pins:
            self._gpio_adapter.write(pin, False)
