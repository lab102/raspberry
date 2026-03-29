from config import Settings
from sensor import SensorFrequencyMonitor


class FirmwareApp:
    def __init__(self, gpio_adapter: object, settings: Settings) -> None:
        self.gpio_adapter = gpio_adapter
        self.settings = settings
        self.sensor = SensorFrequencyMonitor(
            gpio_adapter=gpio_adapter,
            pin=settings.sensor_pin,
            sample_window_seconds=settings.sensor_sample_window_seconds,
        )

    def run(self) -> None:
        self.gpio_adapter.setup_output(self.settings.status_led_pin)
        self.gpio_adapter.write(self.settings.status_led_pin, True)
        self.sensor.setup()
        if self.settings.use_mock_gpio:
            if hasattr(self.gpio_adapter, "configure_mock_input_ramp"):
                self.gpio_adapter.configure_mock_input_ramp(
                    self.settings.sensor_pin,
                    self.settings.mock_sensor_frequency_hz,
                    self.settings.mock_sensor_growth_rate_per_second,
                )
            elif hasattr(self.gpio_adapter, "set_mock_input_frequency"):
                self.gpio_adapter.set_mock_input_frequency(
                    self.settings.sensor_pin, self.settings.mock_sensor_frequency_hz
                )
        print("Firmware scaffold started successfully.")

    def get_status(self) -> dict[str, object]:
        sensor_state = self.sensor.get_state()
        return {
            "connection": "online",
            "gpio_mode": "mock" if self.settings.use_mock_gpio else "raspberry",
            "status_led_pin": self.settings.status_led_pin,
            "firmware_time_unix_ms": sensor_state["measured_at_unix_ms"],
            "sensor": sensor_state,
        }

    def set_mock_sensor_frequency(self, frequency_hz: float) -> dict[str, int | float | None]:
        if not self.settings.use_mock_gpio or not hasattr(self.gpio_adapter, "set_mock_input_frequency"):
            raise RuntimeError("Mock sensor frequency control is only available in mock GPIO mode.")
        if frequency_hz < 0:
            raise ValueError("frequency_hz must be zero or greater")

        self.gpio_adapter.set_mock_input_frequency(self.settings.sensor_pin, frequency_hz)
        return self.sensor.get_state()
