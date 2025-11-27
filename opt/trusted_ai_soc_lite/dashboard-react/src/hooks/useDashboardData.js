import { useEffect, useMemo, useState } from 'react';
import sampleIa from '../sample/ia_decisions.sample.json';
import sampleResponses from '../sample/response_actions.sample.json';
import sampleHistory from '../sample/scan_history.sample.json';

const SOURCES = {
  ia: '/data/ia_decisions.json',
  responses: '/data/response_actions.json',
  history: '/data/scan_history.json',
};

async function fetchJson(path) {
  const res = await fetch(path, { cache: 'no-store' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export function useDashboardData() {
  const [iaDecisions, setIaDecisions] = useState([]);
  const [responses, setResponses] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const [ia, resp, hist] = await Promise.all([
          fetchJson(SOURCES.ia).catch(() => sampleIa),
          fetchJson(SOURCES.responses).catch(() => sampleResponses),
          fetchJson(SOURCES.history).catch(() => sampleHistory),
        ]);
        if (!cancelled) {
          setIaDecisions(Array.isArray(ia) ? ia : []);
          setResponses(Array.isArray(resp) ? resp : []);
          setHistory(Array.isArray(hist) ? hist : []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err);
          setIaDecisions(sampleIa);
          setResponses(sampleResponses);
          setHistory(sampleHistory);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const aggregates = useMemo(() => {
    const byLevel = iaDecisions.reduce(
      (acc, item) => {
        const lvl = (item.risk_level || '').toLowerCase();
        if (lvl in acc) acc[lvl] += 1;
        return acc;
      },
      { low: 0, medium: 0, high: 0, critical: 0 },
    );
    const avgScore = iaDecisions.length
      ? Math.round(
          iaDecisions.reduce((sum, i) => sum + (Number(i.risk_score) || 0), 0) /
            iaDecisions.length,
        )
      : 0;
    const lastUpdated = iaDecisions
      .map((i) => i.timestamp)
      .filter(Boolean)
      .sort()
      .at(-1);
    const cveTable = iaDecisions.flatMap((i) =>
      (i.cves || []).map((cve) => ({
        host: i.host,
        risk_level: i.risk_level,
        risk_score: i.risk_score,
        cve,
        timestamp: i.timestamp,
      })),
    );
    return { byLevel, avgScore, lastUpdated, cveTable };
  }, [iaDecisions]);

  return { iaDecisions, responses, history, aggregates, loading, error };
}
