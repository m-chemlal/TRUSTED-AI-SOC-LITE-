import React from 'react';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

const palette = {
  critical: '#ef4444',
  high: '#fb923c',
  medium: '#f59e0b',
  low: '#22c55e',
};

export function RiskDonut({ aggregates }) {
  const total = Object.values(aggregates.byLevel || {}).reduce((a, b) => a + b, 0);
  const data = Object.entries(aggregates.byLevel || {}).map(([key, value]) => ({
    name: key,
    value,
    pct: total ? Math.round((value / total) * 100) : 0,
  }));

  return (
    <div className="card">
      <div className="section-title">
        <h3 style={{ margin: 0 }}>Risk distribution</h3>
        <small className="muted">Share of hosts by risk level</small>
      </div>
      <div className="donut-wrapper">
        <ResponsiveContainer>
          <PieChart>
            <Pie data={data} dataKey="value" innerRadius={60} outerRadius={90} paddingAngle={3}>
              {data.map((entry) => (
                <Cell key={`cell-${entry.name}`} fill={palette[entry.name]} />
              ))}
            </Pie>
            <Tooltip formatter={(v, n, p) => [`${v} hosts`, `${p.payload.pct}% ${p.payload.name}`]} />
          </PieChart>
        </ResponsiveContainer>
        <div className="donut-legend">
          {data.map((item) => (
            <div key={item.name} className="legend-row">
              <span className="dot" style={{ background: palette[item.name] }} />
              <div>
                <strong style={{ textTransform: 'capitalize' }}>{item.name}</strong>
                <p className="muted" style={{ margin: 0 }}>{item.pct}% of hosts</p>
              </div>
              <span className="legend-value">{item.value}</span>
            </div>
          ))}
          {data.length === 0 && <p className="muted" style={{ marginTop: 8 }}>No data yet</p>}
        </div>
      </div>
    </div>
  );
}
