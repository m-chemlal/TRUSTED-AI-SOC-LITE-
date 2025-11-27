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

function latestIso(timestamps = []) {
  const parsed = timestamps
    .filter(Boolean)
    .map((t) => Date.parse(t))
    .filter((n) => !Number.isNaN(n))
    .sort((a, b) => a - b);
  return parsed.length ? new Date(parsed.at(-1)).toISOString() : null;
}

export function useDashboardData() {
  const [iaDecisions, setIaDecisions] = useState([]);
  const [responses, setResponses] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [usingSamples, setUsingSamples] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      let usedSamples = false;
      try {
        const [ia, resp, hist] = await Promise.all([
          fetchJson(SOURCES.ia).catch(() => {
            usedSamples = true;
            return sampleIa;
          }),
          fetchJson(SOURCES.responses).catch(() => {
            usedSamples = true;
            return sampleResponses;
          }),
          fetchJson(SOURCES.history).catch(() => {
            usedSamples = true;
            return sampleHistory;
          }),
        ]);
        if (!cancelled) {
          setIaDecisions(Array.isArray(ia) ? ia : []);
          setResponses(Array.isArray(resp) ? resp : []);
          setHistory(Array.isArray(hist) ? hist : []);
          setUsingSamples(usedSamples);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err);
          setIaDecisions(sampleIa);
          setResponses(sampleResponses);
          setHistory(sampleHistory);
          setUsingSamples(true);
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
    const lastUpdated = latestIso([
      ...iaDecisions.map((i) => i.timestamp),
      ...history.map((h) => h.timestamp),
    ]);
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
  }, [history, iaDecisions]);

  return { iaDecisions, responses, history, aggregates, loading, error, usingSamples };
}
