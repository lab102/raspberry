# UI

React + TypeScript + Vite scaffold for the desktop UI running on a PC.

## Commands

```bash
npm install
npm run dev
```

The UI now talks to the firmware over HTTP by default at `http://localhost:8000`.

Set `VITE_FIRMWARE_BASE_URL` if the Raspberry is reachable at another host, for example:

```bash
VITE_FIRMWARE_BASE_URL=http://192.168.1.50:8000 npm run dev
```

For local simulation, keep the default `http://localhost:8000`, start the firmware in mock mode, then use the UI to:

- set the mock sensor frequency in Hz
- enable synchronization
- watch the reported sensor frequency and stepper target speed update live
