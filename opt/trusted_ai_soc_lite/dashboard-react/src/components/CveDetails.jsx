import React from 'react';

export function CveDetails({ cveTable }) {
  return (
    <div className="card">
      <div className="section-title">
        <h3 style={{ margin: 0 }}>CVE & TI snapshot</h3>
        <small>Recent CVE detections by host</small>
      </div>
      {cveTable.length === 0 ? (
        <small style={{ color: '#94a3b8' }}>No CVE detected yet</small>
      ) : (
        <div className="table-scroll">
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  <th>CVE</th>
                  <th>Host</th>
                  <th>Risk</th>
                  <th>Score</th>
                  <th>Seen</th>
                </tr>
              </thead>
              <tbody>
                {cveTable.map((row, idx) => (
                  <tr key={`${row.cve}-${idx}`}>
                    <td style={{ color: '#22d3ee' }}>{row.cve}</td>
                    <td>{row.host}</td>
                    <td>
                      <span className={`pill ${row.risk_level?.toLowerCase() || ''}`}>
                        {row.risk_level || 'n/a'}
                      </span>
                    </td>
                    <td>{row.risk_score ?? '—'}</td>
                    <td>{row.timestamp ? row.timestamp.replace('T', ' ').replace('Z', '') : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
