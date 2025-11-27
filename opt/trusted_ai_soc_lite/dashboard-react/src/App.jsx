import React from 'react';
import { SummaryCards } from './components/SummaryCards.jsx';
import { Trends } from './components/Trends.jsx';
import { CveDetails } from './components/CveDetails.jsx';
import { HostTable } from './components/HostTable.jsx';
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
          <h1>Trusted AI SOC Lite — React Dashboard</h1>
          <small style={{ color: '#94a3b8' }}>
            Live view of Nmap → IA/XAI → response (no SIEM required)
          </small>
        </div>
        <div className="badge">Live</div>
      </header>

      {loading ? (
        <Skeleton />
      ) : (
        <>
          <div className="grid two" style={{ marginTop: 18 }}>
            <SummaryCards aggregates={aggregates} totalHosts={iaDecisions.length} />
            <div className="card">
              <div className="section-title">
                <h3 style={{ margin: 0 }}>Latest actions</h3>
                <small>Response engine decisions</small>
              </div>
              {responses.length === 0 ? (
                <small style={{ color: '#94a3b8' }}>No actions recorded</small>
              ) : (
                <ul className="list">
                  {responses.map((r, idx) => (
                    <li key={`${r.ip}-${idx}`}>
                      <strong>{r.action}</strong> on <strong>{r.ip}</strong> — {r.risk_level}
                      {r.timestamp ? ` @ ${r.timestamp.replace('T', ' ').replace('Z', '')}` : ''}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="grid two" style={{ marginTop: 16 }}>
            <Trends history={history} />
            <CveDetails cveTable={aggregates.cveTable} />
          </div>

          <div style={{ marginTop: 16 }}>
            <HostTable iaDecisions={iaDecisions} />
          </div>

          <div className="footer-note">
            Tip: run <code>./run_all.sh --profile full</code> then <code>./dashboard-react/sync_data.sh</code> and
            <code> npm run dev</code> to refresh this UI with your latest scans.
          </div>
        </>
      )}
    </div>
  );
}
