from __future__ import annotations

import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class CLOBClient:
    """CLOB API client for order book data. Returns None on any failure."""

    def __init__(self):
        self.base_url = settings.polymarket_clob_host
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

    async def close(self):
        await self.client.aclose()

    async def get_book(self, token_id: str) -> dict | None:
        try:
            resp = await self.client.get("/book", params={"token_id": token_id})
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_best_bid(self, book: dict) -> float | None:
        """Extract the highest bid price from an order book response."""
        bids = book.get("bids", [])
        if not bids:
            return None
        try:
            return max(float(b["price"]) for b in bids)
        except (KeyError, ValueError, TypeError):
            return None

    def get_best_ask(self, book: dict) -> float | None:
        """Extract the lowest ask price from an order book response."""
        asks = book.get("asks", [])
        if not asks:
            return None
        try:
            return min(float(a["price"]) for a in asks)
        except (KeyError, ValueError, TypeError):
            return None

    def get_ask_depth(self, book: dict, max_spread_pct: float = 0.02) -> float:
        """Compute total USD on the ask side within max_spread_pct of best ask."""
        asks = book.get("asks", [])
        if not asks:
            return 0.0

        try:
            prices = [(float(a["price"]), float(a["size"])) for a in asks]
        except (KeyError, ValueError, TypeError):
            return 0.0

        best_ask = min(p for p, _ in prices)
        if best_ask <= 0:
            return 0.0

        threshold = best_ask * (1 + max_spread_pct)
        total = 0.0
        for price, size in prices:
            if price <= threshold:
                total += price * size
        return total

    def simulate_buy(self, book: dict, spend_usd: float) -> dict:
        """Simulate buying NO shares with a given USD amount.

        Walks the ask ladder to compute:
        - shares_filled: total shares you'd receive
        - avg_price: volume-weighted average fill price
        - slippage_bps: (avg_price - best_ask) / best_ask in basis points
        - best_ask_after: the new best ask price after your order eats liquidity
        - price_impact_bps: (best_ask_after - best_ask) / best_ask in basis points
        - pct_filled: what % of your order gets filled (100 = full fill)
        """
        asks = book.get("asks", [])
        if not asks or spend_usd <= 0:
            return {
                "shares_filled": 0, "avg_price": 0, "slippage_bps": 0,
                "best_ask_after": 0, "price_impact_bps": 0, "pct_filled": 0,
            }

        try:
            levels = sorted(
                [(float(a["price"]), float(a["size"])) for a in asks],
                key=lambda x: x[0],
            )
        except (KeyError, ValueError, TypeError):
            return {
                "shares_filled": 0, "avg_price": 0, "slippage_bps": 0,
                "best_ask_after": 0, "price_impact_bps": 0, "pct_filled": 0,
            }

        best_ask = levels[0][0]
        remaining = spend_usd
        total_shares = 0.0
        total_cost = 0.0
        last_consumed_idx = -1

        for i, (price, size) in enumerate(levels):
            level_cost = price * size  # USD to consume this entire level
            if remaining >= level_cost:
                # consume entire level
                total_shares += size
                total_cost += level_cost
                remaining -= level_cost
                last_consumed_idx = i
            else:
                # partial fill at this level
                shares_at_level = remaining / price
                total_shares += shares_at_level
                total_cost += remaining
                remaining = 0
                break

        if total_shares == 0:
            return {
                "shares_filled": 0, "avg_price": 0, "slippage_bps": 0,
                "best_ask_after": 0, "price_impact_bps": 0, "pct_filled": 0,
            }

        avg_price = total_cost / total_shares
        slippage_bps = ((avg_price - best_ask) / best_ask) * 10000 if best_ask > 0 else 0

        # Best ask after: if we fully consumed some levels, next level is the new best
        if remaining > 0:
            # Didn't fully fill — ran out of liquidity
            best_ask_after = levels[-1][0] if levels else best_ask
        elif last_consumed_idx + 1 < len(levels):
            best_ask_after = levels[last_consumed_idx + 1][0]
        else:
            # Consumed entire book
            best_ask_after = levels[-1][0]

        price_impact_bps = ((best_ask_after - best_ask) / best_ask) * 10000 if best_ask > 0 else 0
        pct_filled = ((spend_usd - remaining) / spend_usd) * 100

        return {
            "shares_filled": round(total_shares, 4),
            "avg_price": round(avg_price, 6),
            "slippage_bps": round(slippage_bps, 1),
            "best_ask_after": round(best_ask_after, 6),
            "price_impact_bps": round(price_impact_bps, 1),
            "pct_filled": round(pct_filled, 1),
        }

    async def fetch_books_throttled(
        self, token_ids: list[str], max_concurrent: int | None = None
    ) -> dict[str, dict]:
        """Fetch order books for multiple tokens with rate limiting."""
        if max_concurrent is None:
            max_concurrent = settings.max_concurrent_clob

        sem = asyncio.Semaphore(max_concurrent)
        results: dict[str, dict] = {}

        async def fetch_one(tid: str):
            async with sem:
                book = await self.get_book(tid)
                await asyncio.sleep(0.05)
                return tid, book

        tasks = [fetch_one(tid) for tid in token_ids]
        for coro in asyncio.as_completed(tasks):
            tid, book = await coro
            if book:
                results[tid] = book

        return results
