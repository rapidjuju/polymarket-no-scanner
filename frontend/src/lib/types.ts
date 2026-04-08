export interface ScannerOpportunity {
  market_id: string;
  question: string;
  end_date: string;
  category: string;
  side: string;
  yes_sticker_price: number;
  no_sticker_price: number;
  ask_price: number;
  gross_return_pct: number;
  net_return_pct: number;
  days_to_expiry: number;
  annualized_net_return_pct: number;
  annualized_excess_return_pct: number;
  slug: string;
  bid_ask_spread_cents: number;
  liquidity_usd: number;
  volume: number;
  slippage_bps: number;
  price_impact_bps: number;
  pct_filled: number;
  holding_reward_eligible: boolean;
}
