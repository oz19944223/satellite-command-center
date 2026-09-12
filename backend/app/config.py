from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Settings:
    satnogs_db_url: str = "https://db.satnogs.org/api"
    satnogs_network_url: str = "https://network.satnogs.org/api"
    cache_db: Path = Path.home() / ".satellite-command-center" / "cache.sqlite3"
    timeout_seconds: float = 10.0
    satellite_ttl_seconds: int = 86400
    station_ttl_seconds: int = 900
    observation_ttl_seconds: int = 120
    orbit_max_age_days: int = 14

settings = Settings()
