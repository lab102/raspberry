import { useEffect, useState } from "react";

type SensorState = {
  pin: number;
  frequency_hz: number;
  sample_window_seconds: number;
  pulse_count_in_window: number;
  last_rising_edge_age_seconds: number | null;
  measured_at_unix_ms: number;
};

type FirmwareStatus = {
  connection: string;
  gpio_mode: string;
  status_led_pin: number;
  firmware_time_unix_ms: number;
  sensor: SensorState;
};

type PullLogEntry = {
  id: number;
  pulled_at_unix_ms: number;
  payload: FirmwareStatus;
};

const firmwareBaseUrl =
  import.meta.env.VITE_FIRMWARE_BASE_URL ?? "http://localhost:8000";

export function App() {
  const [status, setStatus] = useState<FirmwareStatus | null>(null);
  const [pullLogs, setPullLogs] = useState<PullLogEntry[]>([]);
  const [expandedLogIds, setExpandedLogIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [isPulling, setIsPulling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refreshStatus() {
    try {
      const response = await fetch(`${firmwareBaseUrl}/api/status`);
      if (!response.ok) {
        throw new Error(`Status request failed with ${response.status}`);
      }

      const payload = (await response.json()) as FirmwareStatus;
      setStatus(payload);
      setPullLogs((currentLogs) => {
        const nextEntry: PullLogEntry = {
          id: payload.sensor.measured_at_unix_ms,
          pulled_at_unix_ms: Date.now(),
          payload,
        };
        return [nextEntry, ...currentLogs];
      });
      setError(null);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to reach firmware."
      );
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!isPulling) {
      return;
    }

    setLoading(true);
    void refreshStatus();
    const timer = window.setInterval(refreshStatus, 1000);

    return () => window.clearInterval(timer);
  }, [isPulling]);

  function handleStart() {
    setError(null);
    setIsPulling(true);
  }

  function handleStop() {
    setIsPulling(false);
    setLoading(false);
  }

  function toggleLogEntry(id: number) {
    setExpandedLogIds((currentIds) =>
      currentIds.includes(id)
        ? currentIds.filter((currentId) => currentId !== id)
        : [...currentIds, id]
    );
  }

  function handleClearLogs() {
    setPullLogs([]);
    setExpandedLogIds([]);
  }

  return (
    <main className="app-shell">
      <div className="top-half">
        <section className="hero">
          <div>
            <p className="eyebrow">Firmware Sensor Monitor</p>
            <h1>Frequency Tracking Console</h1>
            <p className="hero-copy">
              The firmware measures sensor frequency on the device side. This UI only
              connects, polls the latest status, and displays the measured value with
              the firmware-reported timestamp.
            </p>
          </div>

          <div className="hero-badge">
            <span>Firmware API</span>
            <strong>{firmwareBaseUrl}</strong>
          </div>
        </section>

        <section className="status-grid">
        <article className="status-card">
          <span>Connection</span>
          <strong>
            {loading ? "Checking..." : status?.connection ?? "Offline"}
          </strong>
        </article>
          <article className="status-card">
            <span>Measured Frequency</span>
            <strong>{status ? `${status.sensor.frequency_hz.toFixed(3)} Hz` : "No data"}</strong>
          </article>
          <article className="status-card">
            <span>Firmware Timestamp</span>
            <strong>
              {status
                ? new Date(status.sensor.measured_at_unix_ms).toLocaleString()
                : "No data"}
            </strong>
          </article>
        </section>

      <section className="panel footer-panel">
        <div>
          <p className="panel-kicker">Runtime</p>
          <h2>Status</h2>
          {!status || !isPulling ? (
            <p>
              {status
                ? "Polling is stopped. Press Start to resume pulling firmware data."
                : "Press Start to begin pulling measured frequency data from the firmware."}
            </p>
          ) : null}
          {error ? <p className="error-text">{error}</p> : null}
        </div>
          <div className="button-row compact">
            <button
              className="secondary-button"
              disabled={isPulling}
              type="button"
              onClick={handleStart}
            >
              Start
            </button>
          <button
            className="secondary-button"
            disabled={!isPulling}
            type="button"
            onClick={handleStop}
          >
            Stop
          </button>
          <button className="secondary-button" type="button" onClick={handleClearLogs}>
            Clear logs
          </button>
        </div>
      </section>
      </div>

      <section className="panel log-panel">
        <div className="panel-header">
          <div>
            <p className="panel-kicker">Pull Logs</p>
          </div>
          <span className="terminal-badge">
            {pullLogs.length}
          </span>
        </div>
        <div className="log-window">
          {pullLogs.length === 0 ? (
            <p className="empty-log">No data pulled yet.</p>
          ) : (
            pullLogs.map((entry) => (
              <article className="log-entry" key={`${entry.id}-${entry.pulled_at_unix_ms}`}>
                <button
                  className="log-toggle"
                  type="button"
                  onClick={() => toggleLogEntry(entry.id)}
                >
                  <span className="log-toggle-left">
                    <span className="log-chevron">
                      {expandedLogIds.includes(entry.id) ? "[-]" : "[+]"}
                    </span>
                    <span>time {new Date(entry.payload.sensor.measured_at_unix_ms).toLocaleTimeString()}</span>
                  </span>
                  <span className="log-toggle-right">
                    freq {entry.payload.sensor.frequency_hz.toFixed(3)} Hz
                  </span>
                </button>
                {expandedLogIds.includes(entry.id) ? (
                  <pre className="log-payload">
                    {JSON.stringify(entry.payload, null, 2)}
                  </pre>
                ) : null}
              </article>
            ))
          )}
        </div>
      </section>
    </main>
  );
}
