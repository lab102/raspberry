from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    use_mock_gpio: bool = True
    status_led_pin: int = 23
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    sensor_pin: int = 24
    sensor_sample_window_seconds: float = 1.0
    mock_sensor_frequency_hz: float = 5500.0
    mock_sensor_growth_rate_per_second: float = 0.001


def load_settings() -> Settings:
    use_mock_gpio = os.getenv("RASPBERRY_USE_MOCK_GPIO", "true").lower() != "false"
    status_led_pin = int(os.getenv("RASPBERRY_STATUS_LED_PIN", "23"))
    api_host = os.getenv("RASPBERRY_API_HOST", "0.0.0.0")
    api_port = int(os.getenv("RASPBERRY_API_PORT", "8000"))
    sensor_pin = int(os.getenv("RASPBERRY_SENSOR_PIN", "24"))
    sensor_sample_window_seconds = float(
        os.getenv("RASPBERRY_SENSOR_SAMPLE_WINDOW_SECONDS", "1.0")
    )
    mock_sensor_frequency_hz = float(os.getenv("RASPBERRY_MOCK_SENSOR_HZ", "5500.0"))
    mock_sensor_growth_rate_per_second = float(
        os.getenv("RASPBERRY_MOCK_SENSOR_GROWTH_RATE_PER_SECOND", "0.001")
    )

    return Settings(
        use_mock_gpio=use_mock_gpio,
        status_led_pin=status_led_pin,
        api_host=api_host,
        api_port=api_port,
        sensor_pin=sensor_pin,
        sensor_sample_window_seconds=sensor_sample_window_seconds,
        mock_sensor_frequency_hz=mock_sensor_frequency_hz,
        mock_sensor_growth_rate_per_second=mock_sensor_growth_rate_per_second,
    )
