const modules = [
  "Dashboard",
  "Trade",
  "Portfolio",
  "Watch",
  "AI Chat",
  "Reports",
  "Settings"
];

export default function Home() {
  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">Ledgerline</div>
        <div className="tagline">AI Trading Workspace</div>
        <nav>
          {modules.map((module) => (
            <a href="#" key={module}>
              {module}
            </a>
          ))}
        </nav>
      </aside>
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Phase 1 · Scaffold</p>
            <h1>Personal Trading Workspace</h1>
          </div>
          <span className="status">API ready check: /health</span>
        </header>
        <div className="grid">
          <article className="panel primary">
            <p className="label">Core Principle</p>
            <h2>Record facts. Compute everything else.</h2>
            <p>
              Ledgerline keeps positions, transactions, market data, reports, and AI context in
              separate layers so the workspace can grow without turning into an auto-trading box.
            </p>
          </article>
          <article className="panel">
            <p className="label">Next Build</p>
            <h2>Trade Entry</h2>
            <p>Market, symbol, action, price, quantity, optional note. The target is 20-30 seconds.</p>
          </article>
          <article className="panel">
            <p className="label">Backend</p>
            <h2>FastAPI Core</h2>
            <p>Trading, market data, indicators, strategies, AI triggers, reports, and watch modules.</p>
          </article>
        </div>
      </section>
    </main>
  );
}

