import React from 'react';

const palette = {
  low: '#22c55e',
  medium: '#f59e0b',
  high: '#fb923c',
  critical: '#ef4444',
};

export function SummaryCards({ aggregates, totalHosts, history }) {
  const cards = [
    { label: 'Critical', value: aggregates.byLevel.critical || 0, accent: palette.critical },
    { label: 'High', value: aggregates.byLevel.high || 0, accent: palette.high },
    { label: 'Medium', value: aggregates.byLevel.medium || 0, accent: palette.medium },
    { label: 'Low', value: aggregates.byLevel.low || 0, accent: palette.low },
    {
      label: 'Avg. risk score',
      value: `${aggregates.avgScore}/100`,
      accent: '#0ea5e9',
      helper: `${totalHosts} hosts scanned`,
    },
  ];

  const lastScanIso = aggregates.lastUpdated || history?.map((h) => h.timestamp).sort().at(-1);
  const lastScan = lastScanIso ? new Date(lastScanIso).toISOString().replace('T', ' ').replace('Z', '') : null;

  return (
    <div className="grid five">
      {cards.map((card) => (
        <div className="card kpi" key={card.label}>
          <p className="muted" style={{ margin: 0 }}>{card.label}</p>
          <div className="metrics">
            <span className="value" style={{ color: card.accent }}>{card.value}</span>
          </div>
          {card.helper && <small className="muted">{card.helper}</small>}
        </div>
      ))}
      <div className="card kpi">
        <p className="muted" style={{ margin: 0 }}>Last update</p>
        <div className="metrics">
          <span className="value" style={{ color: '#10b981' }}>{lastScan || '—'}</span>
        </div>
        <small className="muted">Most recent IA decision</small>
      </div>
    </div>
  );
}
