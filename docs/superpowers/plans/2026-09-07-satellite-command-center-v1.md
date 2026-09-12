# Satellite Command Center V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows-friendly local web application that browses real public SatNOGS satellite, ground-station, observation, artifact, and calculated orbit/pass information without fabricating live telemetry.

**Architecture:** A React + TypeScript SPA consumes only a local FastAPI API. FastAPI adapters isolate SatNOGS Network/DB formats, services normalize records, an orbit module computes positions/passes from orbital elements, and SQLite caches data plus source-health metadata.

**Tech Stack:** Python 3.12+, FastAPI, httpx, Pydantic v2, SQLite, Skyfield, pytest; Node 22+, React, TypeScript, Vite, TanStack Query, Leaflet/React-Leaflet, Vitest/Testing Library, Playwright.

**Spec:** `docs/superpowers/specs/2026-09-07-satellite-command-center-design.md`

## Global Constraints
- Real public/authorized data only; no fabricated production records.
- Calculated satellite positions display `Calculated orbit position`.
- External APIs are accessed server-side and read-only.
- Timeouts, bounded exponential backoff, schema validation, cache degradation, and source freshness are mandatory.
- Missing/stale orbital data never generates a fake current position.
- Default map region is Southern Africa; global browsing remains available.
- V1 excludes uplink, decryption, unauthorized control/interception, paid imagery, AI intelligence analysis, and SDR hardware control.

---

### Task 1: Backend foundation and domain contract
**Files:** `backend/pyproject.toml`, `backend/app/config.py`, `backend/app/models/domain.py`, `backend/app/main.py`, `backend/tests/test_health_api.py`

**Interfaces:** Produces `Satellite`, `Transmitter`, `GroundStation`, `Observation`, `ObservationArtifact`, `OrbitPosition`, `SourceHealth`; `create_app() -> FastAPI`; `GET /api/health`.

- [ ] Write a failing TestClient test asserting `GET /api/health` returns `{"app":"ok"}`.
- [ ] Run `cd backend && python -m pytest tests/test_health_api.py -v`; expect import failure.
- [ ] Define normalized Pydantic models. `OrbitPosition.label` defaults exactly to `Calculated orbit position`.
- [ ] Implement FastAPI app factory and health endpoint.
- [ ] Run `python -m pytest -v`; expect PASS.
- [ ] Commit: `git commit -m "feat: establish satellite command backend"`.

### Task 2: Safe HTTP transport and SatNOGS adapters
**Files:** `backend/app/integrations/http.py`, `backend/app/integrations/satnogs_db/client.py`, `backend/app/integrations/satnogs_network/client.py`, fixture JSON files, `backend/tests/test_satnogs_clients.py`

**Interfaces:** `SafeHttpClient.get_json(url, params=None)`, `SatnogsDbClient.search_satellites(query) -> list[Satellite]`, `SatnogsNetworkClient.list_stations() -> list[GroundStation]`, `list_observations(**filters) -> list[Observation]`.

- [ ] Capture small schema-faithful fixtures and write failing normalization/malformed-payload tests.
- [ ] Run adapter tests; expect FAIL.
- [ ] Implement `httpx.AsyncClient(timeout=10)` with retries for connection/time-out/429/5xx only, delays 0.5/1/2 seconds, max four attempts; final failure raises typed `UpstreamError`.
- [ ] Implement adapters; keep every upstream field-name dependency inside adapter modules. Missing optional values remain absent/None, never invented.
- [ ] Run adapter tests; expect PASS.
- [ ] Commit: `feat: add validated SatNOGS adapters`.

### Task 3: SQLite cache and source health
**Files:** `backend/app/repositories/cache.py`, `backend/app/services/health.py`, `backend/tests/test_cache.py`, `backend/tests/test_source_health.py`

**Interfaces:** `put(namespace,key,payload,retrieved_at,expires_at)`, `get(namespace,key) -> CacheEntry|None`; source-health `record_success`, `record_failure`, `get`.

- [ ] Write failing tests proving fresh=`LIVE_RECENT`, expired real cache remains readable=`CACHED`, and source failure retains `last_success_at` while becoming `SOURCE_OFFLINE`.
- [ ] Run tests; expect FAIL.
- [ ] Implement `cache_entries` and `source_health` SQLite tables behind the repository only.
- [ ] Implement health-state mapping including `DATA_UNAVAILABLE`.
- [ ] Run tests; expect PASS.
- [ ] Commit: `feat: add resilient local satellite cache`.

### Task 4: Domain services
**Files:** `backend/app/services/satellites.py`, `stations.py`, `observations.py`, `backend/tests/test_services.py`

**Interfaces:** `SatelliteService.search/get`, `StationService.list/get`, `ObservationService.list/get`.

- [ ] Write fake-adapter tests: successful first fetch fills cache; later `UpstreamError` returns cached real data with cached/offline provenance. Empty upstream artifact arrays stay empty.
- [ ] Run tests; expect FAIL.
- [ ] Implement service/cache policy: satellite metadata TTL 24h, stations 15m, recent observations 2m.
- [ ] Run tests; expect PASS.
- [ ] Commit: `feat: normalize satellite network services`.

### Task 5: Orbit and pass calculations
**Files:** `backend/app/orbit/service.py`, `backend/tests/test_orbit_service.py`

**Interfaces:** `position(tle_lines, at) -> OrbitPosition`; `passes(tle_lines, latitude, longitude, start, hours=24) -> list[PassWindow]`.

- [ ] Write a fixed historical TLE/time reference test with explicit coordinate/altitude tolerances; assert the exact calculated label. Add missing/stale TLE tests expecting typed `OrbitUnavailable`.
- [ ] Run tests; expect FAIL.
- [ ] Isolate Skyfield parsing/calculation inside OrbitService and return only normalized numeric models.
- [ ] Implement rise/culmination/set pass windows with maximum elevation.
- [ ] Run tests; expect PASS.
- [ ] Commit: `feat: add calculated orbit and pass service`.

### Task 6: Frontend-facing API
**Files:** `backend/app/api/routes.py`, modify `backend/app/main.py`, `backend/tests/test_api_contract.py`

**Interfaces:** `GET /api/satellites?q=`, `/satellites/{id}`, `/stations`, `/stations/{id}`, `/observations`, `/observations/{id}`, `/orbit/{satellite_id}`, `/passes/{satellite_id}?lat=&lon=`, `/sources/health`.

- [ ] Write failing contract tests with dependency-overridden services; assert normalized JSON, ISO timestamps, provenance, 404/422/503 semantics, and calculated orbit label.
- [ ] Run tests; expect FAIL.
- [ ] Implement routers with no SQL or SatNOGS field parsing.
- [ ] Run complete backend suite; expect PASS.
- [ ] Commit: `feat: expose satellite command API`.

### Task 7: Frontend shell and provenance
**Files:** Vite React/TS scaffold; `src/api/client.ts`, `types/domain.ts`, `components/AppShell.tsx`, `SourceBadge.tsx`, badge tests.

**Interfaces:** typed Task-6 API client; `<SourceBadge state retrievedAt />`.

- [ ] Write failing tests for exact labels: `LIVE / RECENT`, `CALCULATED`, `HISTORICAL`, `CACHED`, `SOURCE OFFLINE`, `DATA UNAVAILABLE`.
- [ ] Run `npm test -- --run`; expect FAIL.
- [ ] Scaffold Vite/React/TS and TanStack Query. Frontend calls `/api/*` only.
- [ ] Build desktop-first dark command-center shell. Loading states never show fake counts.
- [ ] Run tests and `npm run build`; expect PASS.
- [ ] Commit: `feat: create satellite command frontend shell`.

### Task 8: Dashboard map and activity
**Files:** `src/map/CommandMap.tsx`, `features/dashboard/DashboardPage.tsx`, dashboard tests.

- [ ] Write failing tests that real returned station coordinates become markers, orbit markers show `CALCULATED`, and failures produce `SOURCE OFFLINE` with no dummy markers.
- [ ] Run tests; expect FAIL.
- [ ] Implement Leaflet map centered approximately `-30,25`, station markers, calculated orbit positions/tracks only when data exists, source health, real counts and recent observations.
- [ ] Run tests/build; expect PASS.
- [ ] Commit: `feat: add real-data satellite dashboard`.

### Task 9: Satellite search/profile
**Files:** `features/satellites/SatelliteSearch.tsx`, `SatelliteDetailPage.tsx`, tests.

- [ ] Write failing search-to-profile tests covering identifiers, transmitters, observations, `Orbit data unavailable`, and calculated position label.
- [ ] Run tests; expect FAIL.
- [ ] Implement debounced search and profile. Never invent transmitter values; show passes only with sufficient location/orbit data.
- [ ] Run tests/build; expect PASS.
- [ ] Commit: `feat: add satellite search and profiles`.

### Task 10: Stations and observations
**Files:** `features/stations/StationDetailPage.tsx`, `features/observations/ObservationList.tsx`, `ObservationDetailPage.tsx`, tests.

- [ ] Write failing tests proving only actual waterfall/audio/data artifacts render. For `artifacts=[]`, show `No result artifacts supplied` and no fake player.
- [ ] Run tests; expect FAIL.
- [ ] Implement station metadata/activity/passes and observation detail with exact source/retrieval timestamp and safe external artifact links.
- [ ] Run tests/build; expect PASS.
- [ ] Commit: `feat: add station and observation explorer`.

### Task 11: E2E, Windows startup, degraded mode
**Files:** `frontend/e2e/core-flow.spec.ts`, `scripts/dev.ps1`, `README.md`, integration config.

- [ ] Write Playwright flow: app starts, real satellite search/profile works, station opens, observations load, observation data is distinguishable from calculated orbit data. Add deterministic offline test using pre-seeded real fixture cache and unreachable upstream, expecting `CACHED` + `SOURCE OFFLINE`.
- [ ] Run E2E; expect initial FAIL.
- [ ] Implement PowerShell launcher for FastAPI `127.0.0.1:8000` and Vite `127.0.0.1:5173`, with child-process cleanup.
- [ ] Complete proxy/CORS and README with Windows prerequisites, setup, start/test commands, cache semantics, and remote-observation-vs-direct-control explanation.
- [ ] Run backend pytest, frontend Vitest, Vite production build, and Playwright; all must PASS.
- [ ] Manually smoke-test current public data and verify freshness/source labels.
- [ ] Commit: `feat: complete satellite command center v1`.

## Final Verification Gate
- Backend, frontend, build, and Playwright suites all pass.
- No direct SatNOGS credentials/upstream dependency exists in frontend source.
- No production fixture/demo data is represented as real.
- Network outage visibly degrades to cached/offline semantics.
- Every orbital position is visibly identified as calculated.
- Missing artifacts remain unavailable rather than fake.
- Windows startup instructions work from a clean shell.
