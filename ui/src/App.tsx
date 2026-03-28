const deviceCards = [
  { title: "Connection", value: "Waiting for Raspberry" },
  { title: "GPIO Mode", value: "Mock adapter" },
  { title: "Last Sync", value: "Not started" }
];

export function App() {
  return (
    <main className="app-shell">
      <section className="hero">
        <p className="eyebrow">PC Control Panel</p>
        <h1>ProjRaspberry</h1>
        <p className="hero-copy">
          Desktop UI scaffold for monitoring and controlling a Raspberry-based
          device runtime.
        </p>
      </section>

      <section className="status-grid">
        {deviceCards.map((card) => (
          <article className="status-card" key={card.title}>
            <span>{card.title}</span>
            <strong>{card.value}</strong>
          </article>
        ))}
      </section>

      <section className="panel">
        <h2>Next steps</h2>
        <p>
          Connect this UI to the firmware service using HTTP, WebSocket, or a
          custom protocol once the Raspberry runtime is ready.
        </p>
      </section>
    </main>
  );
}
