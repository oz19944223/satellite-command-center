import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import httpx
from app.integrations.http import SafeHttpClient, UpstreamError
from app.integrations.satnogs_db.client import SatnogsDbClient
from app.repositories.cache import CacheRepository
from app.services.health import SourceHealthService
from app.services.satellites import SatelliteService
from app.models.domain import FreshnessState

def test_db_satellite_and_transmitter_normalization():
    def handler(req: httpx.Request):
        u=str(req.url)
        if '/transmitters/' in u:
            return httpx.Response(200,json=[{"uuid":"tx1","description":"Voice","downlink_low":145800000,"mode":"FM","status":"active","norad_cat_id":25544}])
        if '/tle/' in u:
            return httpx.Response(200,json=[])
        return httpx.Response(200,json=[{"sat_id":"ISS-ID","name":"ISS","norad_cat_id":25544,"status":"alive"}])
    client=SatnogsDbClient(SafeHttpClient('SatNOGS DB',transport=httpx.MockTransport(handler)))
    sat=asyncio.run(client.get_satellite('25544'))
    assert sat.name=='ISS' and sat.norad_id==25544 and sat.transmitters[0].downlink_low_hz==145800000

def test_cached_real_satellite_survives_later_upstream_failure():
    calls={'n':0}
    def handler(req):
        calls['n']+=1
        if calls['n']==1: return httpx.Response(200,json=[{"sat_id":"X","name":"TESTSAT","norad_cat_id":12345}])
        raise httpx.ConnectError('offline',request=req)
    with tempfile.TemporaryDirectory() as d:
        repo=CacheRepository(Path(d)/'cache.sqlite3'); health=SourceHealthService(repo)
        service=SatelliteService(SatnogsDbClient(SafeHttpClient('SatNOGS DB',transport=httpx.MockTransport(handler))),repo,health)
        first=asyncio.run(service.search('TESTSAT')); assert first[0].name=='TESTSAT'
        entry=repo.get('sat-search','testsat')
        # Force the cache stale so service attempts a refresh.
        repo.put('sat-search','testsat',entry.payload,entry.retrieved_at,datetime.now(timezone.utc)-timedelta(seconds=1))
        second=asyncio.run(service.search('TESTSAT'))
        assert second[0].name=='TESTSAT' and second[0].freshness==FreshnessState.CACHED
        assert health.get('SatNOGS DB').state==FreshnessState.SOURCE_OFFLINE
