# Satellite Command Center

Satellite Command Center is a local, Windows-friendly dashboard for real public satellite information from the SatNOGS ecosystem. It does **not** fabricate live telemetry: actual SatNOGS ground-station observations are labeled as observations, cached records are labeled cached/offline, and orbital positions are labeled **Calculated orbit position**.

## What V1 does

- Searches public SatNOGS satellite metadata and transmitter frequencies/modes.
- Browses public SatNOGS Network observations.
- Shows participating ground stations, or derives station positions from real observation records if the station-list endpoint is unavailable.
- Opens published waterfall, audio, and demodulated-data artifacts when an observation actually supplies them.
- Calculates satellite position/pass data from TLEs when orbital elements and the Skyfield dependency are available.
- Keeps a local SQLite cache so previously retrieved real records can remain visible during an upstream outage.
- Starts as a local web app on `127.0.0.1:8000`.

## Windows install

Requirements: Windows 10/11, Python 3.12 or newer, and an internet connection for the first dependency install and for live satellite data.

Open PowerShell in the project folder and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install.ps1
.\scripts\start.ps1
```

Your browser opens to `http://127.0.0.1:8000`.

## Data sources

- SatNOGS DB: satellite metadata, identifiers, transmitters and available orbital elements.
- SatNOGS Network: ground-station observations and result artifacts.

External requests are read-only and happen in the local Python backend. The browser never needs a SatNOGS credential.

## Data labels

- `LIVE / RECENT`: recently fetched public source data.
- `HISTORICAL`: completed real ground-station observation.
- `CALCULATED`: computed locally from orbital elements; not direct telemetry.
- `CACHED`: a real record previously fetched from the upstream source.
- `SOURCE OFFLINE`: the upstream source cannot currently be refreshed.
- `DATA UNAVAILABLE`: the app does not have enough real information to show the requested value.

## Tests

```powershell
.\scripts\test.ps1
```

or from the repository root:

```text
PYTHONPATH=backend python -m pytest backend/tests -v
```

## Cache location

The default cache is stored at:

`%USERPROFILE%\.satellite-command-center\cache.sqlite3`

No observation audio/waterfall files are permanently copied by default; the app keeps the upstream artifact links.

## Direct satellite communication vs this app

This V1 uses remote public ground-station data over the internet. It does not transmit to satellites or take unauthorized control of remote stations. A later version can add your own SDR/antenna hardware or authorized station scheduling without changing the public-data API layer.
