# Firmware

Python scaffold for Raspberry-specific logic.

The current structure separates the application logic from the hardware adapter:

- `src/app.py`: high-level firmware workflow
- `src/config.py`: runtime configuration
- `src/hardware/gpio.py`: Raspberry GPIO adapter placeholder
- `src/hardware/mock_gpio.py`: local development adapter
- `src/stepper.py`: stepper motor control logic and state tracking

## Run

```bash
python src/main.py
```

The firmware now exposes a small HTTP API on `http://0.0.0.0:8000`:

- `GET /api/status`: firmware and motor status
- `POST /api/stepper/move`: move the motor with `{"direction":"forward","steps":256}`
- `POST /api/stepper/release`: release the motor coils

Environment variables:

- `RASPBERRY_USE_MOCK_GPIO=false` to use real Raspberry GPIO with `gpiozero`
- `RASPBERRY_API_PORT=8000` to change the API port
- `RASPBERRY_STEPPER_PINS=17,18,27,22` to set the four stepper GPIO pins
- `RASPBERRY_STEPPER_DELAY_MS=2.5` to tune the stepping speed
- `RASPBERRY_STEPPER_STEPS_PER_REV=2048` to match your motor/gearing
