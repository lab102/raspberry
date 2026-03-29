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

The firmware now exposes a small HTTP API on `http://0.0.0.0:8000`:

- `GET /api/status`: firmware and sensor status, including firmware-generated timestamps
- `POST /api/mock-sensor`: change the local mock sensor frequency in Hz

Environment variables:

- `RASPBERRY_USE_MOCK_GPIO=false` to use real Raspberry GPIO with `gpiozero`
- `RASPBERRY_API_PORT=8000` to change the API port
- `RASPBERRY_SENSOR_PIN=24` to select the sensor input pin
- `RASPBERRY_SENSOR_SAMPLE_WINDOW_SECONDS=1.0` to set the measurement window
- `RASPBERRY_MOCK_SENSOR_HZ=5500` to set the mock sensor starting frequency in Hz
- `RASPBERRY_MOCK_SENSOR_GROWTH_RATE_PER_SECOND=0.001` to increase mock frequency by 0.1% per second

## Local simulation

1. Start the firmware in mock mode:

```bash
python src/main.py
```

2. In another terminal, launch the UI:

```bash
npm run dev
```

3. Open the UI to see connection status and the measured sensor frequency update live.

By default, mock mode starts near `5500 Hz` and ramps upward by `0.1%` per second. The measured frequency is still calculated in firmware from emitted pulse edges.
