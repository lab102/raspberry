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
- `POST /api/sync`: enable or tune sensor-to-stepper sync
- `POST /api/mock-sensor`: change the local mock sensor frequency in Hz

Environment variables:

- `RASPBERRY_USE_MOCK_GPIO=false` to use real Raspberry GPIO with `gpiozero`
- `RASPBERRY_API_PORT=8000` to change the API port
- `RASPBERRY_STEPPER_PINS=17,18,27,22` to set the four stepper GPIO pins
- `RASPBERRY_STEPPER_DELAY_MS=2.5` to tune the stepping speed
- `RASPBERRY_STEPPER_STEPS_PER_REV=2048` to match your motor/gearing
- `RASPBERRY_SENSOR_PIN=24` to select the sensor input pin
- `RASPBERRY_SENSOR_SAMPLE_WINDOW_SECONDS=1.0` to set the measurement window
- `RASPBERRY_SYNC_STEPS_PER_HZ=32` to convert sensor Hz to stepper steps/second
- `RASPBERRY_SYNC_DIRECTION=forward` to choose tracking direction
- `RASPBERRY_SYNC_MAX_STEPS_PER_SECOND=900` to cap the commanded stepper speed
- `RASPBERRY_MOCK_SENSOR_HZ=2` to set the local simulated pulse frequency

## Local simulation

1. Start the firmware in mock mode:

```bash
python src/main.py
```

2. In another terminal, launch the UI:

```bash
npm run dev
```

3. In the UI:

- set a mock frequency such as `5 Hz`
- enable sync
- choose `steps per sensor Hz`, for example `40`

At `5 Hz` and `40 steps/Hz`, the stepper target will become `200 steps/second`.
