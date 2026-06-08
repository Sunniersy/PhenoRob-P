from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_minio_init_retries_transient_alias_setup_failures():
    compose_text = (ROOT_DIR / "deploy/docker-compose.yml").read_text()
    minio_init_section = compose_text.split("  minio-init:", 1)[1].split(
        "\n  mosquitto:", 1
    )[0]
    entrypoint = minio_init_section.split("    entrypoint: >", 1)[1]

    assert "for attempt in" in entrypoint
    assert "mc alias set" in entrypoint
    assert "sleep" in entrypoint
    assert "mc mb --ignore-existing" in entrypoint
