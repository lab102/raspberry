import { FormEvent, useEffect, useMemo, useState } from "react";

type StepperState = {
  position_steps: number;
  position_degrees: number;
  enabled: boolean;
  is_moving: boolean;
  last_direction: string;
  last_step_count: number;
  total_steps_moved: number;
  step_delay_ms: number;
  steps_per_revolution: number;
  pins: number[];
};

type FirmwareStatus = {
  connection: string;
  gpio_mode: string;
  status_led_pin: number;
  stepper: StepperState;
};

const firmwareBaseUrl =
  import.meta.env.VITE_FIRMWARE_BASE_URL ?? "http://localhost:8000";

const jogPresets = [64, 128, 256, 512];

export function App() {
  const [status, setStatus] = useState<FirmwareStatus | null>(null);
  const [stepCount, setStepCount] = useState(256);
  const [loading, setLoading] = useState(true);
  const [actionBusy, setActionBusy] = useState(false);
  const [message, setMessage] = useState("Connecting to firmware...");
  const [error, setError] = useState<string | null>(null);

  const statusCards = useMemo(
    () => [
      { title: "Connection", value: status?.connection ?? "Offline" },
      { title: "GPIO Mode", value: status?.gpio_mode ?? "Unknown" },
      {
        title: "Position",
        value: status
          ? `${status.stepper.position_steps} steps / ${status.stepper.position_degrees} deg`
          : "Not synced"
      },
      {
        title: "Motor State",
        value: status?.stepper.is_moving
          ? "Moving"
          : status?.stepper.enabled
            ? "Holding torque"
            : "Released"
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
      setMessage("Firmware is online and ready for motor commands.");
      setError(null);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to reach firmware."
      );
      setMessage("Start the firmware API to enable stepper control.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshStatus();
    const timer = window.setInterval(() => {
      void refreshStatus();
    }, 2500);

    return () => window.clearInterval(timer);
  }, []);

  async function sendStepperCommand(
    path: string,
    body?: Record<string, number | string>
  ) {
    setActionBusy(true);
    setError(null);

    try {
      const response = await fetch(`${firmwareBaseUrl}${path}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: body ? JSON.stringify(body) : undefined
      });

      const payload = (await response.json()) as
        | { error: string }
        | { stepper: StepperState };

      if (!response.ok || "error" in payload) {
        throw new Error(
          "error" in payload ? payload.error : `Request failed with ${response.status}`
        );
      }

      setStatus((currentStatus) =>
        currentStatus
          ? { ...currentStatus, stepper: payload.stepper }
          : {
              connection: "online",
              gpio_mode: "unknown",
              status_led_pin: 0,
              stepper: payload.stepper
            }
      );
      setMessage("Stepper command completed successfully.");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Stepper command failed."
      );
    } finally {
      setActionBusy(false);
    }
  }

  async function handleMove(direction: "forward" | "reverse", steps = stepCount) {
    await sendStepperCommand("/api/stepper/move", { direction, steps });
  }

  async function handleRelease() {
    await sendStepperCommand("/api/stepper/release");
  }

  function handleStepSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void handleMove("forward");
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">Raspberry Stepper Console</p>
          <h1>Motor Control Station</h1>
          <p className="hero-copy">
            Drive the Raspberry-connected stepper motor from the desktop UI,
            monitor its live position, and send repeatable jog commands for
            testing or operation.
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
              <p className="panel-kicker">Command</p>
              <h2>Jog the stepper</h2>
            </div>
            <span className={loading ? "pill pill-warn" : "pill"}>
              {loading ? "Syncing" : "Live"}
            </span>
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
                  disabled={actionBusy}
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
                disabled={actionBusy}
                type="button"
                onClick={() => void handleMove("reverse")}
              >
                Reverse
              </button>
              <button className="action-button forward" disabled={actionBusy} type="submit">
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
          <h2>Motor feedback</h2>
          <dl className="telemetry-list">
            <div>
              <dt>GPIO pins</dt>
              <dd>{status?.stepper.pins.join(", ") ?? "n/a"}</dd>
            </div>
            <div>
              <dt>Steps per rev</dt>
              <dd>{status?.stepper.steps_per_revolution ?? "n/a"}</dd>
            </div>
            <div>
              <dt>Step delay</dt>
              <dd>{status?.stepper.step_delay_ms ?? "n/a"} ms</dd>
            </div>
            <div>
              <dt>Last move</dt>
              <dd>
                {status
                  ? `${status.stepper.last_direction} ${status.stepper.last_step_count} steps`
                  : "No command yet"}
              </dd>
            </div>
            <div>
              <dt>Total travel</dt>
              <dd>{status?.stepper.total_steps_moved ?? 0} steps</dd>
            </div>
            <div>
              <dt>Status LED pin</dt>
              <dd>{status?.status_led_pin ?? "n/a"}</dd>
            </div>
          </dl>
        </article>
      </section>

      <section className="panel footer-panel">
        <div>
          <p className="panel-kicker">Runtime</p>
          <h2>Firmware connection notes</h2>
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
            onClick={() => void handleMove("forward", 2048)}
          >
            Full rotation
          </button>
        </div>
      </section>
    </main>
  );
}
