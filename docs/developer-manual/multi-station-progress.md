# Multi-Station Support — Progress Tracker

Reference: [Implementation Plan](./multi-station-plan.md)

Legend: `done` / `in progress` / `todo` / `blocked`

---

## Phase 1 — Config: StationConfig model

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Add `StationConfig` model to `shared/libretime_shared/config/_models.py` | done | |
| 1.2 | Update `Config` class in `playout/libretime_playout/config.py` | done | Add `stations:`, keep `stream:` for compat |
| 1.3 | Add backward-compat `_normalize_stations` validator | done | |
| 1.4 | Update `dev/config.yml` with 2-station example | done | |
| 1.5 | Update `docker-compose.yml` — expose ports 8003, 8004 | done | |
| 1.6 | Update config tests in `shared/tests/config/models_test.py` | done | 7/7 passing |

---

## Phase 2 — Database: station_id on cc_show

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | Create SQL migration `0047_add_station_id_to_show.py` | done | DEFAULT 1, no FK |
| 2.2 | Add `station_id = IntegerField(default=1)` to Django `Show` model | done | |
| 2.3 | Add read-only `GET /api/v2/stations/` endpoint (from config) | done | `StationsView` in `schedule/views/station.py` |
| 2.4 | Expose `station_id` in `Show` serializer | done | |
| 2.5 | Add `?station_id=N` filter to Schedule viewset | done | Filter via `instance__show__station_id` |
| 2.6 | Tests: stations endpoint + schedule filter | done | `tests/views/test_stations.py` |

---

## Phase 3 — Liquidsoap multi-pipeline

| # | Task | Status | Notes |
|---|------|--------|-------|
| 3.1 | Refactor `ls_script.liq` into `make_station_pipeline(station_id)` function | done | 1.4 + 2.1 |
| 3.2 | Prefix all queue IDs and telnet commands with `station_N_` | done | Queues `s{offset}..s{offset+3}`, cmds `station_{id}.*` |
| 3.3 | Update `entrypoint.liq.j2` to loop over `config.stations` | done | Produces `s_1 = make_station_pipeline(...)` etc. |
| 3.4 | Update `outputs.liq.j2` to reference `s_N` per station | done | Output IDs scoped as `{station_id}_{loop.index}` |
| 3.5 | `events.py` — `station_id` field on `FileEvent`/`WebStreamEvent` | done | |
| 3.6 | `schedule.py` — pass `station_id` from show when building events | done | |
| 3.7 | `liquidsoap.py` — per-station queue ranges + `find_available_queue(station_id)` | done | |
| 3.8 | `_client.py` — `source_switch_status` loops over station_ids | done | |
| 3.9 | `main.py` — pass `stations=[(s.id, i*4) …]` to `Liquidsoap` | done | |
| 3.10 | Template validation script | done | `tools/_validate_phase3.py` → all `[OK]` |

---

## Phase 4 — Playout Python multi-station (schedule fetch per station)

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4.1 | `player/schedule.py` — `get_schedule(station_id)` adds `?station_id=N` to API call | todo | |
| 4.2 | `PypoFetch` — receive `station_id`, filter fetched schedule per station | todo | |
| 4.3 | `PypoPush` / `PypoLiqQueue` — route items to correct station queues | todo | Already partially done via `file_event.station_id` → `find_available_queue` |
| 4.4 | `main.py` — one `PypoFetch`+`PypoPush` pair per station (or shared with filter) | todo | |
| 4.5 | RabbitMQ messages — include `station_id` for routing | todo | |
| 4.6 | Integration test: 2 stations playing simultaneously | todo | |

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
- **2026-04-30** — Phase 1 committed (`959b2e1`). Phase 2 committed (`453b7844f`).
  Phase 3 committed (`e4847233d`): Liquidsoap refactored into `make_station_pipeline()`,
  per-station queue ranges, telnet command namespacing, `station_id` on events, Python routing.
  Phase 4 next: schedule fetch filtered per station.
