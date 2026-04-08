from __future__ import annotations

from pydantic import BaseModel


class ScannerOpportunity(BaseModel):
    market_id: str
    question: str
    end_date: str
    category: str = ""
    side: str = "NO"  # "YES" or "NO" — which cheap share to buy
    yes_sticker_price: float
    no_sticker_price: float
    ask_price: float
    gross_return_pct: float
    net_return_pct: float
    days_to_expiry: int
    annualized_net_return_pct: float
    annualized_excess_return_pct: float
    slug: str = ""
    bid_ask_spread_cents: float = 0
    liquidity_usd: float
    volume: float = 0
    # Order book impact for a $1K buy
    slippage_bps: float = 0        # avg fill price vs best ask, in basis points
    price_impact_bps: float = 0    # how much best ask moves after your order
    pct_filled: float = 0          # % of $1K order that gets filled
    holding_reward_eligible: bool = False
