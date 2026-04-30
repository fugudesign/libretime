# Multi-Station Support — Implementation Plan

## Context

LibreTime currently handles a single radio station: one Liquidsoap audio pipeline,
one schedule, and multiple Icecast outputs that all broadcast the **same stream**.

Goal: manage N independent stations within a single LibreTime instance, each with:
- Its own schedule (shows, schedule items)
- Its own Liquidsoap pipeline (queues, live inputs)
- Its own Icecast outputs (distinct mounts)
- While **sharing** the audio library, playlists, and smart blocks

## Architectural decision: config-driven stations

Stations are defined **only in `config.yml`**. No `cc_stations` database table.

Rationale:
- No complex UI CRUD needed
- Consistent with LibreTime's philosophy (stream outputs are already in config)
- Sufficient for real-world use (stations rarely change)
- Leaves the door open for an optional UI layer later

The only DB change: an integer `station_id` column on `cc_show`,
referencing the `id` of a station defined in config.

---

## Target architecture

```
config.yml
  stations:
    - id: 1  name: "Radio A"  stream: { inputs, outputs }
    - id: 2  name: "Radio B"  stream: { inputs, outputs }

Database (minimal change)
  cc_show -> station_id INTEGER  (references id from config)

Django API
  GET /api/v2/stations/   (read-only, served from config)
  show.station_id exposed in Show serializer
  GET /api/v2/schedule/?station_id=N

Playout Python
  Thread Station 1 -> queues "station_1_sN" -> Liquidsoap pipeline 1
  Thread Station 2 -> queues "station_2_sN" -> Liquidsoap pipeline 2

Liquidsoap (single process, N parallel pipelines)
  station_1: switch(harbor_main_1 | harbor_show_1 | queue_1 | default)
  station_2: switch(harbor_main_2 | harbor_show_2 | queue_2 | default)
       |                    |
       v                    v
  Icecast: /radio-a.ogg   Icecast: /radio-b.mp3

Legacy PHP UI (minimal)
  "Station" select field in add/edit show form
  (populated from /api/v2/stations/, hidden if only one station)
```

---

## Target config.yml format

`stream:` is replaced by `stations:`. Backward compatibility: if `stations:` is absent,
the system implicitly creates station id=1 from the existing `stream:` block.

```yaml
stations:
  - id: 1
    name: "Radio A"
    stream:
      inputs:
        main:
          public_url: https://localhost:8001/main
          mount: main-a
          port: 8001
          secure: true
        show:
          mount: show-a
          port: 8002
      outputs:
        .default: &default
          host: icecast
          port: 8000
          source_password: hackme
          admin_password: hackme
        icecast:
          - <<: *default
            enabled: true
            mount: radio-a.ogg
            audio: { format: ogg, bitrate: 256 }
          - <<: *default
            enabled: true
            mount: radio-a.mp3
            audio: { format: mp3, bitrate: 128 }

  - id: 2
    name: "Radio B"
    stream:
      inputs:
        main:
          mount: main-b
          port: 8003
        show:
          mount: show-b
          port: 8004
      outputs:
        icecast:
          - enabled: true
            host: icecast
            port: 8000
            mount: radio-b.ogg
            source_password: hackme
            admin_password: hackme
            audio: { format: ogg, bitrate: 256 }
```

Harbor port convention: station N uses ports `8000 + (N-1)*2 + 1` / `8000 + (N-1)*2 + 2`.
- Station 1 -> 8001 / 8002
- Station 2 -> 8003 / 8004
- Station 3 -> 8005 / 8006

---

## Impacted files

| Component | Files |
|-----------|-------|
| Shared config model | `shared/libretime_shared/config/_models.py` |
| Dev config | `dev/config.yml` |
| Docker configs | `docker/config.yml`, `docker/example/config.yml` |
| Docker compose | `docker-compose.yml` (extra harbor ports) |
| SQL migration | `api/libretime_api/legacy/migrations/0047_add_station_id_to_show.py` (new) |
| Django model | `api/libretime_api/schedule/models/show.py` |
| Django API | `api/libretime_api/schedule/serializers/`, `views/`, `router.py` |
| Playout player | `playout/libretime_playout/player/schedule.py`, `fetch.py`, `push.py`, `liquidsoap.py` |
| Playout main | `playout/libretime_playout/main.py` |
| Liquidsoap script | `playout/libretime_playout/liquidsoap/2.1/ls_script.liq` |
| Liquidsoap lib | `playout/libretime_playout/liquidsoap/2.1/ls_lib.liq` |
| Jinja2 template | `playout/libretime_playout/liquidsoap/templates/entrypoint.liq.j2` |
| Jinja2 template | `playout/libretime_playout/liquidsoap/templates/outputs.liq.j2` |
| Liquidsoap entrypoint | `playout/libretime_playout/liquidsoap/entrypoint.py` |
| Legacy UI form | `legacy/application/forms/AddShowForm.php` |
| Legacy UI controller | `legacy/application/controllers/ScheduleController.php` |
| Config tests | `shared/tests/config/models_test.py` |
| API tests | `api/libretime_api/schedule/tests/` |

---

## Phase 1 — Config: StationConfig model

> Foundation for everything else.

### 1.1 — Add StationConfig to shared/_models.py

```python
class StationConfig(BaseModel):
    id: int
    name: str
    stream: StreamConfig
```

### 1.2 — Update Config class in each component

`stream:` becomes optional, `stations:` is added. A validator provides backward compat:

```python
class Config(BaseConfig):
    ...
    stream: Optional[StreamConfig] = None   # backward compat
    stations: List[StationConfig] = []

    @model_validator(mode="after")
    def _normalize_stations(self):
        if not self.stations and self.stream:
            self.stations = [StationConfig(id=1, name="Default", stream=self.stream)]
        return self
```

Affected: `playout/libretime_playout/config.py` (and any other component using `stream:`).

### 1.3 — Update dev/config.yml

Replace `stream:` block with `stations:` containing 2 example stations.

### 1.4 — Update docker-compose.yml

Expose harbor ports for the second station (8003, 8004).

### 1.5 — Update config tests

Adapt `shared/tests/config/models_test.py` to cover `StationConfig` and the
backward-compat validator.

---

## Phase 2 — Database: station_id on cc_show

> Minimal DB change: a single integer column.

### 2.1 — SQL migration

New file `api/libretime_api/legacy/migrations/0047_add_station_id_to_show.py`:

```sql
-- forward
ALTER TABLE cc_show ADD COLUMN station_id INTEGER NOT NULL DEFAULT 1;

-- reverse
ALTER TABLE cc_show DROP COLUMN IF EXISTS station_id;
```

No FK constraint — the value references config, not a table. `DEFAULT 1` ensures
all existing shows fall into the default station.

### 2.2 — Django Show model

```python
station_id = models.IntegerField(default=1)
```

### 2.3 — Read-only stations endpoint

`GET /api/v2/stations/` returns the list from `settings.CONFIG.stations` (no DB model).
Simple APIView, returns `[{"id": 1, "name": "Radio A"}, ...]`.

### 2.4 — Show serializer

Expose `station_id` in the existing Show serializer.

### 2.5 — Schedule filter by station

In the Schedule viewset, support `GET /api/v2/schedule/?station_id=2`.
Filter via `instance__show__station_id`.

---

## Phase 3 — Liquidsoap multi-pipeline

> Most complex part. Single Liquidsoap process, N independent pipelines.

### 3.1 — Refactor ls_script.liq into a per-station function

Extract the current single pipeline into a function `create_station_pipeline(station_id)`:
- 4 queues: `station_N_s0` .. `station_N_s3`
- Harbor main input: `id="harbor:input_main_N"`, port/mount from config
- Harbor show input: `id="harbor:input_show_N"`
- Priority switch: `s_N = switch([main, show, queue, default])`
- All telnet server commands prefixed: `station_N.queues.s0_skip`, etc.
- Returns source `s_N`

Call it N times (once per station) from the entrypoint template.

### 3.2 — Update entrypoint.liq.j2

```jinja
{% for station in config.stations %}
{{ create_station_pipeline(station.id, station.stream.inputs) }}
{% endfor %}
```

### 3.3 — Update outputs.liq.j2

Each output references its station's source `s_N`:

```jinja
{% for station in config.stations %}
  {% for output in station.stream.outputs.icecast %}
    {{ output_icecast(station.id, loop.index, output, "s_" ~ station.id|string) }}
  {% endfor %}
{% endfor %}
```

### 3.4 — Update entrypoint.py (Python)

Pass `config.stations` to the Jinja2 template render call.

### 3.5 — Test .liq script generation

Add a unit test verifying the generated script for 2 stations is syntactically valid.

---

## Phase 4 — Playout Python multi-station

> Wire the schedule fetch and push threads to the right Liquidsoap pipeline per station.

### 4.1 — Liquidsoap client: station-prefixed commands

All methods in `player/liquidsoap.py` that send telnet commands accept `station_id`
and prefix accordingly: `station_N.queues.s0_push`, `station_N.sources.start_schedule`, etc.

### 4.2 — get_schedule(station_id)

In `player/schedule.py`: pass `station_id` as API filter param.

### 4.3 — PypoFetch and PypoPush per station

Each instance receives `station_id` in its constructor and uses it throughout.

### 4.4 — main.py: loop over stations

```python
for station in config.stations:
    liq = Liquidsoap(station_id=station.id, ...)
    fetch = PypoFetch(station_id=station.id, ...)
    push = PypoPush(station_id=station.id, ...)
    fetch.start()
    push.start()
```

### 4.5 — RabbitMQ messages

Push schedule messages must include `station_id` to route to the correct thread.

---

## Phase 5 — Legacy PHP UI (minimal, optional)

> Allow assigning a show to a station. Not blocking — station_id can be set via API or SQL.

### 5.1 — Read stations from API

PHP helper that calls `GET /api/v2/stations/` and returns `[(id, name), ...]`.

### 5.2 — Station field in show form

In `AddShowForm.php`: add a `<select>` for "Station", hidden if only one station.
Default value: 1.

### 5.3 — Persist station_id

In `ScheduleController.php`: save `station_id` when creating/editing a show.

### 5.4 — Calendar filter (optional+)

Dropdown in the calendar header to filter by active station.

---

## Tests

| Test file | Phase | Action |
|-----------|-------|--------|
| `shared/tests/config/models_test.py` | 1 | Extend for `StationConfig` and backward compat |
| `api/.../schedule/tests/views/test_schedule.py` | 2 | Test `?station_id=` filter |
| `api/.../schedule/tests/models/test_show.py` | 2 | Test `station_id` field |
| New: test .liq generation | 3 | Assert valid script for 2 stations |

Existing tests must not regress at any phase.

---

## Constraints and watch-outs

1. **Backward compat**: existing `stream:` format keeps working (implicit station id=1).

2. **No FK in DB**: `station_id` is a plain integer. If a station is removed from config,
   its shows keep the orphaned `station_id` — log a warning at playout startup.

3. **Single Icecast**: the existing Icecast container handles multiple mounts, no changes needed.

4. **Harbor ports**: each station needs 2 ports (main + show). See convention above.

5. **Liquidsoap single-threaded**: N pipelines in one process. Viable up to ~6 stations
   on a standard server.

6. **Phase 5 is optional**: fully functional without UI. Assign shows via REST API or SQL.
