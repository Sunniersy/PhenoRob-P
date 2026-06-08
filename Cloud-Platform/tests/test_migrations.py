from pathlib import Path


def test_alembic_history_keeps_legacy_robot_commands_revision_resolvable():
    versions_dir = Path("alembic/versions")
    legacy_revision = versions_dir / "0002_robot_commands.py"
    compatibility_revision = versions_dir / "0002_platform_hardening.py"
    backfill_revision = versions_dir / "0003_platform_hardening_backfill.py"
    disable_demo_revision = versions_dir / "0004_disable_demo_analysis_default.py"

    assert legacy_revision.exists()
    assert 'revision = "0002_robot_commands"' in legacy_revision.read_text()
    assert 'down_revision = "0002_robot_commands"' in compatibility_revision.read_text()
    assert 'down_revision = "0002_platform_hardening"' in backfill_revision.read_text()
    assert 'down_revision = "0003_platform_hardening_backfill"' in disable_demo_revision.read_text()


def test_alembic_revision_identifiers_fit_default_version_table_column():
    versions_dir = Path("alembic/versions")

    for migration in versions_dir.glob("*.py"):
        content = migration.read_text()
        revision_line = next(line for line in content.splitlines() if line.startswith('revision = "'))
        revision = revision_line.split('"')[1]
        assert len(revision) <= 32, f"{migration.name} revision is too long for alembic_version.version_num"
