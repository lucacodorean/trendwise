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


def test_dev_script_runs_alembic_migrations_through_docker() -> None:
    script = (Path(__file__).resolve().parents[2] / "scripts" / "dev").read_text()
    seed_db_branch = script.split("seed-db)", 1)[1].split("generate-openapi)", 1)[0]

    assert "migrate-db" in script
    assert "docker compose build migrate-db" in script
    assert "docker compose run --rm migrate-db" in script
    assert seed_db_branch.index("docker compose run --rm migrate-db") < seed_db_branch.index(
        "docker compose run --rm seed-db"
    )


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


def test_dev_script_rejects_mobile_api_base_urls_without_protocol() -> None:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "dev"

    result = subprocess.run(
        ["/bin/sh", str(script_path), "up"],
        check=False,
        env={"EXPO_PUBLIC_API_BASE_URL": "192.168.1.10:8000", "PATH": "/no-such-path"},
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "EXPO_PUBLIC_API_BASE_URL must include http:// or https://" in result.stdout


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
    assert (
        "docker: not found" in result.stderr
        or "docker: command not found" in result.stderr
    )


def test_dev_script_declares_expo_helper_command() -> None:
    script = (Path(__file__).resolve().parents[2] / "scripts" / "dev").read_text()

    assert "expo" in script
    assert "Start backend stack and Expo dev server on LAN" in script
    assert "iphone" not in script


def test_dev_script_expo_helper_detects_lan_ip_and_prints_expo_url() -> None:
    script = (Path(__file__).resolve().parents[2] / "scripts" / "dev").read_text()
    expo_branch = script.split("expo)", 1)[1].split("test)", 1)[0]

    assert "detect_lan_ip" in script
    assert "ipconfig getifaddr en0" in script
    assert "ipconfig getifaddr en1" in script
    assert "EXPO_PUBLIC_API_BASE_URL=http://$LAN_IP:8000 docker compose up --build --detach backend postgres redis worker scheduler otel-collector jaeger" in script
    assert "EXPO_PUBLIC_API_BASE_URL=http://$LAN_IP:8000 docker compose run --rm seed-db" in script
    assert expo_branch.index("docker compose run --rm migrate-db") < expo_branch.index(
        "docker compose run --rm seed-db"
    )
    assert "cd mobile" in script
    assert "EXPO_PUBLIC_API_BASE_URL=http://$LAN_IP:8000 npx expo start --host lan" in script
    assert "exp://$LAN_IP:8081" in script
    assert "docker compose down" in script
