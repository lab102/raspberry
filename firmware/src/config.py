from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    use_mock_gpio: bool = True
    status_led_pin: int = 18


def load_settings() -> Settings:
    use_mock_gpio = os.getenv("RASPBERRY_USE_MOCK_GPIO", "true").lower() != "false"
    status_led_pin = int(os.getenv("RASPBERRY_STATUS_LED_PIN", "18"))
    return Settings(use_mock_gpio=use_mock_gpio, status_led_pin=status_led_pin)
