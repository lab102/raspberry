# ProjRaspberry

Starter monorepo for a Raspberry-based system with two subprojects:

- `ui`: PC user interface
- `firmware`: Raspberry-specific runtime and hardware integration layer

## Structure

```text
.
|-- firmware
|   |-- README.md
|   `-- src
|       |-- hardware
|       |   |-- gpio.py
|       |   `-- mock_gpio.py
|       |-- app.py
|       |-- config.py
|       `-- main.py
`-- ui
    |-- README.md
    `-- src
```

## Getting started

### UI

```bash
npm install
npm run dev:ui
```

### Firmware

```bash
python firmware/src/main.py
```

The firmware project defaults to a mock GPIO adapter, so it can be developed on a normal PC before being moved to a Raspberry Pi.
