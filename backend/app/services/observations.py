import json
from app.config import settings
from app.integrations.satnogs_network.client import SatnogsNetworkClient
from app.models.domain import Observation
from app.repositories.cache import CacheRepository
from app.services.health import SourceHealthService
from app.services.common import CachedServiceMixin
class ObservationService(CachedServiceMixin):
    source="SatNOGS Network"
    def __init__(self,client:SatnogsNetworkClient,repo:CacheRepository,health:SourceHealthService): self.client,self.repo,self.health=client,repo,health
    async def list(self,filters:dict|None=None):
        filters=filters or {}; key=json.dumps(filters,sort_keys=True)
        return await self._cached("observations",key,settings.observation_ttl_seconds,lambda:self.client.list_observations(**filters),lambda p:[Observation.model_validate(x) for x in p])
    async def get(self,observation_id:int):
        return await self._cached("observation",str(observation_id),settings.observation_ttl_seconds,lambda:self.client.get_observation(observation_id),lambda p:Observation.model_validate(p) if p else None)
