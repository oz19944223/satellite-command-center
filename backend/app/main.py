from __future__ import annotations
from pathlib import Path
import tempfile
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router
from app.config import settings
from app.integrations.satnogs_db.client import SatnogsDbClient
from app.integrations.satnogs_network.client import SatnogsNetworkClient
from app.repositories.cache import CacheRepository
from app.services.health import SourceHealthService
from app.services.satellites import SatelliteService
from app.services.stations import StationService
from app.services.observations import ObservationService
from app.orbit.service import OrbitService

def create_app(testing:bool=False)->FastAPI:
    app=FastAPI(title='Satellite Command Center API',version='0.1.0')
    app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:8000','http://localhost:8000'],allow_methods=['GET'],allow_headers=['*'])
    cache_path=Path(tempfile.gettempdir())/'scc-test-cache.sqlite3' if testing else settings.cache_db
    repo=CacheRepository(cache_path); health=SourceHealthService(repo)
    app.state.services={
      'health':health,
      'satellites':SatelliteService(SatnogsDbClient(),repo,health),
      'stations':StationService(SatnogsNetworkClient(),repo,health),
      'observations':ObservationService(SatnogsNetworkClient(),repo,health),
      'orbit':OrbitService(settings.orbit_max_age_days),
    }
    app.include_router(router)
    static=Path(__file__).parent/'static'
    app.mount('/static',StaticFiles(directory=static),name='static')
    @app.get('/',include_in_schema=False)
    def index(): return FileResponse(static/'index.html')
    return app
app=create_app()
