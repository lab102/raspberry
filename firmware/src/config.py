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
    sensor_pin: int = 24
    sensor_sample_window_seconds: float = 1.0
    sync_steps_per_hz: float = 32.0
    sync_direction: str = "forward"
    sync_max_steps_per_second: float = 900.0
    mock_sensor_frequency_hz: float = 2.0


def load_settings() -> Settings:
    use_mock_gpio = os.getenv("RASPBERRY_USE_MOCK_GPIO", "true").lower() != "false"
    status_led_pin = int(os.getenv("RASPBERRY_STATUS_LED_PIN", "23"))
    api_host = os.getenv("RASPBERRY_API_HOST", "0.0.0.0")
    api_port = int(os.getenv("RASPBERRY_API_PORT", "8000"))
    step_delay_ms = float(os.getenv("RASPBERRY_STEPPER_DELAY_MS", "2.5"))
    steps_per_revolution = int(os.getenv("RASPBERRY_STEPPER_STEPS_PER_REV", "2048"))
    stepper_pins_raw = os.getenv("RASPBERRY_STEPPER_PINS", "17,18,27,22")
    stepper_pins = tuple(int(pin.strip()) for pin in stepper_pins_raw.split(","))
    sensor_pin = int(os.getenv("RASPBERRY_SENSOR_PIN", "24"))
    sensor_sample_window_seconds = float(
        os.getenv("RASPBERRY_SENSOR_SAMPLE_WINDOW_SECONDS", "1.0")
    )
    sync_steps_per_hz = float(os.getenv("RASPBERRY_SYNC_STEPS_PER_HZ", "32.0"))
    sync_direction = os.getenv("RASPBERRY_SYNC_DIRECTION", "forward").lower()
    sync_max_steps_per_second = float(
        os.getenv("RASPBERRY_SYNC_MAX_STEPS_PER_SECOND", "900.0")
    )
    mock_sensor_frequency_hz = float(os.getenv("RASPBERRY_MOCK_SENSOR_HZ", "2.0"))

    if len(stepper_pins) != 4:
        raise ValueError("RASPBERRY_STEPPER_PINS must contain exactly four GPIO pins.")
    if sync_direction not in {"forward", "reverse"}:
        raise ValueError("RASPBERRY_SYNC_DIRECTION must be 'forward' or 'reverse'.")

    return Settings(
        use_mock_gpio=use_mock_gpio,
        status_led_pin=status_led_pin,
        api_host=api_host,
        api_port=api_port,
        stepper_pins=stepper_pins,
        step_delay_ms=step_delay_ms,
        steps_per_revolution=steps_per_revolution,
        sensor_pin=sensor_pin,
        sensor_sample_window_seconds=sensor_sample_window_seconds,
        sync_steps_per_hz=sync_steps_per_hz,
        sync_direction=sync_direction,
        sync_max_steps_per_second=sync_max_steps_per_second,
        mock_sensor_frequency_hz=mock_sensor_frequency_hz,
    )
