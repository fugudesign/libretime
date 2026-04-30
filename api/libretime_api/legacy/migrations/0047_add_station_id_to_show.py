# pylint: disable=invalid-name

from django.db import migrations

from ._migrations import legacy_migration_factory

UP = """
ALTER TABLE cc_show ADD COLUMN station_id INTEGER NOT NULL DEFAULT 1;
"""

DOWN = """
ALTER TABLE cc_show DROP COLUMN IF EXISTS station_id;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("legacy", "0046_add_override_intro_outro_playlists"),
    ]
    operations = [
        migrations.RunPython(
            code=legacy_migration_factory(
                target="47",
                sql=UP,
            )
        )
    ]
