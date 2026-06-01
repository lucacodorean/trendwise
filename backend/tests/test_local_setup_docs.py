from pathlib import Path


def test_readme_documents_local_prototype_startup() -> None:
    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text()

    assert "./scripts/dev up" in readme
    assert "./scripts/dev test" in readme
    assert "./scripts/dev typecheck" in readme
    assert "./scripts/dev update" in readme
    assert ".env.example" in readme


def test_mobile_api_base_url_is_documented_for_physical_devices() -> None:
    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text()

    assert "EXPO_PUBLIC_API_BASE_URL" in readme
    assert "physical devices" in readme
    assert "http://192.168.x.x:8000" in readme


def test_mobile_api_base_url_is_available_to_compose_services() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    env_example = (repo_root / ".env.example").read_text()
    compose = (repo_root / "docker-compose.yml").read_text()

    assert "EXPO_PUBLIC_API_BASE_URL=http://localhost:8000" in env_example
    assert "EXPO_PUBLIC_API_BASE_URL: ${EXPO_PUBLIC_API_BASE_URL:-http://localhost:8000}" in compose
    assert compose.count("EXPO_PUBLIC_API_BASE_URL: ${EXPO_PUBLIC_API_BASE_URL:-http://localhost:8000}") >= 2
