import React, { useMemo, useState } from 'react';
import { SummaryCards } from './components/SummaryCards.jsx';
import { CveDetails } from './components/CveDetails.jsx';
import { HostTable } from './components/HostTable.jsx';
import { RiskBars } from './components/RiskBars.jsx';
import { RiskDonut } from './components/RiskDonut.jsx';
import { computeAggregates, useDashboardData } from './hooks/useDashboardData.js';

function Skeleton() {
  return <div style={{ color: '#94a3b8' }}>Loading data…</div>;
}

export default function App() {
  const {
    iaDecisions,
    responses,
    history,
    scanOptions,
    loading,
    usingSamples,
    error,
  } = useDashboardData();

  const [selectedScan, setSelectedScan] = useState('all');

  const filteredHistory = useMemo(
    () => (selectedScan === 'all' ? history : history.filter((h) => h.scan_id === selectedScan)),
    [history, selectedScan],
  );

  const filteredIa = useMemo(
    () => (selectedScan === 'all' ? iaDecisions : iaDecisions.filter((item) => item.scan_id === selectedScan)),
    [iaDecisions, selectedScan],
  );

  const filteredResponses = useMemo(
    () => (selectedScan === 'all' ? responses : responses.filter((item) => item.scan_id === selectedScan)),
    [responses, selectedScan],
  );

  const scanLookup = useMemo(() => {
    const map = new Map();
    history.forEach((h) => {
      if (h.host) map.set(h.host, h.scan_id);
    });
    return map;
  }, [history]);

  const filteredAggregates = useMemo(
    () => computeAggregates(filteredIa, filteredHistory),
    [filteredHistory, filteredIa],
  );

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

      <div className="filter-card">
        <div className="filter-meta">
          <div className="pill">Scan</div>
          <p className="filter-title">Choose a scan run</p>
          <small className="muted">View aggregates for a specific execution or everything at once.</small>
        </div>
        <div className="filter-controls">
          <div className="select-shell">
            <span className="select-label">Scan</span>
            <select
              id="scan-select"
              className="select-control"
              value={selectedScan}
              onChange={(e) => setSelectedScan(e.target.value)}
            >
              <option value="all">All scans</option>
              {scanOptions.map((id) => (
                <option key={id} value={id}>
                  {id}
                </option>
              ))}
            </select>
            <span className="select-chevron">▾</span>
          </div>
          {selectedScan !== 'all' && (
            <button className="ghost" type="button" onClick={() => setSelectedScan('all')}>
              Reset
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <Skeleton />
      ) : (
        <>
          {(usingSamples || error) && (
            <div className={`callout ${error ? 'danger' : 'warning'}`}>
              <strong>{error ? 'Fallback mode:' : 'Sample data in use.'}</strong>{' '}
              {error
                ? 'Live data could not be loaded; showing bundled samples instead.'
                : 'Sync your latest audit JSONs via ./dashboard-react/sync_data.sh to replace the demo numbers.'}
            </div>
          )}

          <SummaryCards
            aggregates={filteredAggregates}
            totalHosts={filteredIa.length}
            history={filteredHistory}
          />

          <div className="grid two" style={{ marginTop: 18 }}>
            <RiskBars aggregates={filteredAggregates} />
            <RiskDonut aggregates={filteredAggregates} />
          </div>

          <div className="grid two" style={{ marginTop: 18 }}>
            <div className="card">
              <div className="section-title">
                <h3 style={{ margin: 0 }}>Latest actions</h3>
                <small>Response engine decisions</small>
              </div>
              {filteredResponses.length === 0 ? (
                <small className="muted">No actions recorded for this view</small>
              ) : (
                <div className="scrollable">
                  <ul className="list compact">
                    {filteredResponses.map((r, idx) => (
                      <li key={`${r.ip}-${idx}`}>
                        <strong>{r.action}</strong> on <strong>{r.ip}</strong> — {r.risk_level}
                        {r.timestamp ? ` @ ${r.timestamp.replace('T', ' ').replace('Z', '')}` : ''}
                        {r.scan_id ? ` (scan ${r.scan_id})` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <CveDetails cveTable={filteredAggregates.cveTable} />
          </div>

          <div style={{ marginTop: 18 }}>
            <HostTable iaDecisions={filteredIa} scanLookup={scanLookup} />
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
