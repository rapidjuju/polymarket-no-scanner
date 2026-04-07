from __future__ import annotations

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class GammaClient:
    def __init__(self):
        self.base_url = settings.polymarket_gamma_host
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=15.0)

    async def close(self):
        await self.client.aclose()

    async def get_all_active_markets(self, min_volume: float = 0) -> list[dict]:
        """Fetch all active, non-closed markets across all categories.

        Sorted by volume descending. Stops paginating when it hits a full page
        of markets below min_volume (meaning all remaining are lower).
        Set min_volume=0 to fetch everything (slow — 50K+ markets).
        """
        all_markets: list[dict] = []
        offset = 0
        limit = 100

        while True:
            try:
                resp = await self.client.get(
                    "/markets",
                    params={
                        "active": "true",
                        "closed": "false",
                        "limit": str(limit),
                        "offset": str(offset),
                        "order": "volume",
                        "ascending": "false",
                    },
                )
                resp.raise_for_status()
                batch = resp.json()

                if not batch:
                    break

                below_threshold = 0
                for m in batch:
                    parsed = self._parse_market(m)
                    if parsed:
                        if min_volume > 0 and parsed["volume"] < min_volume:
                            below_threshold += 1
                            continue
                        all_markets.append(parsed)

                # Since results are sorted by volume desc, once an entire page
                # is below the threshold, all subsequent pages will be too
                if min_volume > 0 and below_threshold == len(batch):
                    break

                if len(batch) < limit:
                    break
                offset += limit

            except Exception as e:
                logger.warning(f"Failed to fetch markets at offset {offset}: {e}")
                break

        logger.info(f"Fetched {len(all_markets)} active markets from Gamma API")
        return all_markets

    def _parse_market(self, m: dict) -> dict | None:
        try:
            clob_token_ids = _parse_json_list(m.get("clobTokenIds", "[]"))
            outcome_prices = [
                float(p) for p in _parse_json_list(m.get("outcomePrices", "[]"))
            ]

            # Need at least YES + NO tokens and prices
            if len(clob_token_ids) < 2 or len(outcome_prices) < 2:
                return None

            end_date = m.get("endDate", "")
            if not end_date:
                return None

            return {
                "id": m.get("id", ""),
                "question": m.get("question", ""),
                "outcome_prices": outcome_prices,
                "clob_token_ids": clob_token_ids,
                "end_date": end_date,
                "volume": float(m.get("volume", 0) or 0),
                "fee_type": m.get("feeType") or "",
                "holding_rewards_enabled": bool(m.get("holdingRewardsEnabled")),
                "slug": m.get("slug", ""),
            }
        except Exception as e:
            logger.debug(f"Failed to parse market: {e}")
            return None


def _parse_json_list(val) -> list:
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return []
    return []
