from __future__ import annotations

from app import FirmwareApp
from config import load_settings
from hardware.gpio import RaspberryGPIOAdapter
from hardware.mock_gpio import MockGPIOAdapter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json


def build_gpio_adapter(use_mock_gpio: bool) -> object:
    if use_mock_gpio:
        return MockGPIOAdapter()
    return RaspberryGPIOAdapter()


def create_handler(app: FirmwareApp) -> type[BaseHTTPRequestHandler]:
    class FirmwareRequestHandler(BaseHTTPRequestHandler):
        def do_OPTIONS(self) -> None:  # noqa: N802
            self.send_response(HTTPStatus.NO_CONTENT)
            self._send_common_headers()
            self.end_headers()

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/api/status":
                self._send_json(HTTPStatus.OK, app.get_status())
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/api/stepper/move":
                payload = self._read_json_body()
                if payload is None:
                    return

                try:
                    state = app.stepper.move(
                        direction=str(payload.get("direction", "forward")),
                        steps=int(payload.get("steps", 0)),
                    )
                except (ValueError, RuntimeError) as error:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                    return

                self._send_json(HTTPStatus.OK, {"stepper": state})
                return

            if self.path == "/api/stepper/release":
                state = app.stepper.release()
                self._send_json(HTTPStatus.OK, {"stepper": state})
                return

            if self.path == "/api/sync":
                payload = self._read_json_body()
                if payload is None:
                    return

                try:
                    sync_state = app.update_sync(
                        enabled=payload.get("enabled"),
                        direction=payload.get("direction"),
                        steps_per_hz=float(payload["steps_per_hz"])
                        if "steps_per_hz" in payload
                        else None,
                        max_steps_per_second=float(payload["max_steps_per_second"])
                        if "max_steps_per_second" in payload
                        else None,
                    )
                except (ValueError, RuntimeError) as error:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                    return

                self._send_json(HTTPStatus.OK, {"sync": sync_state, "stepper": app.stepper.get_state()})
                return

            if self.path == "/api/mock-sensor":
                payload = self._read_json_body()
                if payload is None:
                    return

                try:
                    sensor_state = app.set_mock_sensor_frequency(float(payload.get("frequency_hz", 0.0)))
                except (ValueError, RuntimeError) as error:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                    return

                self._send_json(HTTPStatus.OK, {"sensor": sensor_state})
                return

            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

        def log_message(self, format: str, *args: object) -> None:
            print(f"[firmware-api] {self.address_string()} - {format % args}")

        def _read_json_body(self) -> dict[str, object] | None:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Request body is required"})
                return None

            raw_body = self.rfile.read(content_length)
            try:
                return json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON payload"})
                return None

        def _send_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
            encoded = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self._send_common_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_common_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")

    return FirmwareRequestHandler


def main() -> None:
    settings = load_settings()
    gpio_adapter = build_gpio_adapter(settings.use_mock_gpio)
    app = FirmwareApp(gpio_adapter=gpio_adapter, settings=settings)
    app.run()
    server = ThreadingHTTPServer((settings.api_host, settings.api_port), create_handler(app))
    print(f"Firmware API listening on http://{settings.api_host}:{settings.api_port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
