import type { ScannerOpportunity } from './types';

const BASE = '/api';

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const fetchScanner = () => fetchJSON<ScannerOpportunity[]>('/scanner');
