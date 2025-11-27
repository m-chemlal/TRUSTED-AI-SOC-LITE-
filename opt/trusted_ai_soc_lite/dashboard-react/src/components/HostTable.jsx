import React from 'react';

const palette = {
  low: '#34d399',
  medium: '#fbbf24',
  high: '#fb923c',
  critical: '#f87171',
};

function riskPill(level) {
  const key = (level || '').toLowerCase();
  return (
    <span className={`pill ${key}`} style={{ minWidth: 82 }}>
      {level || 'n/a'}
    </span>
  );
}

export function HostTable({ iaDecisions }) {
  return (
    <div className="card">
      <div className="section-title">
        <h3 style={{ margin: 0 }}>Hosts</h3>
        <small>Latest IA verdict per host</small>
      </div>
      {iaDecisions.length === 0 ? (
        <small style={{ color: '#94a3b8' }}>No hosts scanned yet</small>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="table">
            <thead>
              <tr>
                <th>Host</th>
                <th>Risk</th>
                <th>Score</th>
                <th>Services</th>
                <th>Top findings</th>
                <th>Last seen</th>
              </tr>
            </thead>
            <tbody>
              {iaDecisions.map((row) => (
                <tr key={row.host}>
                  <td style={{ color: '#22d3ee', fontWeight: 600 }}>{row.host}</td>
                  <td>{riskPill(row.risk_level)}</td>
                  <td style={{ color: palette[(row.risk_level || '').toLowerCase()] || '#e2e8f0' }}>
                    {row.risk_score ?? '—'}
                  </td>
                  <td>
                    <ul className="list">
                      {(row.services || []).map((s) => (
                        <li key={`${row.host}-${s}`}>{s}</li>
                      ))}
                    </ul>
                  </td>
                  <td>
                    <ul className="list">
                      {(row.top_findings || []).map((f, idx) => (
                        <li key={`${row.host}-f-${idx}`}>{f}</li>
                      ))}
                    </ul>
                  </td>
                  <td>{row.timestamp ? row.timestamp.replace('T', ' ').replace('Z', '') : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
