from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    polymarket_gamma_host: str = "https://gamma-api.polymarket.com"
    polymarket_clob_host: str = "https://clob.polymarket.com"
    risk_free_rate: float = 0.043
    holding_reward_rate: float = 0.04
    poll_interval_seconds: int = 300
    max_concurrent_clob: int = 20
    min_market_volume: float = 100000  # only scan markets with >$100K all-time volume

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
