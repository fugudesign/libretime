#!/usr/bin/env python3
"""Quick validation of Phase 3 template rendering."""
import sys
sys.path.insert(0, '/Users/vincent/Sites/lab/libretime/playout')

from tests.liquidsoap.fixtures import make_config_with_stream
from libretime_playout.liquidsoap.entrypoint import generate_entrypoint
from libretime_playout.liquidsoap.models import Info, StreamPreferences

config = make_config_with_stream(
    outputs={'icecast': [{'enabled': True, 'mount': 'main', 'source_password': 'hackme',
                          'audio': {'format': 'ogg', 'bitrate': 256}}]}
)
print('stations:', [(s.id, s.name) for s in config.stations])

prefs = StreamPreferences(
    input_fade_transition=0.0, message_format=1, message_offline='offline',
    replay_gain_enabled=False, replay_gain_offset=0.0
)
info = Info(station_name='Test')
result = generate_entrypoint(None, config, prefs, info, (1, 4, 0))

checks = [
    'make_station_pipeline', 's_1 =', 'queue_offset=0', 'station_id=1',
    'output_icecast_1_1_source', 'output.icecast('
]
for marker in checks:
    found = marker in result
    status = "OK" if found else "MISSING"
    print(f"[{status}] {marker!r}")

print("\n--- Pipeline call snippet ---")
start = result.find('s_1 = make_station_pipeline')
print(result[start:start+350])

print("\n--- Output snippet ---")
out_start = result.find('output_icecast_1_1')
print(result[out_start:out_start+200])
