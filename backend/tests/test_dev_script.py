import subprocess
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


def test_dev_script_generates_mobile_openapi_client_through_docker() -> None:
    script = (Path(__file__).resolve().parents[2] / "scripts" / "dev").read_text()

    assert "generate-openapi" in script
    assert "docker compose build openapi-export" in script
    assert "docker compose run --rm openapi-export" in script
    assert "docker compose build mobile-openapi" in script
    assert "docker compose run --rm mobile-openapi" in script


def test_dev_script_renders_config_with_tool_services() -> None:
    script = (Path(__file__).resolve().parents[2] / "scripts" / "dev").read_text()

    assert "docker compose --profile tools config" in script


def test_dev_script_requires_mobile_api_base_url_before_lan_startup() -> None:
    script = (Path(__file__).resolve().parents[2] / "scripts" / "dev").read_text()

    assert "require_mobile_api_base_url" in script
    assert "EXPO_PUBLIC_API_BASE_URL is required before ./scripts/dev up" in script
    assert "http://192.168.x.x:8000" in script


def test_dev_script_rejects_loopback_mobile_api_base_urls() -> None:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "dev"

    for base_url in ("http://localhost", "http://127.0.0.1"):
        result = subprocess.run(
            ["/bin/sh", str(script_path), "up"],
            check=False,
            env={"EXPO_PUBLIC_API_BASE_URL": base_url, "PATH": "/no-such-path"},
            text=True,
            capture_output=True,
        )

        assert result.returncode == 2
        assert "EXPO_PUBLIC_API_BASE_URL is required before ./scripts/dev up" in result.stdout


def test_dev_script_prefers_inline_mobile_api_base_url_over_dotenv(tmp_path: Path) -> None:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "dev"
    (tmp_path / ".env").write_text("EXPO_PUBLIC_API_BASE_URL=http://192.168.1.10:8000\n")

    result = subprocess.run(
        ["/bin/sh", str(script_path), "up"],
        check=False,
        cwd=tmp_path,
        env={"EXPO_PUBLIC_API_BASE_URL": "http://localhost", "PATH": "/no-such-path"},
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "EXPO_PUBLIC_API_BASE_URL is required before ./scripts/dev up" in result.stdout


def test_dev_script_allows_inline_lan_url_to_override_stale_dotenv(tmp_path: Path) -> None:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "dev"
    (tmp_path / ".env").write_text("EXPO_PUBLIC_API_BASE_URL=http://localhost\n")

    result = subprocess.run(
        ["/bin/sh", str(script_path), "up"],
        check=False,
        cwd=tmp_path,
        env={"EXPO_PUBLIC_API_BASE_URL": "http://192.168.1.10:8000", "PATH": "/no-such-path"},
        text=True,
        capture_output=True,
    )

    assert result.returncode == 127
    assert "docker: not found" in result.stderr
