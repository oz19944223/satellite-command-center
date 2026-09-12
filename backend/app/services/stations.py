from app.config import settings
from app.integrations.satnogs_network.client import SatnogsNetworkClient
from app.models.domain import GroundStation
from app.repositories.cache import CacheRepository
from app.services.health import SourceHealthService
from app.services.common import CachedServiceMixin
class StationService(CachedServiceMixin):
    source="SatNOGS Network"
    def __init__(self,client:SatnogsNetworkClient,repo:CacheRepository,health:SourceHealthService): self.client,self.repo,self.health=client,repo,health
    async def list(self): return await self._cached("stations","all",settings.station_ttl_seconds,self.client.list_stations,lambda p:[GroundStation.model_validate(x) for x in p])
    async def get(self,station_id:int):
        for s in await self.list():
            if s.id==station_id:return s
        return None
