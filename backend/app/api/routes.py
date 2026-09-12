from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.integrations.http import UpstreamError
from app.orbit.service import OrbitUnavailable

router=APIRouter(prefix="/api")

def sv(request:Request): return request.app.state.services

@router.get('/health')
def health(): return {'app':'ok','mode':'real-public-data'}

@router.get('/sources/health')
def source_health(services=Depends(sv)):
    return [services['health'].get('SatNOGS DB'),services['health'].get('SatNOGS Network')]

@router.get('/satellites')
async def satellites(q:str='',services=Depends(sv)):
    try:return await services['satellites'].search(q)
    except UpstreamError as exc: raise HTTPException(503,detail=f"{exc.source}: {exc.message}")

@router.get('/satellites/{satellite_id}')
async def satellite(satellite_id:str,services=Depends(sv)):
    try:item=await services['satellites'].get(satellite_id)
    except UpstreamError as exc: raise HTTPException(503,detail=f"{exc.source}: {exc.message}")
    if not item: raise HTTPException(404,'Satellite not found')
    return item

@router.get('/stations')
async def stations(services=Depends(sv)):
    try:return await services['stations'].list()
    except UpstreamError as exc: raise HTTPException(503,detail=f"{exc.source}: {exc.message}")

@router.get('/stations/{station_id}')
async def station(station_id:int,services=Depends(sv)):
    try:item=await services['stations'].get(station_id)
    except UpstreamError as exc: raise HTTPException(503,detail=f"{exc.source}: {exc.message}")
    if not item: raise HTTPException(404,'Ground station not found')
    return item

@router.get('/observations')
async def observations(norad_id:int|None=None,station_id:int|None=None,status:str|None=None,services=Depends(sv)):
    filters={"satellite__norad_cat_id":norad_id,"ground_station":station_id,"status":status}
    try:return await services['observations'].list(filters)
    except UpstreamError as exc: raise HTTPException(503,detail=f"{exc.source}: {exc.message}")

@router.get('/observations/{observation_id}')
async def observation(observation_id:int,services=Depends(sv)):
    try:item=await services['observations'].get(observation_id)
    except UpstreamError as exc: raise HTTPException(503,detail=f"{exc.source}: {exc.message}")
    if not item: raise HTTPException(404,'Observation not found')
    return item

@router.get('/orbit/{satellite_id}')
async def orbit(satellite_id:str,services=Depends(sv)):
    try:sat=await services['satellites'].get(satellite_id)
    except UpstreamError as exc: raise HTTPException(503,detail=f"{exc.source}: {exc.message}")
    if not sat: raise HTTPException(404,'Satellite not found')
    try:return services['orbit'].position(sat.tle0,sat.tle1,sat.tle2)
    except OrbitUnavailable as exc: raise HTTPException(503,detail=str(exc))

@router.get('/passes/{satellite_id}')
async def passes(satellite_id:str,lat:float=Query(ge=-90,le=90),lon:float=Query(ge=-180,le=180),services=Depends(sv)):
    try:sat=await services['satellites'].get(satellite_id)
    except UpstreamError as exc: raise HTTPException(503,detail=f"{exc.source}: {exc.message}")
    if not sat: raise HTTPException(404,'Satellite not found')
    try:return services['orbit'].passes(sat.tle0,sat.tle1,sat.tle2,lat,lon)
    except OrbitUnavailable as exc: raise HTTPException(503,detail=str(exc))

@router.get('/dashboard')
async def dashboard(services=Depends(sv)):
    satellites=[]; stations=[]; observations=[]
    errors=[]
    try:satellites=await services['satellites'].search('')
    except Exception as exc: errors.append(str(exc))
    try:stations=await services['stations'].list()
    except Exception as exc: errors.append(str(exc))
    try:observations=await services['observations'].list({})
    except Exception as exc: errors.append(str(exc))
    return {
      'satellites':len(satellites),'stations':len(stations),'observations':len(observations),
      'recent_observations':[x.model_dump(mode='json') for x in observations[:12]],
      'stations_sample':[x.model_dump(mode='json') for x in stations[:80]],
      'source_health':[services['health'].get('SatNOGS DB').model_dump(mode='json'),services['health'].get('SatNOGS Network').model_dump(mode='json')],
      'errors':errors
    }
