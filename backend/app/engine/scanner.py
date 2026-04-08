from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.clients.clob import CLOBClient
from app.clients.gamma import GammaClient
from app.config import settings
from app.models import ScannerOpportunity

logger = logging.getLogger(__name__)

# Load fee rates from config file
_FEE_RATES_PATH = Path(__file__).resolve().parent.parent.parent / "fee_rates.json"
with open(_FEE_RATES_PATH) as f:
    FEE_RATES: dict[str, float] = json.load(f)

DEFAULT_FEE_RATE = FEE_RATES.pop("_default", 0.04)

# Map Polymarket's feeType field to our fee_rates.json keys
FEE_TYPE_MAP = {
    "crypto_fees_v2": "crypto",
    "crypto_fees": "crypto",
    "sports_fees_v2": "sports",
    "sports_fees": "sports",
    "weather_fees": "weather",
    "geopolitical_fees": "geopolitical",
}

# Cap annualized return to avoid infinity for very short-dated markets



# Keyword-based category detection.
# Order matters: first match wins. More specific categories go first.
_CATEGORY_KEYWORDS: list[tuple[str, list[str]]] = [
    # More specific categories first to avoid false positives
    ("geopolitical", [
        # Conflicts & military
        "invasion", "invade", "ceasefire", "war ", "conflict", "military",
        "nuclear deal", "nuclear weapon", "enriched uranium", "missile",
        "airstrike", "strike ", "sanctions", "embargo",
        "nato", "un security council",
        # Regions & conflicts
        "russia-ukraine", "ukraine-russia", "israel-iran", "iran-israel",
        "israel/us conflict", "iran x israel",
        "taiwan strait", "south china sea", "north korea", "dprk",
        "gaza", "west bank", "hezbollah", "houthi", "hamas",
        "coup attempt", "coup d'etat", "regime change",
        "leadership change", "leader of ",
        "litani river", "annexed",
    ]),
    ("politics", [
        # Elections & offices
        "president", "presidential", "governor", "senator", "senate",
        "congress", "house of representatives", "parliament", "prime minister",
        "chancellor", "election", "midterm", "nominee", "nomination",
        "republican", "democrat", "gop", "tory", "labour party", "conservative party",
        "liberal party",
        # Political figures (major)
        "trump", "biden", "desantis", "newsom", "vance", "obama",
        "macron", "starmer", "modi", "erdogan", "netanyahu", "zelensky",
        "putin", "xi jinping", "scholz", "meloni", "maduro",
        "bolsonaro", "lula", "trudeau", "milei",
        # Political terms
        "impeach", "pardon", "executive order", "supreme court", "scotus",
        "filibuster", "veto", "cabinet", "resign", "approval rating",
        "ballot", "electoral", "referendum", "redistrict",
        "confirmed as", "appointed to",
    ]),
    ("sports", [
        # Leagues & tournaments
        "epl", "premier league", "la liga", "serie a", "bundesliga", "ligue 1",
        "champions league", "europa league", "mls ", "nba", "nfl", "nhl", "mlb",
        "wnba", "ncaa", "stanley cup", "super bowl", "world series",
        "world cup", "euros 20", "copa america", "uefa",
        "ipl", "cricket", "rugby", "f1 ", "formula 1", "grand prix",
        "ufc", "boxing", "pga", "masters tournament", "open championship",
        "us open golf", "ryder cup", "wimbledon", "french open", "australian open",
        "davis cup", "euroleague", "six nations", "lck", "lcs", "esport",
        "fide candidates",
        # Match patterns
        " vs ", " vs. ",
        # Teams (major — soccer)
        "arsenal", "manchester united", "manchester city", "liverpool", "chelsea",
        "tottenham", "real madrid", "barcelona", "bayern munich", "psg",
        "juventus", "inter milan", "ac milan", "napoli", "atletico madrid",
        "borussia dortmund",
        # Teams (NBA)
        "lakers", "celtics", "warriors", "nuggets", "knicks", "76ers",
        "bucks", "heat", "mavericks", "thunder", "timberwolves", "cavaliers",
        "nets", "clippers", "suns", "rockets", "bulls", "hawks", "pacers",
        # Teams (MLB)
        "yankees", "dodgers", "mets", "braves", "astros", "phillies",
        "cubs", "red sox", "padres", "orioles", "twins",
        "guardians", "rays", "mariners", "white sox", "blue jays",
        # Teams (NFL)
        "chiefs", "49ers", "ravens", "bills", "lions",
        "cowboys", "packers", "dolphins", "bengals", "texans", "vikings",
        "steelers", "commanders", "broncos", "saints",
        # Teams (NHL)
        "oilers", "maple leafs", "bruins", "hurricanes",
        "avalanche", "lightning", "predators", "penguins",
        "blue jackets", "blackhawks", "kraken",
        # Sports terms
        "win the 202", "finish in the top", "make the playoffs",
        "mvp", "golden boot", "ballon d'or", "heisman",
        "relegat", "promoted to",
    ]),
    ("crypto", [
        "bitcoin", "btc", "ethereum", "eth ", "solana", "sol ",
        "crypto", "token", "blockchain", "defi", "nft",
        "binance", "coinbase", "ftx", "uniswap", "aave",
        "stablecoin", "usdc", "usdt", "tether",
        "market cap (fdv)", "fdv above", "fdv below",
        "launch a token", "ticker be $",
        "memecoin", "meme coin", "altcoin",
        "halving", "mining",
    ]),
    ("finance", [
        # Markets & indices
        "s&p 500", "s&p500", "nasdaq", "dow jones", "ftse", "nikkei",
        "stock market", "bear market", "bull market", "market crash",
        "largest company", "market cap",
        # Commodities
        "crude oil", "wti", "brent", "natural gas", "gold price",
        "silver ", "copper ", "oil price", "commodity",
        # Companies & IPO
        "ipo", "public offering", "ticker",
        "apple", "google", "alphabet", "amazon", "microsoft", "nvidia",
        "meta ", "tesla", "spacex", "stripe", "openai",
        "anthropic", "deepseek", "mistral",
        # Monetary policy
        "fed ", "federal reserve", "interest rate", "rate cut", "rate hike",
        "fed chair", "fomc", "ecb", "bank of england",
        "inflation", "cpi", "gdp", "recession", "unemployment",
        "tariff", "trade war", "trade deal",
        "yield curve", "treasury", "bond ",
    ]),
    ("tech", [
        "ai model", "artificial intelligence", "machine learning",
        "gpt", "llm", "chatgpt", "gemini", "claude",
        "agi", "asi", "superintelligen",
        "self-driving", "autonomous vehicle",
        "quantum comput", "fusion energy",
        "app store", "iphone", "android",
        "starship", "falcon", "rocket launch", "mars",
        "social media", "tiktok", "twitter", "x.com",
        "data breach", "hack", "cybersecurity",
    ]),
    ("culture", [
        "oscar", "academy award", "grammy", "emmy", "golden globe",
        "box office", "grossing movie", "grossing film",
        "billboard", "spotify", "album", "song",
        "eurovision", "super bowl halftime",
        "nobel prize", "pulitzer",
        "bestseller", "book of the year",
        "viral", "trending",
    ]),
    ("weather", [
        "hurricane", "typhoon", "tornado", "earthquake", "tsunami",
        "wildfire", "flooding", "drought", "heat wave", "heatwave",
        "hottest year", "coldest", "climate",
        "el nino", "la nina",
        "category 4", "category 5", "magnitude",
        "temperature record",
    ]),
]


def _classify_category(fee_type: str, slug: str, question: str = "") -> str:
    """Derive category from feeType field, falling back to keyword heuristics."""
    if fee_type:
        mapped = FEE_TYPE_MAP.get(fee_type)
        if mapped:
            return mapped
        base = fee_type.replace("_fees", "").replace("_v2", "").replace("_v3", "")
        if base in FEE_RATES:
            return base

    # Keyword-based detection on question text (first match wins)
    q_lower = question.lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        for kw in keywords:
            if kw in q_lower:
                return category

    # Fallback: keyword match on slug
    slug_lower = slug.lower()
    for category in FEE_RATES:
        if category in slug_lower:
            return category
    return "other"


def _get_fee_rate(category: str) -> float:
    return FEE_RATES.get(category, DEFAULT_FEE_RATE)


def compute_opportunity(
    market: dict, book: dict, clob_client: CLOBClient, side: str = "NO"
) -> ScannerOpportunity | None:
    """Compute opportunity metrics for buying a cheap share on the given side."""
    try:
        outcome_prices = market["outcome_prices"]
        yes_sticker = outcome_prices[0]
        no_sticker = outcome_prices[1] if len(outcome_prices) > 1 else 1.0 - yes_sticker

        # Get actual ask from order book for this side
        ask = clob_client.get_best_ask(book)
        if ask is None or ask <= 0 or ask >= 1:
            return None

        # Parse expiry
        end_date_str = market["end_date"]
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
            try:
                end_dt = datetime.strptime(end_date_str, fmt).replace(tzinfo=timezone.utc)
                break
            except ValueError:
                continue
        else:
            return None

        days = (end_dt - datetime.now(timezone.utc)).days
        if days <= 0:
            return None

        # Gross return (before fees)
        gross_return = (1.0 - ask) / ask

        # Fee calculation using feeType from the API
        category = _classify_category(
            market.get("fee_type", ""), market.get("slug", ""), market.get("question", "")
        )
        fee_rate = _get_fee_rate(category)
        fee_per_share = fee_rate * ask * (1.0 - ask)

        # Net return (after fees on entry)
        effective_cost = ask + fee_per_share
        if effective_cost >= 1.0:
            return None
        net_return = (1.0 - effective_cost) / effective_cost

        # Annualize (cap display at 99,999% to avoid overflow for short-dated markets)
        try:
            annualized_net = (1.0 + net_return) ** (365.0 / days) - 1.0
        except OverflowError:
            annualized_net = 999.99  # 99,999%
        annualized_net_pct = min(annualized_net * 100, 99999.0)

        # Excess return over risk-free, plus holding reward if eligible
        reward_eligible = bool(market.get("holding_rewards_enabled"))
        reward = settings.holding_reward_rate if reward_eligible else 0.0
        annualized_excess_pct = annualized_net_pct - (settings.risk_free_rate * 100) + (reward * 100)

        # Bid-ask spread for the chosen side
        best_bid = clob_client.get_best_bid(book)
        bid_ask_spread_cents = round((ask - best_bid) * 100, 2) if best_bid is not None else 0.0

        # Liquidity
        liquidity = clob_client.get_ask_depth(book)

        # Order book impact simulation ($1K buy)
        impact = clob_client.simulate_buy(book, 1000.0)

        return ScannerOpportunity(
            market_id=market["id"],
            question=market["question"],
            end_date=end_date_str,
            category=category,
            side=side,
            yes_sticker_price=yes_sticker,
            no_sticker_price=no_sticker,
            ask_price=ask,
            gross_return_pct=round(gross_return * 100, 2),
            net_return_pct=round(net_return * 100, 2),
            days_to_expiry=days,
            annualized_net_return_pct=round(annualized_net_pct, 2),
            annualized_excess_return_pct=round(annualized_excess_pct, 2),
            slug=market.get("slug", ""),
            bid_ask_spread_cents=bid_ask_spread_cents,
            liquidity_usd=round(liquidity, 2),
            volume=market.get("volume", 0),
            slippage_bps=impact["slippage_bps"],
            price_impact_bps=impact["price_impact_bps"],
            pct_filled=impact["pct_filled"],
            holding_reward_eligible=reward_eligible,
        )
    except Exception as e:
        logger.debug(f"Failed to compute opportunity for {market.get('id')}: {e}")
        return None


def _flip_book(book: dict) -> dict:
    """Derive the NO-side order book from the YES-side book.

    Polymarket's CLOB mirrors the NO book from the YES book:
      NO asks = 1 - YES bids  (buying NO = selling YES)
      NO bids = 1 - YES asks  (selling NO = buying YES)
    So we only need to fetch the YES book and flip it for the NO side.
    """
    yes_bids = book.get("bids", [])
    yes_asks = book.get("asks", [])
    return {
        "asks": [{"price": str(round(1.0 - float(b["price"]), 4)), "size": b["size"]} for b in yes_bids],
        "bids": [{"price": str(round(1.0 - float(a["price"]), 4)), "size": a["size"]} for a in yes_asks],
    }


async def refresh_scanner(
    gamma_client: GammaClient, clob_client: CLOBClient
) -> list[ScannerOpportunity]:
    """Full scan: fetch markets, get order books, compute opportunities.

    We only fetch the YES (first) token's order book, because Polymarket's
    CLOB mirrors the NO book from the YES book (NO asks = 1 - YES bids).
    Using the real YES book avoids phantom price discrepancies.
    """
    logger.info("Starting scanner refresh...")

    markets = await gamma_client.get_all_active_markets(min_volume=settings.min_market_volume)
    logger.info(f"Got {len(markets)} active markets, fetching CLOB books...")

    # Only fetch YES (first) token books
    yes_token_map: dict[str, dict] = {}  # yes_token_id -> market
    for m in markets:
        yes_token = m["clob_token_ids"][0]
        yes_token_map[yes_token] = m

    books = await clob_client.fetch_books_throttled(list(yes_token_map.keys()))
    logger.info(f"Got {len(books)} order books")

    # For each market, compute both YES and NO opportunities from the same book,
    # then pick the side closer to 100¢
    opportunities: list[ScannerOpportunity] = []
    for yes_token, market in yes_token_map.items():
        yes_book = books.get(yes_token)
        if not yes_book:
            continue

        no_book = _flip_book(yes_book)

        yes_opp = compute_opportunity(market, yes_book, clob_client, side="YES")
        no_opp = compute_opportunity(market, no_book, clob_client, side="NO")

        # Pick the side closer to 100¢ (higher ask = more likely outcome)
        candidates = [o for o in [yes_opp, no_opp] if o is not None]
        if not candidates:
            continue
        if len(candidates) == 1:
            if candidates[0].ask_price >= 0.5:
                opportunities.append(candidates[0])
        else:
            best = max(candidates, key=lambda o: o.ask_price)
            opportunities.append(best)

    # Sort by annualized excess return descending
    opportunities.sort(key=lambda o: o.annualized_excess_return_pct, reverse=True)

    logger.info(f"Scanner found {len(opportunities)} opportunities (high-prob side per market)")
    return opportunities
