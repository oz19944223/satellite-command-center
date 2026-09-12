from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from app.config import settings
from app.integrations.http import SafeHttpClient, UpstreamError
from app.models.domain import FreshnessState, GroundStation, Observation, ObservationArtifact

class SatnogsNetworkClient:
    source = "SatNOGS Network"
    def __init__(self, http: SafeHttpClient | None = None, base_url: str | None = None):
        self.http = http or SafeHttpClient(self.source, settings.timeout_seconds)
        self.base_url = (base_url or settings.satnogs_network_url).rstrip("/")

    @staticmethod
    def _rows(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list): return payload
        if isinstance(payload, dict) and isinstance(payload.get("results"), list): return payload["results"]
        return []

    @staticmethod
    def _float(value: Any) -> float | None:
        try: return float(value)
        except (TypeError, ValueError): return None

    def _observation(self, row: dict[str, Any]) -> Observation:
        now = datetime.now(timezone.utc)
        artifacts: list[ObservationArtifact] = []
        if row.get("waterfall"):
            artifacts.append(ObservationArtifact(kind="waterfall", url=str(row["waterfall"]), label="Waterfall image"))
        if row.get("payload"):
            artifacts.append(ObservationArtifact(kind="audio", url=str(row["payload"]), label="Audio recording"))
        for item in row.get("demoddata") or []:
            if isinstance(item, dict) and item.get("payload_demod"):
                artifacts.append(ObservationArtifact(kind="data", url=str(item["payload_demod"]), label="Demodulated data"))
        norad = row.get("norad_cat_id")
        try: norad_i = int(norad) if norad is not None else None
        except (TypeError, ValueError): norad_i = None
        start = datetime.fromisoformat(str(row["start"]).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(row["end"]).replace("Z", "+00:00"))
        historical = end <= now
        freq = row.get("transmitter_downlink_low") or row.get("observation_frequency")
        return Observation(id=int(row["id"]), satellite_id=str(row.get("transmitter_uuid") or norad or "") or None, norad_id=norad_i, station_id=int(row["ground_station"]), station_name=row.get("station_name"), start=start, end=end, status=row.get("status"), frequency_hz=int(freq) if isinstance(freq, (int,float)) else None, mode=row.get("transmitter_mode"), transmitter_description=row.get("transmitter_description"), station_latitude=self._float(row.get("station_lat")), station_longitude=self._float(row.get("station_lng")), station_altitude_m=self._float(row.get("station_alt")), max_altitude_deg=self._float(row.get("max_altitude")), tle0=row.get("tle0"), tle1=row.get("tle1"), tle2=row.get("tle2"), artifacts=artifacts, source=self.source, retrieved_at=now, freshness=FreshnessState.HISTORICAL if historical else FreshnessState.LIVE_RECENT)

    async def list_observations(self, **filters: Any) -> list[Observation]:
        params: dict[str, Any] = {"format": "json"}
        params.update({k: v for k, v in filters.items() if v is not None and v != ""})
        payload = await self.http.get_json(f"{self.base_url}/observations/", params)
        return [self._observation(row) for row in self._rows(payload)[:100]]

    async def get_observation(self, observation_id: int) -> Observation | None:
        try:
            payload = await self.http.get_json(f"{self.base_url}/observations/{observation_id}/", {"format": "json"})
        except UpstreamError as exc:
            if exc.status_code == 404: return None
            raise
        if not isinstance(payload, dict): return None
        return self._observation(payload)

    async def list_stations(self) -> list[GroundStation]:
        now = datetime.now(timezone.utc)
        try:
            payload = await self.http.get_json(f"{self.base_url}/stations/", {"format": "json"})
            rows = self._rows(payload)
            out = []
            for row in rows[:250]:
                lat, lon = self._float(row.get("lat") or row.get("latitude")), self._float(row.get("lng") or row.get("longitude"))
                if lat is None or lon is None: continue
                antennas = row.get("antennas") or []
                if isinstance(antennas, list):
                    antennas = [str(a.get("antenna_type") or a.get("type") or a) if isinstance(a, dict) else str(a) for a in antennas]
                out.append(GroundStation(id=int(row["id"]), name=str(row.get("name") or f"Station {row['id']}"), latitude=lat, longitude=lon, altitude_m=self._float(row.get("alt") or row.get("altitude")), status=str(row.get("status")) if row.get("status") is not None else None, antennas=antennas, source=self.source, retrieved_at=now))
            if out: return out
        except UpstreamError:
            pass
        # Public observations always carry station coordinates; derive real station records if station listing is unavailable.
        observations = await self.list_observations()
        stations: dict[int, GroundStation] = {}
        for obs in observations:
            if obs.station_latitude is None or obs.station_longitude is None: continue
            stations[obs.station_id] = GroundStation(id=obs.station_id, name=obs.station_name or f"Station {obs.station_id}", latitude=obs.station_latitude, longitude=obs.station_longitude, altitude_m=obs.station_altitude_m, source=self.source, retrieved_at=now)
        return list(stations.values())
