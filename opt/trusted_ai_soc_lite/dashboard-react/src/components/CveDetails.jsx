import React, { useMemo, useState } from 'react';

export function CveDetails({ cveTable }) {
  const [query, setQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');

  const filteredRows = useMemo(() => {
    const q = query.trim().toLowerCase();
    return cveTable.filter((row) => {
      const matchesRisk =
        riskFilter === 'all' || (row.risk_level || '').toLowerCase() === riskFilter;
      const haystack = `${row.cve || ''} ${row.host || ''} ${row.top_findings || ''}`.toLowerCase();
      const matchesQuery = q ? haystack.includes(q) : true;
      return matchesRisk && matchesQuery;
    });
  }, [cveTable, query, riskFilter]);

  return (
    <div className="card">
      <div className="section-title">
        <h3 style={{ margin: 0 }}>CVE & TI snapshot</h3>
        <small>Recent CVE detections by host</small>
      </div>
      <div className="table-controls">
        <input
          className="input"
          type="search"
          placeholder="Filter by CVE or host"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select
          className="input"
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
        >
          <option value="all">All risks</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
      {filteredRows.length === 0 ? (
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
                {filteredRows.map((row, idx) => (
                  <tr key={`${row.cve}-${idx}`}>
                    <td style={{ color: '#22d3ee' }}>
                      {row.cve ? (
                        <a
                          href={`https://nvd.nist.gov/vuln/detail/${row.cve}`}
                          target="_blank"
                          rel="noreferrer"
                          className="cve-link"
                        >
                          {row.cve}
                        </a>
                      ) : (
                        '—'
                      )}
                    </td>
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
