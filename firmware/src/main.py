from app import FirmwareApp
from config import load_settings
from hardware.gpio import RaspberryGPIOAdapter
from hardware.mock_gpio import MockGPIOAdapter


def build_gpio_adapter(use_mock_gpio: bool) -> object:
    if use_mock_gpio:
        return MockGPIOAdapter()
    return RaspberryGPIOAdapter()


def main() -> None:
    settings = load_settings()
    gpio_adapter = build_gpio_adapter(settings.use_mock_gpio)
    app = FirmwareApp(gpio_adapter=gpio_adapter, settings=settings)
    app.run()


if __name__ == "__main__":
    main()
