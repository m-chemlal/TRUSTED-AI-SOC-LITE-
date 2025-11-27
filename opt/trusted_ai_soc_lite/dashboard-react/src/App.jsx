import React from 'react';
import { SummaryCards } from './components/SummaryCards.jsx';
import { CveDetails } from './components/CveDetails.jsx';
import { HostTable } from './components/HostTable.jsx';
import { RiskBars } from './components/RiskBars.jsx';
import { RiskDonut } from './components/RiskDonut.jsx';
import { useDashboardData } from './hooks/useDashboardData.js';

function Skeleton() {
  return <div style={{ color: '#94a3b8' }}>Loading data…</div>;
}

export default function App() {
  const { iaDecisions, responses, history, aggregates, loading } = useDashboardData();

  return (
    <div className="app-shell">
      <header className="header">
        <div>
          <p className="eyebrow">Trusted AI SOC Lite</p>
          <h1>Risk & Vulnerability Overview</h1>
          <small className="muted">Nmap → IA/XAI → Response — modern single-page view</small>
        </div>
        <div className="badge">Live</div>
      </header>

      {loading ? (
        <Skeleton />
      ) : (
        <>
          <SummaryCards aggregates={aggregates} totalHosts={iaDecisions.length} history={history} />

          <div className="grid two" style={{ marginTop: 18 }}>
            <RiskBars aggregates={aggregates} />
            <RiskDonut aggregates={aggregates} />
          </div>

          <div className="grid two" style={{ marginTop: 18 }}>
            <div className="card">
              <div className="section-title">
                <h3 style={{ margin: 0 }}>Latest actions</h3>
                <small>Response engine decisions</small>
              </div>
              {responses.length === 0 ? (
                <small className="muted">No actions recorded</small>
              ) : (
                <div className="scrollable">
                  <ul className="list compact">
                    {responses.map((r, idx) => (
                      <li key={`${r.ip}-${idx}`}>
                        <strong>{r.action}</strong> on <strong>{r.ip}</strong> — {r.risk_level}
                        {r.timestamp ? ` @ ${r.timestamp.replace('T', ' ').replace('Z', '')}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <CveDetails cveTable={aggregates.cveTable} />
          </div>

          <div style={{ marginTop: 18 }}>
            <HostTable iaDecisions={iaDecisions} />
          </div>

          <div className="footer-note">
            After each scan, run <code>./dashboard-react/sync_data.sh</code> then <code>npm run dev</code> to refresh
            this view with live data.
          </div>
        </>
      )}
    </div>
  );
}
