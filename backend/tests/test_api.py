from fastapi.testclient import TestClient
from app.main import create_app

def test_static_ui_and_health():
    c=TestClient(create_app(testing=True))
    assert c.get('/').status_code==200
    assert 'SATELLITE' in c.get('/').text
    r=c.get('/api/health'); assert r.status_code==200 and r.json()['mode']=='real-public-data'

def test_orbit_missing_satellite_is_not_fabricated():
    # Upstream unavailable may be 503, but the app never returns fake coordinates for unknown data.
    c=TestClient(create_app(testing=True))
    r=c.get('/api/orbit/nonexistent')
    assert r.status_code in (404,503)


def test_dashboard_includes_realistic_globe_asset():
    c=TestClient(create_app(testing=True))
    html=c.get('/').text
    assert 'earth-globe' in html
    asset=c.get('/static/earth_globe.png')
    assert asset.status_code==200
    assert asset.headers.get('content-type','').startswith('image/')
