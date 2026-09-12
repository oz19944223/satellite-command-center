from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from pydantic import BaseModel
from app.integrations.http import UpstreamError
from app.models.domain import FreshnessState

class CachedServiceMixin:
    repo: Any
    health: Any
    source: str
    async def _cached(self, namespace: str, key: str, ttl: int, fetch: Callable, decoder: Callable[[Any], Any]):
        entry=self.repo.get(namespace,key)
        if entry and not entry.expired:
            return decoder(entry.payload)
        try:
            value=await fetch()
            now=datetime.now(timezone.utc)
            payload=value.model_dump(mode="json") if isinstance(value,BaseModel) else [x.model_dump(mode="json") for x in value] if isinstance(value,list) and (not value or isinstance(value[0],BaseModel)) else value
            self.repo.put(namespace,key,payload,now,now+timedelta(seconds=ttl)); self.health.record_success(self.source,now)
            return value
        except UpstreamError as exc:
            self.health.record_failure(self.source,exc.message)
            if entry:
                value=decoder(entry.payload)
                items=value if isinstance(value,list) else [value]
                for item in items:
                    if hasattr(item,"freshness"): item.freshness=FreshnessState.CACHED
                return value
            raise
