import { FormEvent, useEffect, useMemo, useState } from "react";

type StepperState = {
  position_steps: number;
  position_degrees: number;
  enabled: boolean;
  is_moving: boolean;
  last_direction: string;
  last_step_count: number;
  total_steps_moved: number;
  mode: string;
  target_steps_per_second: number;
  step_delay_ms: number;
  steps_per_revolution: number;
  pins: number[];
};

type SensorState = {
  pin: number;
  frequency_hz: number;
  sample_window_seconds: number;
  pulse_count_in_window: number;
  last_rising_edge_age_seconds: number | null;
};

type SyncState = {
  enabled: boolean;
  direction: string;
  steps_per_hz: number;
  max_steps_per_second: number;
  target_steps_per_second: number;
};

type FirmwareStatus = {
  connection: string;
  gpio_mode: string;
  status_led_pin: number;
  sensor: SensorState;
  sync: SyncState;
  stepper: StepperState;
};

const firmwareBaseUrl =
  import.meta.env.VITE_FIRMWARE_BASE_URL ?? "http://localhost:8000";

const jogPresets = [64, 128, 256, 512];
const mockSensorPresets = [0.5, 1, 2, 5, 10];

export function App() {
  const [status, setStatus] = useState<FirmwareStatus | null>(null);
  const [stepCount, setStepCount] = useState(256);
  const [syncEnabled, setSyncEnabled] = useState(false);
  const [syncDirection, setSyncDirection] = useState<"forward" | "reverse">("forward");
  const [stepsPerHz, setStepsPerHz] = useState(32);
  const [maxStepsPerSecond, setMaxStepsPerSecond] = useState(900);
  const [mockFrequency, setMockFrequency] = useState(2);
  const [loading, setLoading] = useState(true);
  const [actionBusy, setActionBusy] = useState(false);
  const [message, setMessage] = useState("Connecting to firmware...");
  const [error, setError] = useState<string | null>(null);

  const statusCards = useMemo(
    () => [
      { title: "Connection", value: status?.connection ?? "Offline" },
      { title: "Sensor Hz", value: status ? `${status.sensor.frequency_hz} Hz` : "No data" },
      {
        title: "Sync Target",
        value: status ? `${status.sync.target_steps_per_second} steps/s` : "No data"
      },
      {
        title: "Motor State",
        value: status
          ? `${status.stepper.mode} / ${status.stepper.last_direction}`
          : "Unknown"
      }
    ],
    [status]
  );

  async function refreshStatus() {
    try {
      const response = await fetch(`${firmwareBaseUrl}/api/status`);
      if (!response.ok) {
        throw new Error(`Status request failed with ${response.status}`);
      }

      const payload = (await response.json()) as FirmwareStatus;
      setStatus(payload);
      setSyncEnabled(payload.sync.enabled);
      setSyncDirection(payload.sync.direction as "forward" | "reverse");
      setStepsPerHz(payload.sync.steps_per_hz);
      setMaxStepsPerSecond(payload.sync.max_steps_per_second);
      setMockFrequency(payload.sensor.frequency_hz || mockFrequency);
      setMessage("Firmware is online. Sensor frequency and stepper sync are live.");
      setError(null);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to reach firmware."
      );
      setMessage("Start the firmware API to enable the local simulation.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshStatus();
    const timer = window.setInterval(() => {
      void refreshStatus();
    }, 1000);

    return () => window.clearInterval(timer);
  }, []);

  async function sendJson<T>(path: string, body?: Record<string, unknown>) {
    const response = await fetch(`${firmwareBaseUrl}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: body ? JSON.stringify(body) : undefined
    });

    const payload = (await response.json()) as T & { error?: string };
    if (!response.ok || payload.error) {
      throw new Error(payload.error ?? `Request failed with ${response.status}`);
    }

    return payload;
  }

  async function withBusyAction(action: () => Promise<void>) {
    setActionBusy(true);
    setError(null);

    try {
      await action();
    } catch (requestError) {
      setError(
        requestError instanceof Error ? requestError.message : "Action failed."
      );
    } finally {
      setActionBusy(false);
    }
  }

  async function handleMove(direction: "forward" | "reverse", steps = stepCount) {
    await withBusyAction(async () => {
      const payload = await sendJson<{ stepper: StepperState }>("/api/stepper/move", {
        direction,
        steps
      });
      setStatus((currentStatus) =>
        currentStatus ? { ...currentStatus, stepper: payload.stepper } : currentStatus
      );
      setMessage("Manual stepper jog completed.");
    });
  }

  async function handleRelease() {
    await withBusyAction(async () => {
      const payload = await sendJson<{ stepper: StepperState }>("/api/stepper/release");
      setStatus((currentStatus) =>
        currentStatus ? { ...currentStatus, stepper: payload.stepper } : currentStatus
      );
      setMessage("Stepper coils released.");
    });
  }

  async function applySyncSettings(nextEnabled = syncEnabled) {
    await withBusyAction(async () => {
      const payload = await sendJson<{ sync: SyncState; stepper: StepperState }>("/api/sync", {
        enabled: nextEnabled,
        direction: syncDirection,
        steps_per_hz: stepsPerHz,
        max_steps_per_second: maxStepsPerSecond
      });
      setSyncEnabled(payload.sync.enabled);
      setStatus((currentStatus) =>
        currentStatus
          ? { ...currentStatus, sync: payload.sync, stepper: payload.stepper }
          : currentStatus
      );
      setMessage("Synchronization settings applied.");
    });
  }

  async function applyMockSensorFrequency(nextFrequency = mockFrequency) {
    await withBusyAction(async () => {
      const payload = await sendJson<{ sensor: SensorState }>("/api/mock-sensor", {
        frequency_hz: nextFrequency
      });
      setMockFrequency(nextFrequency);
      setStatus((currentStatus) =>
        currentStatus ? { ...currentStatus, sensor: payload.sensor } : currentStatus
      );
      setMessage("Mock sensor frequency updated.");
    });
  }

  function handleStepSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void handleMove("forward");
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Sensor To Stepper Sync</p>
          <h1>Frequency Tracking Console</h1>
          <p className="hero-copy">
            Measure a sensor pulse train on the Raspberry, convert that live frequency
            into a stepper speed target, and tune the whole loop locally with the mock
            simulator before moving onto hardware.
          </p>
        </div>

        <div className="hero-badge">
          <span>Firmware API</span>
          <strong>{firmwareBaseUrl}</strong>
        </div>
      </section>

      <section className="status-grid">
        {statusCards.map((card) => (
          <article className="status-card" key={card.title}>
            <span>{card.title}</span>
            <strong>{card.value}</strong>
          </article>
        ))}
      </section>

      <section className="control-grid">
        <article className="panel panel-accent">
          <div className="panel-heading">
            <div>
              <p className="panel-kicker">Synchronization</p>
              <h2>Sensor-driven motion</h2>
            </div>
            <span className={loading ? "pill pill-warn" : "pill"}>
              {loading ? "Syncing" : syncEnabled ? "Enabled" : "Ready"}
            </span>
          </div>

          <div className="control-form">
            <label htmlFor="sync-direction">Direction</label>
            <select
              id="sync-direction"
              className="numeric-input"
              value={syncDirection}
              onChange={(event) =>
                setSyncDirection(event.target.value as "forward" | "reverse")
              }
            >
              <option value="forward">Forward</option>
              <option value="reverse">Reverse</option>
            </select>

            <label htmlFor="steps-per-hz">Steps per sensor Hz</label>
            <input
              id="steps-per-hz"
              className="numeric-input"
              min={0}
              step={1}
              type="number"
              value={stepsPerHz}
              onChange={(event) => setStepsPerHz(Number(event.target.value) || 0)}
            />

            <label htmlFor="max-steps">Max steps per second</label>
            <input
              id="max-steps"
              className="numeric-input"
              min={1}
              step={10}
              type="number"
              value={maxStepsPerSecond}
              onChange={(event) => setMaxStepsPerSecond(Number(event.target.value) || 1)}
            />

            <div className="button-row">
              <button
                className="action-button forward"
                disabled={actionBusy}
                type="button"
                onClick={() => void applySyncSettings(true)}
              >
                Enable sync
              </button>
              <button
                className="action-button reverse"
                disabled={actionBusy}
                type="button"
                onClick={() => void applySyncSettings(false)}
              >
                Disable sync
              </button>
            </div>
          </div>
        </article>

        <article className="panel">
          <p className="panel-kicker">Simulation</p>
          <h2>Mock sensor source</h2>
          <div className="control-form">
            <label htmlFor="mock-frequency">Mock frequency (Hz)</label>
            <input
              id="mock-frequency"
              className="numeric-input"
              min={0}
              step={0.1}
              type="number"
              value={mockFrequency}
              onChange={(event) => setMockFrequency(Number(event.target.value) || 0)}
            />

            <div className="preset-row">
              {mockSensorPresets.map((preset) => (
                <button
                  className="preset-button"
                  disabled={actionBusy}
                  key={preset}
                  type="button"
                  onClick={() => setMockFrequency(preset)}
                >
                  {preset} Hz
                </button>
              ))}
            </div>

            <button
              className="secondary-button"
              disabled={actionBusy}
              type="button"
              onClick={() => void applyMockSensorFrequency()}
            >
              Apply sensor frequency
            </button>
          </div>
        </article>
      </section>

      <section className="control-grid secondary-grid">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="panel-kicker">Manual Control</p>
              <h2>Jog the stepper</h2>
            </div>
          </div>

          <form className="control-form" onSubmit={handleStepSubmit}>
            <label htmlFor="steps">Step count</label>
            <input
              id="steps"
              className="numeric-input"
              min={1}
              max={4096}
              step={1}
              type="number"
              value={stepCount}
              onChange={(event) => setStepCount(Number(event.target.value) || 1)}
            />

            <div className="preset-row">
              {jogPresets.map((preset) => (
                <button
                  className="preset-button"
                  disabled={actionBusy || syncEnabled}
                  key={preset}
                  type="button"
                  onClick={() => setStepCount(preset)}
                >
                  {preset} steps
                </button>
              ))}
            </div>

            <div className="button-row">
              <button
                className="action-button reverse"
                disabled={actionBusy || syncEnabled}
                type="button"
                onClick={() => void handleMove("reverse")}
              >
                Reverse
              </button>
              <button
                className="action-button forward"
                disabled={actionBusy || syncEnabled}
                type="submit"
              >
                Forward
              </button>
            </div>

            <button
              className="secondary-button"
              disabled={actionBusy}
              type="button"
              onClick={() => void handleRelease()}
            >
              Release coils
            </button>
          </form>
        </article>

        <article className="panel">
          <p className="panel-kicker">Telemetry</p>
          <h2>Signal and motion feedback</h2>
          <dl className="telemetry-list">
            <div>
              <dt>Sensor pin</dt>
              <dd>{status?.sensor.pin ?? "n/a"}</dd>
            </div>
            <div>
              <dt>Pulse count</dt>
              <dd>{status?.sensor.pulse_count_in_window ?? 0} / window</dd>
            </div>
            <div>
              <dt>Sensor age</dt>
              <dd>
                {status?.sensor.last_rising_edge_age_seconds ?? "n/a"} s since last pulse
              </dd>
            </div>
            <div>
              <dt>Stepper speed target</dt>
              <dd>{status?.stepper.target_steps_per_second ?? 0} steps/s</dd>
            </div>
            <div>
              <dt>Position</dt>
              <dd>
                {status
                  ? `${status.stepper.position_steps} steps / ${status.stepper.position_degrees} deg`
                  : "n/a"}
              </dd>
            </div>
            <div>
              <dt>GPIO pins</dt>
              <dd>{status?.stepper.pins.join(", ") ?? "n/a"}</dd>
            </div>
          </dl>
        </article>
      </section>

      <section className="panel footer-panel">
        <div>
          <p className="panel-kicker">Runtime</p>
          <h2>Simulation notes</h2>
          <p>{message}</p>
          {error ? <p className="error-text">{error}</p> : null}
        </div>
        <div className="button-row compact">
          <button className="secondary-button" type="button" onClick={() => void refreshStatus()}>
            Refresh status
          </button>
          <button
            className="secondary-button"
            disabled={actionBusy}
            type="button"
            onClick={() => void applyMockSensorFrequency(0)}
          >
            Stop mock pulses
          </button>
        </div>
      </section>
    </main>
  );
}
