from pathlib import Path


def test_dev_script_rebuilds_test_images_before_running_commands() -> None:
    script = (Path(__file__).resolve().parents[2] / "scripts" / "dev").read_text()

    assert "docker compose build backend-tests" in script
    assert "docker compose build mobile-typecheck" in script


def test_dev_script_runs_database_seeder_through_docker() -> None:
    script = (Path(__file__).resolve().parents[2] / "scripts" / "dev").read_text()

    assert "seed-db)" in script
    assert "docker compose build seed-db" in script
    assert "docker compose run --rm seed-db" in script
