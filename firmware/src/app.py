from config import Settings


class FirmwareApp:
    def __init__(self, gpio_adapter: object, settings: Settings) -> None:
        self.gpio_adapter = gpio_adapter
        self.settings = settings

    def run(self) -> None:
        self.gpio_adapter.setup_output(self.settings.status_led_pin)
        self.gpio_adapter.write(self.settings.status_led_pin, True)
        print("Firmware scaffold started successfully.")
