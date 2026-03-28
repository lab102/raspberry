from config import Settings
from sensor import SensorFrequencyMonitor, SensorStepperSynchronizer
from stepper import StepperMotorController


class FirmwareApp:
    def __init__(self, gpio_adapter: object, settings: Settings) -> None:
        self.gpio_adapter = gpio_adapter
        self.settings = settings
        self.stepper = StepperMotorController(
            gpio_adapter=gpio_adapter,
            pins=settings.stepper_pins,
            step_delay_ms=settings.step_delay_ms,
            steps_per_revolution=settings.steps_per_revolution,
        )
        self.sensor = SensorFrequencyMonitor(
            gpio_adapter=gpio_adapter,
            pin=settings.sensor_pin,
            sample_window_seconds=settings.sensor_sample_window_seconds,
        )
        self.synchronizer = SensorStepperSynchronizer(
            sensor_monitor=self.sensor,
            stepper_controller=self.stepper,
            direction=settings.sync_direction,
            steps_per_hz=settings.sync_steps_per_hz,
            max_steps_per_second=settings.sync_max_steps_per_second,
        )

    def run(self) -> None:
        self.gpio_adapter.setup_output(self.settings.status_led_pin)
        self.gpio_adapter.write(self.settings.status_led_pin, True)
        self.stepper.setup()
        self.sensor.setup()
        if self.settings.use_mock_gpio and hasattr(self.gpio_adapter, "set_mock_input_frequency"):
            self.gpio_adapter.set_mock_input_frequency(
                self.settings.sensor_pin, self.settings.mock_sensor_frequency_hz
            )
        print("Firmware scaffold started successfully.")

    def get_status(self) -> dict[str, object]:
        return {
            "connection": "online",
            "gpio_mode": "mock" if self.settings.use_mock_gpio else "raspberry",
            "status_led_pin": self.settings.status_led_pin,
            "sensor": self.sensor.get_state(),
            "sync": self.synchronizer.get_state(),
            "stepper": self.stepper.get_state(),
        }

    def update_sync(
        self,
        *,
        enabled: bool | None = None,
        direction: str | None = None,
        steps_per_hz: float | None = None,
        max_steps_per_second: float | None = None,
    ) -> dict[str, float | bool | str]:
        return self.synchronizer.update_settings(
            enabled=enabled,
            direction=direction,
            steps_per_hz=steps_per_hz,
            max_steps_per_second=max_steps_per_second,
        )

    def set_mock_sensor_frequency(self, frequency_hz: float) -> dict[str, int | float | None]:
        if not self.settings.use_mock_gpio or not hasattr(self.gpio_adapter, "set_mock_input_frequency"):
            raise RuntimeError("Mock sensor frequency control is only available in mock GPIO mode.")
        if frequency_hz < 0:
            raise ValueError("frequency_hz must be zero or greater")

        self.gpio_adapter.set_mock_input_frequency(self.settings.sensor_pin, frequency_hz)
        return self.sensor.get_state()
