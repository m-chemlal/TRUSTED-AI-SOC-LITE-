import React from 'react';
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const palette = {
  critical: '#ef4444',
  high: '#fb923c',
  medium: '#f59e0b',
  low: '#22c55e',
};

export function RiskBars({ aggregates }) {
  const items = [
    { key: 'critical', label: 'Critical' },
    { key: 'high', label: 'High' },
    { key: 'medium', label: 'Medium' },
    { key: 'low', label: 'Low' },
  ];

  const data = items.map((item) => ({
    ...item,
    count: aggregates.byLevel[item.key] || 0,
  }));

  return (
    <div className="card">
      <div className="section-title">
        <h3 style={{ margin: 0 }}>Risk by stage</h3>
        <small className="muted">Snapshot of hosts per risk level</small>
      </div>
      <div style={{ width: '100%', height: 260 }}>
        <ResponsiveContainer>
          <BarChart data={data} margin={{ top: 10, right: 12, left: -16, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="label" stroke="#475569" />
            <YAxis stroke="#475569" allowDecimals={false} />
            <Tooltip formatter={(v) => [v, 'Hosts']} cursor={{ fill: 'rgba(22, 163, 74, 0.08)' }} />
            <Bar dataKey="count" radius={[12, 12, 0, 0]}>
              {data.map((entry, index) => (
                <Cell key={`cell-${entry.key}-${index}`} fill={palette[entry.key]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
