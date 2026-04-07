from __future__ import annotations

from fastapi import APIRouter, Query, Request

router = APIRouter(prefix="/api")


@router.get("/scanner")
async def get_scanner(
    request: Request,
    min_annualized: float | None = Query(None),
    min_liquidity: float | None = Query(None),
    category: str | None = Query(None),
):
    results = getattr(request.app.state, "scanner_results", [])

    filtered = results
    if min_annualized is not None:
        filtered = [o for o in filtered if o.annualized_excess_return_pct >= min_annualized]
    if min_liquidity is not None:
        filtered = [o for o in filtered if o.liquidity_usd >= min_liquidity]
    if category is not None:
        filtered = [o for o in filtered if o.category == category.lower()]

    return [o.model_dump() for o in filtered]
