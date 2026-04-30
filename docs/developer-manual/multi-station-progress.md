# Multi-Station Support — Progress Tracker

Reference: [Implementation Plan](./multi-station-plan.md)

Legend: `done` / `in progress` / `todo` / `blocked`

---

## Phase 1 — Config: StationConfig model

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Add `StationConfig` model to `shared/libretime_shared/config/_models.py` | todo | |
| 1.2 | Update `Config` class in `playout/libretime_playout/config.py` | todo | Add `stations:`, keep `stream:` for compat |
| 1.3 | Add backward-compat `_normalize_stations` validator | todo | |
| 1.4 | Update `dev/config.yml` with 2-station example | todo | |
| 1.5 | Update `docker-compose.yml` — expose ports 8003, 8004 | todo | |
| 1.6 | Update config tests in `shared/tests/config/models_test.py` | todo | |

---

## Phase 2 — Database: station_id on cc_show

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | Create SQL migration `0047_add_station_id_to_show.py` | todo | DEFAULT 1, no FK |
| 2.2 | Add `station_id = IntegerField(default=1)` to Django `Show` model | todo | |
| 2.3 | Add read-only `GET /api/v2/stations/` endpoint (from config) | todo | |
| 2.4 | Expose `station_id` in `Show` serializer | todo | |
| 2.5 | Add `?station_id=N` filter to Schedule viewset | todo | Filter via `instance__show__station_id` |
| 2.6 | Tests: stations endpoint + schedule filter | todo | |

---

## Phase 3 — Liquidsoap multi-pipeline

| # | Task | Status | Notes |
|---|------|--------|-------|
| 3.1 | Refactor `ls_script.liq` into `create_station_pipeline(station_id)` function | todo | |
| 3.2 | Prefix all queue IDs and telnet commands with `station_N_` | todo | |
| 3.3 | Update `entrypoint.liq.j2` to loop over `config.stations` | todo | |
| 3.4 | Update `outputs.liq.j2` to reference `s_N` per station | todo | |
| 3.5 | Update `entrypoint.py` to pass `config.stations` to template | todo | |
| 3.6 | Adapt `ls_lib.liq` if needed (shared helpers) | todo | |
| 3.7 | Test: assert generated `.liq` script is valid for 2 stations | todo | |
| 3.8 | Integration test: start Liquidsoap with 2 pipelines via Docker | todo | |

---

## Phase 4 — Playout Python multi-station

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4.1 | `player/liquidsoap.py` — all commands accept `station_id`, prefix telnet calls | todo | |
| 4.2 | `player/schedule.py` — `get_schedule(station_id)` filters API | todo | |
| 4.3 | `player/fetch.py` — pass `station_id` through | todo | |
| 4.4 | `player/push.py` — pass `station_id` through | todo | |
| 4.5 | `main.py` — instantiate one `PypoFetch`+`PypoPush` pair per station | todo | |
| 4.6 | RabbitMQ messages — include `station_id` for routing | todo | |
| 4.7 | Integration test: 2 stations playing simultaneously | todo | |

---

## Phase 5 — Legacy PHP UI (optional)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 5.1 | PHP helper to fetch stations from `GET /api/v2/stations/` | todo | |
| 5.2 | Add `station_id` select to `AddShowForm.php` (hidden if 1 station) | todo | |
| 5.3 | Persist `station_id` in `ScheduleController.php` | todo | |
| 5.4 | Calendar filter dropdown by station | todo | Optional+ |

---

## Session notes

- **2026-04-30** — Plan finalized. Architecture decided: config-driven stations (no DB table
  for stations), single integer `station_id` on `cc_show`, backward compat via implicit
  station id=1 from existing `stream:` block. Phase 5 (UI) is optional and non-blocking.
