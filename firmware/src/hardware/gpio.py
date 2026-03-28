from __future__ import annotations

from typing import Any

try:
    from gpiozero import OutputDevice
except ImportError:  # pragma: no cover - exercised on Raspberry Pi
    OutputDevice = None


class RaspberryGPIOAdapter:
    def __init__(self) -> None:
        self._pins: dict[int, Any] = {}

    def setup_output(self, pin: int) -> None:
        if pin in self._pins:
            return

        if OutputDevice is None:
            raise RuntimeError(
                "gpiozero is not installed. Install it on the Raspberry Pi or set "
                "RASPBERRY_USE_MOCK_GPIO=true for local development."
            )

        self._pins[pin] = OutputDevice(pin=pin, initial_value=False)

    def write(self, pin: int, value: bool) -> None:
        if pin not in self._pins:
            self.setup_output(pin)

        device = self._pins[pin]
        if value:
            device.on()
            return

        device.off()
