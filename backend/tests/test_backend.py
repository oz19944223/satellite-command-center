from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import httpx, pytest
from fastapi.testclient import TestClient
from app.integrations.http import SafeHttpClient
from app.integrations.satnogs_network.client import SatnogsNetworkClient
from app.models.domain import FreshnessState, OrbitPosition
from app.repositories.cache import CacheRepository

def test_health_endpoint():
    from app.main import create_app
    c=TestClient(create_app(testing=True)); r=c.get('/api/health'); assert r.status_code==200 and r.json()['app']=='ok'

def test_network_observation_normalization():
    payload={"id":42,"start":"2026-09-06T10:00:00Z","end":"2026-09-06T10:10:00Z","ground_station":26,"norad_cat_id":"25544","station_name":"Test","station_lat":"-26.2","station_lng":"28.0","station_alt":"1700","status":"good","waterfall":"https://example/w.png","payload":"https://example/a.ogg","demoddata":[{"payload_demod":"https://example/data.bin"}],"transmitter_downlink_low":145800000,"transmitter_mode":"FM"}
    def handler(req): return httpx.Response(200,json=[payload])
    cli=SatnogsNetworkClient(SafeHttpClient('SatNOGS Network',transport=httpx.MockTransport(handler)))
    import asyncio
    rows=asyncio.run(cli.list_observations())
    assert rows[0].norad_id==25544 and len(rows[0].artifacts)==3 and rows[0].station_latitude==-26.2

def test_cache_expiry_keeps_payload():
    with tempfile.TemporaryDirectory() as d:
        repo=CacheRepository(Path(d)/'c.sqlite3'); now=datetime.now(timezone.utc)
        repo.put('x','y',{'a':1},now,now-timedelta(seconds=1)); entry=repo.get('x','y')
        assert entry and entry.expired and entry.payload=={'a':1}

def test_orbit_position_label_contract():
    p=OrbitPosition(latitude=0,longitude=0,altitude_km=400,calculated_at=datetime.now(timezone.utc))
    assert p.label=='Calculated orbit position' and p.freshness==FreshnessState.CALCULATED
