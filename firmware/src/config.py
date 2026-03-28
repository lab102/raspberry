from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    use_mock_gpio: bool = True
    status_led_pin: int = 23
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    stepper_pins: tuple[int, int, int, int] = (17, 18, 27, 22)
    step_delay_ms: float = 2.5
    steps_per_revolution: int = 2048


def load_settings() -> Settings:
    use_mock_gpio = os.getenv("RASPBERRY_USE_MOCK_GPIO", "true").lower() != "false"
    status_led_pin = int(os.getenv("RASPBERRY_STATUS_LED_PIN", "23"))
    api_host = os.getenv("RASPBERRY_API_HOST", "0.0.0.0")
    api_port = int(os.getenv("RASPBERRY_API_PORT", "8000"))
    step_delay_ms = float(os.getenv("RASPBERRY_STEPPER_DELAY_MS", "2.5"))
    steps_per_revolution = int(os.getenv("RASPBERRY_STEPPER_STEPS_PER_REV", "2048"))
    stepper_pins_raw = os.getenv("RASPBERRY_STEPPER_PINS", "17,18,27,22")
    stepper_pins = tuple(int(pin.strip()) for pin in stepper_pins_raw.split(","))

    if len(stepper_pins) != 4:
        raise ValueError("RASPBERRY_STEPPER_PINS must contain exactly four GPIO pins.")

    return Settings(
        use_mock_gpio=use_mock_gpio,
        status_led_pin=status_led_pin,
        api_host=api_host,
        api_port=api_port,
        stepper_pins=stepper_pins,
        step_delay_ms=step_delay_ms,
        steps_per_revolution=steps_per_revolution,
    )
