export default function HomePage() {
  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">CompliSense AI</p>
        <h1>EU AI Act Compliance in Minutes</h1>
        <p className="lede">
          Run privacy-safe scans locally, sync only the metadata you choose, and review compliance posture from a
          hosted SaaS dashboard.
        </p>
        <a className="cta" href="mailto:demo@complisense.ai?subject=Request%20Demo">
          Request Demo
        </a>
      </section>

      <section className="grid">
        <article className="card">
          <h2>Problem</h2>
          <p>
            Most AI teams cannot prove governance, documentation, and risk controls quickly enough for procurement,
            audits, or regulator scrutiny.
          </p>
        </article>
        <article className="card">
          <h2>How it works</h2>
          <ol>
            <li>Create a project in the SaaS dashboard.</li>
            <li>Download a customized local agent and run the scan inside client infrastructure.</li>
            <li>Upload scan metadata back to the dashboard for reports, tracking, and audit history.</li>
          </ol>
        </article>
        <article className="card">
          <h2>Why teams use it</h2>
          <p>They get a public-facing compliance workflow without moving model artefacts or sensitive data into the cloud.</p>
        </article>
      </section>
    </main>
  );
}
