from config import Settings
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

    def run(self) -> None:
        self.gpio_adapter.setup_output(self.settings.status_led_pin)
        self.gpio_adapter.write(self.settings.status_led_pin, True)
        self.stepper.setup()
        print("Firmware scaffold started successfully.")

    def get_status(self) -> dict[str, object]:
        return {
            "connection": "online",
            "gpio_mode": "mock" if self.settings.use_mock_gpio else "raspberry",
            "status_led_pin": self.settings.status_led_pin,
            "stepper": self.stepper.get_state(),
        }
