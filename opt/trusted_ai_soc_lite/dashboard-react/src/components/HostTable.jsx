import React from 'react';

export function HostTable({ iaDecisions }) {
  return (
    <div className="card">
      <div className="section-title">
        <h3 style={{ margin: 0 }}>My Hosts</h3>
        <small className="muted">Latest IA verdict per asset</small>
      </div>
      {iaDecisions.length === 0 ? (
        <small className="muted">No hosts scanned yet</small>
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
                  <td className="host-name">{row.host}</td>
                  <td>
                    <span className={`pill ${(row.risk_level || '').toLowerCase()}`} style={{ minWidth: 90 }}>
                      {row.risk_level || 'n/a'}
                    </span>
                  </td>
                  <td className={`score ${(row.risk_level || '').toLowerCase()}`}>{row.risk_score ?? '—'}</td>
                  <td>
                    <ul className="list compact">
                      {(row.services || []).map((s) => (
                        <li key={`${row.host}-${s}`}>{s}</li>
                      ))}
                    </ul>
                  </td>
                  <td>
                    <ul className="list compact">
                      {(row.top_findings || []).map((f, idx) => (
                        <li key={`${row.host}-f-${idx}`}>{f}</li>
                      ))}
                    </ul>
                  </td>
                  <td className="muted">{row.timestamp ? row.timestamp.replace('T', ' ').replace('Z', '') : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
