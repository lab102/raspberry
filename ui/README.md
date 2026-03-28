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
