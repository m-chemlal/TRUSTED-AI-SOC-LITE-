import React from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

function formatDateLabel(ts) {
  if (!ts) return '';
  return ts.split('T')[0];
}

export function Trends({ history }) {
  const data = history
    .map((item) => ({ ...item, risk_score: Number(item.risk_score) || 0 }))
    .sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

  return (
    <div className="card">
      <div className="section-title">
        <h3 style={{ margin: 0 }}>Risk timeline</h3>
        <small>Risk score per scan</small>
      </div>
      {data.length === 0 ? (
        <small style={{ color: '#94a3b8' }}>No history yet</small>
      ) : (
        <div style={{ width: '100%', height: 220 }}>
          <ResponsiveContainer>
            <AreaChart data={data} margin={{ top: 10, right: 16, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id="risk" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="timestamp" tickFormatter={formatDateLabel} stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" domain={[0, 100]} />
              <Tooltip labelFormatter={formatDateLabel} formatter={(v) => [v, 'Risk score']} />
              <Area type="monotone" dataKey="risk_score" stroke="#22d3ee" fillOpacity={1} fill="url(#risk)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
