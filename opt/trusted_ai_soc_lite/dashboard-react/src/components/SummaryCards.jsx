import React from 'react';

const palette = {
  low: '#34d399',
  medium: '#fbbf24',
  high: '#fb923c',
  critical: '#f87171',
};

export function SummaryCards({ aggregates, totalHosts }) {
  const items = [
    { label: 'Critical', key: 'critical' },
    { label: 'High', key: 'high' },
    { label: 'Medium', key: 'medium' },
    { label: 'Low', key: 'low' },
  ];
  return (
    <div className="grid four">
      {items.map((item) => (
        <div className="card" key={item.key}>
          <small>{item.label}</small>
          <div className="metrics">
            <span className="value" style={{ color: palette[item.key] }}>
              {aggregates.byLevel[item.key] || 0}
            </span>
            <span className="label">hosts</span>
          </div>
        </div>
      ))}
      <div className="card">
        <small>Avg. risk score</small>
        <div className="metrics">
          <span className="value">{aggregates.avgScore}</span>
          <span className="label">/ 100</span>
        </div>
        <div className="metrics" style={{ marginTop: 4 }}>
          <span className="label">Total hosts: {totalHosts}</span>
        </div>
      </div>
    </div>
  );
}
