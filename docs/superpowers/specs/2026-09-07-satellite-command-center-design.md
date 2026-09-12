# Satellite Command Center — V1 Design

Date: 2026-09-07
Status: Approved concept, pending user review of written specification

## 1. Goal

Build a Windows-friendly local web application called **Satellite Command Center** that presents real satellite and remote ground-station information in a professional command-center interface. V1 will be SatNOGS-first and will use real public/authorized data only. No simulated observations or fake live telemetry will be presented as real.

The product must make the provenance and freshness of every important data point clear: live/recent, cached, historical, or unavailable.

## 2. V1 Scope

V1 includes:

- Satellite catalogue search and filtering.
- Satellite details including identifiers and transmitter metadata when available.
- Interactive world map showing satellites and participating ground stations.
- Ground-station browser with status, location, antennas/capabilities and observation activity when exposed by the source.
- Observation browser for real SatNOGS observations.
- Observation detail view with available result artifacts such as waterfall, audio, decoded/demodulated data or related links when the upstream observation exposes them.
- Orbit/pass visualization from public orbital element data available through the selected upstream source(s).
- South Africa as the default map region, without restricting global use.
- Source/freshness badges for data displayed in the UI.
- Local caching to reduce unnecessary upstream API calls and improve responsiveness.
- Clear error and degraded-data states when an upstream service is unavailable or incomplete.

V1 does not include:

- Unauthorized access to encrypted or private satellite systems.
- Remote control of third-party ground stations unless their public APIs explicitly authorize that operation for the user/account.
- Transmission/uplink to satellites.
- Military/commercial private communications interception.
- Automated signal cracking or decryption.
- Paid commercial Earth-imagery integrations.
- AI-based intelligence analysis.
- User-owned SDR hardware control.

Those can be considered separately in later versions where technically and legally appropriate.

## 3. Data Sources

### 3.1 SatNOGS Network

Primary source for public ground-station and observation information. The integration will consume the official REST/OpenAPI interfaces available from SatNOGS Network.

Use cases:

- Observations and scheduled/public observation data.
- Ground-station information where available.
- Links/results associated with observations.
- Network-level satellite activity.

### 3.2 SatNOGS DB

Primary source for satellite and transmitter metadata.

Use cases:

- Satellite records.
- Satellite identifiers.
- Transmitter frequencies and modes.
- Metadata needed to determine whether an observation/station combination is meaningful.

### 3.3 Orbital data

V1 will use orbital elements exposed by or compatible with the SatNOGS ecosystem where available. The orbit module will be isolated so another public orbital source can be added later without changing the UI contracts.

## 4. Architecture

The application will use a three-layer architecture:

### Frontend

A modern single-page web interface running locally in the user's browser. It is responsible for:

- Command-center dashboard.
- Interactive map and orbit visualization.
- Satellite search.
- Ground-station and observation screens.
- Status/freshness indicators.
- User filters and preferences.

Recommended implementation: React + TypeScript with a map/globe library selected during implementation based on compatibility and bundle size.

### Backend

A local application service responsible for all external integrations and data normalization. The browser will not directly depend on SatNOGS response formats.

Responsibilities:

- SatNOGS Network API client.
- SatNOGS DB API client.
- Orbit/TLE retrieval and calculation services.
- Data normalization into stable internal models.
- Caching.
- Rate limiting/backoff.
- Health/status checks.
- API endpoints consumed by the frontend.

Recommended implementation: Python FastAPI. This keeps orbital/scientific processing straightforward and provides a clean path for later SDR/signal-processing integrations.

### Local data/cache

SQLite will store cached metadata and user preferences. Large observation artifacts will not be permanently copied by default; the system will preserve upstream URLs/references unless caching an artifact is explicitly needed.

## 5. Internal Modules

### Satellite Service

Provides search, satellite profiles, identifiers, transmitters and normalized metadata.

### Ground Station Service

Provides known stations, location/capabilities, latest-known activity and compatibility information.

### Observation Service

Provides observation lists, filtering, observation details and available result artifacts.

### Orbit Service

Parses orbital elements and computes positions/passes. Its API must not expose library-specific objects to the rest of the application.

### Source Health Service

Tracks upstream availability and last successful synchronization time. It feeds visible UI badges such as:

- LIVE/RECENT
- CACHED
- HISTORICAL
- SOURCE OFFLINE
- DATA UNAVAILABLE

### Cache Repository

Owns SQLite persistence and expiry logic. Other services do not write database queries directly.

## 6. Main User Experience

### Dashboard

The first screen opens centered on Southern Africa and includes:

- Global map/globe.
- Visible satellite markers/tracks when orbit data is available.
- Ground-station markers.
- Search box.
- Quick counts for satellites, stations and recent observations.
- Recent observation activity.
- Source-health indicator.

### Satellite Detail

Selecting a satellite opens a profile containing:

- Name and identifiers.
- Current calculated position when orbital data is available.
- Orbit track.
- Known transmitters/frequencies/modes.
- Recent observations.
- Ground stations that have recently observed it.
- Upcoming calculated passes for a selected station/location where possible.

### Ground Station Detail

Shows:

- Station name/identifier.
- Location.
- Antenna/capability metadata where available.
- Recent observations.
- Upcoming compatible satellite passes when enough metadata exists.

### Observation Detail

Shows:

- Satellite.
- Ground station.
- Observation start/end timestamps.
- Frequency/mode metadata when available.
- Quality/status information exposed upstream.
- Waterfall, audio, decoded/demodulated data or external result links where supplied.
- Exact data source and retrieval timestamp.

## 7. Real-Time Semantics

The application must not use the word **live** merely because information came from an API.

Definitions:

- **Live/Recent:** upstream information refreshed within the configured freshness window and representing current/recent network state.
- **Calculated:** locally calculated from current orbital elements, not a direct satellite measurement.
- **Historical:** completed observation data.
- **Cached:** a previously retrieved upstream record currently being shown because refresh has not occurred or upstream is unavailable.

Every satellite position will be labeled **Calculated orbit position** unless it is genuinely sourced from real-time tracking telemetry.

## 8. Networking and API Safety

- External API calls occur server-side through adapters.
- Timeouts are mandatory.
- Retries use bounded exponential backoff.
- HTTP failures do not crash the UI.
- Upstream response schemas are validated before entering the application model.
- Any API token added later is stored outside frontend code and is never committed to source control.
- Public data access remains read-only by default.

## 9. Error Handling

Examples:

- If SatNOGS Network is offline, cached observations remain visible and are marked CACHED / SOURCE OFFLINE.
- If SatNOGS DB is unavailable, known satellite metadata can remain cached while new searches report limited availability.
- If orbital elements are stale or absent, no current orbit position is fabricated; the UI states that orbit data is unavailable/stale.
- If an observation has no audio/waterfall/result artifact, the control is hidden or marked unavailable rather than producing a dead fake player.

## 10. Testing Strategy

### Backend

- Unit tests for each upstream API adapter using fixed response fixtures.
- Unit tests for normalization and cache expiry.
- Orbit calculation tests using known reference cases.
- Failure tests for timeout, malformed upstream payloads and unavailable APIs.
- Contract tests for frontend-facing endpoints.

### Frontend

- Component tests for loading, success, empty and failure states.
- Tests that source/freshness labels are correctly displayed.
- Map interaction tests at the component/integration level where practical.

### End-to-end

A small E2E suite will verify:

1. App starts locally.
2. Satellite search returns a real record.
3. Satellite profile opens.
4. Ground station page opens.
5. Recent observations load.
6. Observation detail clearly distinguishes actual observation data from calculated orbit information.

## 11. Project Layout

```text
satellite-command-center/
  backend/
    app/
      api/
      integrations/
        satnogs_network/
        satnogs_db/
      services/
      models/
      repositories/
      orbit/
    tests/
  frontend/
    src/
      api/
      components/
      features/
        dashboard/
        satellites/
        stations/
        observations/
      map/
      types/
    tests/
  docs/
    superpowers/specs/
  scripts/
  README.md
```

## 12. V1 Success Criteria

The build is considered a successful V1 when:

1. It launches locally on Windows with documented startup steps.
2. The dashboard uses real SatNOGS-derived data.
3. A user can search for a satellite and inspect its metadata.
4. A user can browse real ground stations and observations.
5. Available observation artifacts can be opened/viewed from the observation screen.
6. Orbit positions and passes are clearly labeled as calculated rather than direct telemetry.
7. The app continues functioning in a degraded read-only mode when an upstream API is temporarily unavailable.
8. There are no deliberately fabricated satellite, station, observation or telemetry records in production mode.

## 13. Future Expansion Hooks

The architecture deliberately leaves room for:

- Additional public satellite networks/APIs.
- Weather imagery.
- Fire/flood/vegetation Earth observation layers.
- User-owned SatNOGS/SDR station integration.
- Authorized remote station scheduling/control.
- Alerts and notifications.
- Historical change analysis.
- AI-assisted signal/data classification.
- Packaged Windows desktop distribution.

These are not part of V1.
