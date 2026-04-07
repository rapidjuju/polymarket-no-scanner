import { useState, useMemo } from 'react';
import { Target } from 'lucide-react';
import type { NoScannerOpportunity } from '../lib/types';

interface ScannerTableProps {
  opportunities: NoScannerOpportunity[];
}

type SortKey =
  | 'yes_sticker_price'
  | 'no_sticker_price'
  | 'no_ask_price'
  | 'gross_return_pct'
  | 'net_return_pct'
  | 'days_to_expiry'
  | 'daily_return_pct'
  | 'annualized_excess_return_pct'
  | 'liquidity_usd'
  | 'volume'
  | 'slippage_bps'
  | 'price_impact_bps';

export function ScannerTable({ opportunities }: ScannerTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('annualized_excess_return_pct');
  const [sortAsc, setSortAsc] = useState(false);
  const [minNoPrice, setMinNoPrice] = useState<number>(0);
  const [minVolume, setMinVolume] = useState<number>(0);
  const [minDepth, setMinDepth] = useState<number>(0);

  // All unique categories from the data
  const allCategories = useMemo(() => {
    return Array.from(new Set(opportunities.map((o) => o.category))).sort();
  }, [opportunities]);

  // Track which categories are enabled (all on by default)
  const [enabledCategories, setEnabledCategories] = useState<Set<string> | null>(null);

  // Resolve: null = all enabled, otherwise use the set
  const activeCats = enabledCategories ?? new Set(allCategories);

  const toggleCategory = (cat: string) => {
    const current = new Set(activeCats);
    if (current.has(cat)) {
      current.delete(cat);
    } else {
      current.add(cat);
    }
    setEnabledCategories(current);
  };

  const toggleAll = () => {
    if (activeCats.size === allCategories.length) {
      // All on -> turn all off
      setEnabledCategories(new Set());
    } else {
      // Some off -> turn all on
      setEnabledCategories(null);
    }
  };

  const filtered = useMemo(() => {
    let data = opportunities;
    data = data.filter((o) => activeCats.has(o.category));
    if (minNoPrice > 0) {
      data = data.filter((o) => o.no_ask_price * 100 >= minNoPrice);
    }
    if (minVolume > 0) {
      data = data.filter((o) => o.volume >= minVolume);
    }
    if (minDepth > 0) {
      data = data.filter((o) => o.liquidity_usd >= minDepth);
    }
    return [...data].sort((a, b) => {
      const mul = sortAsc ? 1 : -1;
      return mul * ((a[sortKey] as number) - (b[sortKey] as number));
    });
  }, [opportunities, activeCats, minNoPrice, minVolume, minDepth, sortKey, sortAsc]);

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  const th =
    'px-3 py-2 text-left text-[10px] font-medium text-[var(--hl-text-dim)] uppercase tracking-wider';

  const SortHeader = ({ label, field }: { label: string; field: SortKey }) => (
    <th
      className={`${th} cursor-pointer hover:text-[var(--hl-text)] select-none whitespace-nowrap`}
      onClick={() => handleSort(field)}
    >
      {label} {sortKey === field ? (sortAsc ? '\u25B2' : '\u25BC') : ''}
    </th>
  );

  const fmtDollars = (v: number) =>
    v >= 1_000_000
      ? `$${(v / 1_000_000).toFixed(1)}M`
      : v >= 1_000
        ? `$${(v / 1_000).toFixed(0)}K`
        : `$${v.toFixed(0)}`;

  const returnColor = (v: number) =>
    v >= 20
      ? 'text-[var(--hl-green)] font-bold'
      : v >= 10
        ? 'text-[var(--hl-green)]'
        : v >= 0
          ? 'text-[var(--hl-text)]'
          : 'text-[var(--hl-red)]';

  const impactColor = (bps: number) =>
    bps === 0
      ? 'text-[var(--hl-green)]'
      : bps <= 50
        ? 'text-[var(--hl-text)]'
        : bps <= 200
          ? 'text-[var(--hl-yellow)]'
          : 'text-[var(--hl-red)] font-bold';

  const inputClass =
    'bg-[var(--hl-bg)] border border-[var(--hl-border)] text-[var(--hl-text)] text-[10px] px-2 py-1 w-20 font-mono focus:outline-none focus:border-[var(--hl-accent)]';

  return (
    <div
      className="flex flex-col h-full bg-[var(--hl-surface)] border border-[var(--hl-border)] overflow-hidden"
      style={{ borderRadius: 'var(--hl-radius)' }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-2.5 border-b border-[var(--hl-border)]">
        <Target className="w-3.5 h-3.5 text-[var(--hl-yellow)]" />
        <h2 className="text-xs font-semibold text-[var(--hl-text)]">
          NO Share Scanner
        </h2>
        <span className="ml-auto text-[10px] text-[var(--hl-text-dim)]">
          {filtered.length} of {opportunities.length} opportunities
        </span>
      </div>

      {/* Filters row */}
      <div className="flex items-center gap-4 px-3 py-2 border-b border-[var(--hl-border)]">
        {/* Category toggles */}
        <div className="flex gap-1 overflow-x-auto">
          <button
            onClick={toggleAll}
            className={`px-2 py-1 text-[9px] font-medium whitespace-nowrap transition-colors ${
              activeCats.size === allCategories.length
                ? 'bg-[var(--hl-accent)]/15 text-[var(--hl-accent)] border border-[var(--hl-accent)]/30'
                : 'text-[var(--hl-text-dim)] hover:text-[var(--hl-text)] hover:bg-[var(--hl-surface2)] border border-transparent'
            }`}
            style={{ borderRadius: 'var(--hl-radius)' }}
          >
            ALL
          </button>
          {allCategories.map((cat) => {
            const isOn = activeCats.has(cat);
            const count = opportunities.filter((o) => o.category === cat).length;
            return (
              <button
                key={cat}
                onClick={() => toggleCategory(cat)}
                className={`px-2 py-1 text-[9px] font-medium whitespace-nowrap transition-colors ${
                  isOn
                    ? 'bg-[var(--hl-accent)]/15 text-[var(--hl-accent)] border border-[var(--hl-accent)]/30'
                    : 'text-[var(--hl-text-dim)] line-through opacity-50 hover:opacity-80 hover:bg-[var(--hl-surface2)] border border-transparent'
                }`}
                style={{ borderRadius: 'var(--hl-radius)' }}
              >
                {cat}
                <span className="ml-1 opacity-60">{count}</span>
              </button>
            );
          })}
        </div>

        <div className="ml-auto flex items-center gap-3">
          {/* Min NO price filter */}
          <div className="flex items-center gap-1.5">
            <label className="text-[9px] text-[var(--hl-text-dim)] whitespace-nowrap">
              Min NO price
            </label>
            <input
              type="number"
              min={0}
              max={99}
              step={5}
              value={minNoPrice || ''}
              placeholder="0"
              onChange={(e) => setMinNoPrice(Number(e.target.value) || 0)}
              className={inputClass}
              style={{ borderRadius: 'var(--hl-radius)' }}
            />
            <span className="text-[9px] text-[var(--hl-text-dim)]">¢</span>
          </div>

          {/* Min volume filter */}
          <div className="flex items-center gap-1.5">
            <label className="text-[9px] text-[var(--hl-text-dim)] whitespace-nowrap">
              Min volume
            </label>
            <input
              type="number"
              min={0}
              step={10000}
              value={minVolume || ''}
              placeholder="0"
              onChange={(e) => setMinVolume(Number(e.target.value) || 0)}
              className={inputClass}
              style={{ borderRadius: 'var(--hl-radius)' }}
            />
            <span className="text-[9px] text-[var(--hl-text-dim)]">$</span>
          </div>

          {/* Min depth filter */}
          <div className="flex items-center gap-1.5">
            <label className="text-[9px] text-[var(--hl-text-dim)] whitespace-nowrap">
              Min depth
            </label>
            <input
              type="number"
              min={0}
              step={1000}
              value={minDepth || ''}
              placeholder="0"
              onChange={(e) => setMinDepth(Number(e.target.value) || 0)}
              className={inputClass}
              style={{ borderRadius: 'var(--hl-radius)' }}
            />
            <span className="text-[9px] text-[var(--hl-text-dim)]">$</span>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-[var(--hl-text-dim)] py-12">
            <Target className="w-6 h-6 mb-2 opacity-30" />
            <p className="text-xs">No opportunities found</p>
            <p className="text-[10px] mt-1 opacity-60">
              {opportunities.length > 0
                ? 'Try lowering your filters'
                : 'Waiting for scanner data...'}
            </p>
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-[var(--hl-surface)] z-10">
              <tr className="border-b border-[var(--hl-border)]">
                <th className={th}>Market</th>
                <SortHeader label="Sticker YES" field="yes_sticker_price" />
                <SortHeader label="Sticker NO" field="no_sticker_price" />
                <SortHeader label="NO Ask" field="no_ask_price" />
                <SortHeader label="Gross %" field="gross_return_pct" />
                <SortHeader label="Net %" field="net_return_pct" />
                <SortHeader label="Days" field="days_to_expiry" />
                <SortHeader label="Daily %" field="daily_return_pct" />
                <SortHeader label="Ann. Excess %" field="annualized_excess_return_pct" />
                <SortHeader label="$1K Slip" field="slippage_bps" />
                <SortHeader label="$1K Impact" field="price_impact_bps" />
                <SortHeader label="Depth" field="liquidity_usd" />
                <SortHeader label="Volume" field="volume" />
                <th className={th}>Cat.</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((o, i) => (
                <tr
                  key={`${o.market_id}-${i}`}
                  className="border-b border-[var(--hl-border)]/50 hover:bg-[var(--hl-surface2)]/50 transition-colors"
                >
                  {/* Market */}
                  <td className="px-3 py-2 max-w-[280px]">
                    <div
                      className="text-[11px] text-[var(--hl-text)] truncate"
                      title={o.question}
                    >
                      {o.question}
                    </div>
                    <div className="text-[9px] text-[var(--hl-text-dim)]">
                      {new Date(o.end_date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                      {o.holding_reward_eligible && (
                        <span className="ml-1.5 text-[var(--hl-yellow)]">4% reward</span>
                      )}
                    </div>
                  </td>

                  {/* Sticker YES */}
                  <td className="px-3 py-2 font-mono text-[11px]">
                    <span className="text-[var(--hl-blue)]">
                      {(o.yes_sticker_price * 100).toFixed(1)}%
                    </span>
                  </td>

                  {/* Sticker NO */}
                  <td className="px-3 py-2 font-mono text-[11px] text-[var(--hl-text-dim)]">
                    {(o.no_sticker_price * 100).toFixed(1)}%
                  </td>

                  {/* NO Ask */}
                  <td className="px-3 py-2 font-mono text-[11px]">
                    <span className="text-[var(--hl-purple)]">
                      {(o.no_ask_price * 100).toFixed(1)}¢
                    </span>
                  </td>

                  {/* Gross Return */}
                  <td className="px-3 py-2 font-mono text-[11px] text-[var(--hl-text-dim)]">
                    {o.gross_return_pct.toFixed(1)}%
                  </td>

                  {/* Net Return */}
                  <td className="px-3 py-2 font-mono text-[11px] text-[var(--hl-text-dim)]">
                    {o.net_return_pct.toFixed(1)}%
                  </td>

                  {/* Days to Expiry */}
                  <td
                    className={`px-3 py-2 font-mono text-[11px] ${
                      o.days_to_expiry < 7
                        ? 'text-[var(--hl-red)] font-bold'
                        : o.days_to_expiry < 30
                          ? 'text-[var(--hl-yellow)]'
                          : 'text-[var(--hl-text-dim)]'
                    }`}
                  >
                    {o.days_to_expiry}
                  </td>

                  {/* Daily Return */}
                  <td
                    className={`px-3 py-2 font-mono text-[11px] ${returnColor(o.daily_return_pct * 100)}`}
                  >
                    {o.daily_return_pct < 1
                      ? o.daily_return_pct.toFixed(3)
                      : o.daily_return_pct.toFixed(1)}%
                  </td>

                  {/* Annualized Excess */}
                  <td
                    className={`px-3 py-2 font-mono text-[11px] font-bold ${returnColor(o.annualized_excess_return_pct)}`}
                    title={`Annualized: ${o.annualized_excess_return_pct.toFixed(1)}%`}
                  >
                    {o.annualized_excess_return_pct >= 10000
                      ? `${(o.annualized_excess_return_pct / 1000).toFixed(0)}K%`
                      : o.annualized_excess_return_pct >= 1000
                        ? `${(o.annualized_excess_return_pct / 1000).toFixed(1)}K%`
                        : `${o.annualized_excess_return_pct.toFixed(1)}%`}
                  </td>

                  {/* $1K Slippage */}
                  <td
                    className={`px-3 py-2 font-mono text-[11px] ${impactColor(o.slippage_bps)}`}
                    title={`Avg fill price vs best ask if you buy $1K of NO shares. ${o.pct_filled < 100 ? `Only ${o.pct_filled}% filled — not enough liquidity for full $1K` : 'Full fill'}`}
                  >
                    {o.slippage_bps.toFixed(0)}bp
                    {o.pct_filled < 100 && (
                      <span className="text-[var(--hl-red)] ml-0.5 text-[8px]">
                        {o.pct_filled.toFixed(0)}%
                      </span>
                    )}
                  </td>

                  {/* $1K Price Impact */}
                  <td
                    className={`px-3 py-2 font-mono text-[11px] ${impactColor(o.price_impact_bps)}`}
                    title="How much the best ask moves after your $1K order"
                  >
                    {o.price_impact_bps.toFixed(0)}bp
                  </td>

                  {/* Depth */}
                  <td className="px-3 py-2 text-[10px] text-[var(--hl-text-dim)] font-mono">
                    {fmtDollars(o.liquidity_usd)}
                  </td>

                  {/* Volume */}
                  <td className="px-3 py-2 text-[10px] text-[var(--hl-text-dim)] font-mono">
                    {fmtDollars(o.volume)}
                  </td>

                  {/* Category */}
                  <td className="px-3 py-2">
                    <span className="text-[9px] bg-[var(--hl-surface2)] text-[var(--hl-text-dim)] px-1.5 py-0.5 rounded font-medium">
                      {o.category}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center gap-4 px-4 py-1.5 border-t border-[var(--hl-border)] text-[9px] text-[var(--hl-text-dim)]">
        <span>$1K Slip = avg fill cost vs best ask for a $1,000 buy (basis points)</span>
        <span>$1K Impact = how much best ask moves after your order</span>
        <span className="text-[var(--hl-green)]">0bp = zero slippage</span>
        <span className="text-[var(--hl-yellow)]">&gt;50bp = thin</span>
        <span className="text-[var(--hl-red)]">&gt;200bp = illiquid</span>
      </div>
    </div>
  );
}
