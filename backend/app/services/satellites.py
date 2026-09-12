from app.config import settings
from app.integrations.satnogs_db.client import SatnogsDbClient
from app.models.domain import Satellite
from app.repositories.cache import CacheRepository
from app.services.health import SourceHealthService
from app.services.common import CachedServiceMixin

class SatelliteService(CachedServiceMixin):
    source="SatNOGS DB"
    def __init__(self, client: SatnogsDbClient, repo: CacheRepository, health: SourceHealthService): self.client,self.repo,self.health=client,repo,health
    async def search(self, query: str):
        key=query.strip().lower() or "__all__"
        return await self._cached("sat-search",key,settings.satellite_ttl_seconds,lambda:self.client.search_satellites(query),lambda p:[Satellite.model_validate(x) for x in p])
    async def get(self, satellite_id: str):
        return await self._cached("satellite",satellite_id,settings.satellite_ttl_seconds,lambda:self.client.get_satellite(satellite_id),lambda p:Satellite.model_validate(p) if p else None)
