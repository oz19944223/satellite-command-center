from __future__ import annotations
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field, HttpUrl

class FreshnessState(StrEnum):
    LIVE_RECENT = "LIVE_RECENT"
    CALCULATED = "CALCULATED"
    HISTORICAL = "HISTORICAL"
    CACHED = "CACHED"
    SOURCE_OFFLINE = "SOURCE_OFFLINE"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"

class Transmitter(BaseModel):
    id: str
    description: str | None = None
    downlink_low_hz: int | None = None
    downlink_high_hz: int | None = None
    mode: str | None = None
    baud: float | None = None
    status: str | None = None

class Satellite(BaseModel):
    id: str
    name: str
    norad_id: int | None = None
    identifiers: dict[str, str] = Field(default_factory=dict)
    status: str | None = None
    transmitters: list[Transmitter] = Field(default_factory=list)
    tle0: str | None = None
    tle1: str | None = None
    tle2: str | None = None
    source: str = "SatNOGS DB"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    freshness: FreshnessState = FreshnessState.LIVE_RECENT

class GroundStation(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float
    altitude_m: float | None = None
    status: str | None = None
    antennas: list[str] = Field(default_factory=list)
    source: str = "SatNOGS Network"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    freshness: FreshnessState = FreshnessState.LIVE_RECENT

class ObservationArtifact(BaseModel):
    kind: str
    url: str
    label: str

class Observation(BaseModel):
    id: int
    satellite_id: str | None = None
    norad_id: int | None = None
    station_id: int
    station_name: str | None = None
    start: datetime
    end: datetime
    status: str | None = None
    frequency_hz: int | None = None
    mode: str | None = None
    transmitter_description: str | None = None
    station_latitude: float | None = None
    station_longitude: float | None = None
    station_altitude_m: float | None = None
    max_altitude_deg: float | None = None
    tle0: str | None = None
    tle1: str | None = None
    tle2: str | None = None
    artifacts: list[ObservationArtifact] = Field(default_factory=list)
    source: str = "SatNOGS Network"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    freshness: FreshnessState = FreshnessState.HISTORICAL

class OrbitPosition(BaseModel):
    latitude: float
    longitude: float
    altitude_km: float
    calculated_at: datetime
    label: str = "Calculated orbit position"
    freshness: FreshnessState = FreshnessState.CALCULATED

class PassWindow(BaseModel):
    rise: datetime
    culmination: datetime | None = None
    set: datetime | None = None
    max_elevation_deg: float | None = None

class SourceHealth(BaseModel):
    source: str
    state: FreshnessState
    last_success_at: datetime | None = None
    message: str | None = None

class DashboardData(BaseModel):
    satellites: int
    stations: int
    observations: int
    recent_observations: list[Observation] = Field(default_factory=list)
    stations_sample: list[GroundStation] = Field(default_factory=list)
    source_health: list[SourceHealth] = Field(default_factory=list)
