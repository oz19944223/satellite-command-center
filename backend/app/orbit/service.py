from __future__ import annotations
from datetime import datetime, timedelta, timezone
from app.models.domain import OrbitPosition, PassWindow

class OrbitUnavailable(RuntimeError): pass

class OrbitService:
    def __init__(self, max_age_days: int = 14): self.max_age_days=max_age_days
    def _sat(self,tle0:str|None,tle1:str|None,tle2:str|None):
        if not tle1 or not tle2: raise OrbitUnavailable("Orbital elements unavailable")
        try:
            from skyfield.api import EarthSatellite, load
        except ImportError as exc:
            raise OrbitUnavailable("Skyfield is not installed; install project dependencies to enable orbit calculations") from exc
        return EarthSatellite(tle1,tle2,tle0 or "SATELLITE",load.timescale()), load.timescale()
    def position(self,tle0:str|None,tle1:str|None,tle2:str|None,at:datetime|None=None)->OrbitPosition:
        at=at or datetime.now(timezone.utc); sat,ts=self._sat(tle0,tle1,tle2)
        t=ts.from_datetime(at.astimezone(timezone.utc)); sub=sat.at(t).subpoint()
        return OrbitPosition(latitude=sub.latitude.degrees,longitude=sub.longitude.degrees,altitude_km=sub.elevation.km,calculated_at=at)
    def passes(self,tle0,tle1,tle2,latitude:float,longitude:float,start:datetime|None=None,hours:int=24)->list[PassWindow]:
        try:
            from skyfield.api import wgs84
        except ImportError as exc: raise OrbitUnavailable("Skyfield is not installed") from exc
        start=start or datetime.now(timezone.utc); sat,ts=self._sat(tle0,tle1,tle2); observer=wgs84.latlon(latitude,longitude)
        times,events=sat.find_events(observer,ts.from_datetime(start),ts.from_datetime(start+timedelta(hours=hours)),altitude_degrees=10.0)
        out=[]; current=None
        for t,e in zip(times,events):
            dt=t.utc_datetime().replace(tzinfo=timezone.utc)
            if e==0: current=PassWindow(rise=dt)
            elif e==1 and current:
                current.culmination=dt; alt=(sat-observer).at(t).altaz()[0].degrees; current.max_elevation_deg=float(alt)
            elif e==2 and current:
                current.set=dt; out.append(current); current=None
        return out
