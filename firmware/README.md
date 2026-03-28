# Firmware

Python scaffold for Raspberry-specific logic.

The current structure separates the application logic from the hardware adapter:

- `src/app.py`: high-level firmware workflow
- `src/config.py`: runtime configuration
- `src/hardware/gpio.py`: Raspberry GPIO adapter placeholder
- `src/hardware/mock_gpio.py`: local development adapter

## Run

```bash
python src/main.py
```

Set `RASPBERRY_USE_MOCK_GPIO=false` when running on the Raspberry Pi with a real GPIO implementation.
