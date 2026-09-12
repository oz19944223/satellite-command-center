from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from app.config import settings
from app.integrations.http import SafeHttpClient
from app.models.domain import Satellite, Transmitter

class SatnogsDbClient:
    source = "SatNOGS DB"
    def __init__(self, http: SafeHttpClient | None = None, base_url: str | None = None):
        self.http = http or SafeHttpClient(self.source, settings.timeout_seconds)
        self.base_url = (base_url or settings.satnogs_db_url).rstrip("/")

    @staticmethod
    def _rows(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list): return payload
        if isinstance(payload, dict) and isinstance(payload.get("results"), list): return payload["results"]
        return []

    @staticmethod
    def _sat_id(row: dict[str, Any]) -> str:
        return str(row.get("sat_id") or row.get("uuid") or row.get("norad_cat_id") or row.get("name") or "unknown")

    async def search_satellites(self, query: str) -> list[Satellite]:
        payload = await self.http.get_json(f"{self.base_url}/satellites/", {"format": "json", "search": query})
        now = datetime.now(timezone.utc)
        rows = self._rows(payload)
        q = query.strip().lower()
        if q:
            filtered = [r for r in rows if q in str(r.get("name", "")).lower() or q in str(r.get("norad_cat_id", "")).lower() or q in str(r.get("sat_id", "")).lower()]
            if filtered: rows = filtered
        result = []
        for row in rows[:50]:
            norad = row.get("norad_cat_id")
            identifiers = {}
            if row.get("sat_id"): identifiers["SatNOGS ID"] = str(row["sat_id"])
            if norad is not None: identifiers["NORAD"] = str(norad)
            result.append(Satellite(id=self._sat_id(row), name=str(row.get("name") or "Unknown"), norad_id=int(norad) if str(norad).isdigit() else None, identifiers=identifiers, status=row.get("status"), source=self.source, retrieved_at=now))
        return result

    async def get_satellite(self, satellite_id: str) -> Satellite | None:
        params = {"format": "json"}
        if satellite_id.isdigit(): params["norad_cat_id"] = satellite_id
        else: params["sat_id"] = satellite_id
        payload = await self.http.get_json(f"{self.base_url}/satellites/", params)
        rows = self._rows(payload)
        if not rows: return None
        row = rows[0]
        sat = (await self.search_satellites(str(row.get("norad_cat_id") or row.get("name") or satellite_id)))[0]
        sat.transmitters = await self.get_transmitters(sat.norad_id)
        # DB has a public TLE endpoint in the same API ecosystem.
        try:
            tle_payload = await self.http.get_json(f"{self.base_url}/tle/", {"format": "json", "norad_cat_id": sat.norad_id})
            tle_rows = self._rows(tle_payload)
            if tle_rows:
                tle = tle_rows[0]
                sat.tle0 = tle.get("tle0") or tle.get("tle_line0")
                sat.tle1 = tle.get("tle1") or tle.get("tle_line1")
                sat.tle2 = tle.get("tle2") or tle.get("tle_line2")
        except Exception:
            pass
        return sat

    async def get_transmitters(self, norad_id: int | None) -> list[Transmitter]:
        if norad_id is None: return []
        payload = await self.http.get_json(f"{self.base_url}/transmitters/", {"format": "json", "satellite__norad_cat_id": norad_id})
        out = []
        for row in self._rows(payload):
            out.append(Transmitter(id=str(row.get("uuid") or "unknown"), description=row.get("description"), downlink_low_hz=row.get("downlink_low"), downlink_high_hz=row.get("downlink_high"), mode=row.get("mode"), baud=row.get("baud"), status=row.get("status")))
        return out
