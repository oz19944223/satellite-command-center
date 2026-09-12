from datetime import datetime, timezone
from app.models.domain import FreshnessState, SourceHealth
from app.repositories.cache import CacheRepository

class SourceHealthService:
    def __init__(self, repo: CacheRepository): self.repo=repo
    def record_success(self, source: str, at: datetime | None = None):
        at=at or datetime.now(timezone.utc); self.repo.set_health(source, FreshnessState.LIVE_RECENT.value, at, None)
    def record_failure(self, source: str, message: str):
        old=self.get(source); self.repo.set_health(source, FreshnessState.SOURCE_OFFLINE.value, old.last_success_at, message)
    def get(self, source: str) -> SourceHealth:
        row=self.repo.get_health(source)
        if not row: return SourceHealth(source=source,state=FreshnessState.DATA_UNAVAILABLE)
        return SourceHealth(source=source,state=FreshnessState(row[0]),last_success_at=datetime.fromisoformat(row[1]) if row[1] else None,message=row[2])
