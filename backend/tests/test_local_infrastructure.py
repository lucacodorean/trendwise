from pathlib import Path

import yaml


def test_docker_compose_declares_required_local_services() -> None:
    compose_path = Path(__file__).resolve().parents[2] / "docker-compose.yml"

    with compose_path.open() as compose_file:
        compose = yaml.safe_load(compose_file)

    services = compose["services"]

    assert {
        "backend",
        "backend-tests",
        "seed-db",
        "postgres",
        "redis",
        "worker",
        "scheduler",
        "otel-collector",
        "jaeger",
        "mobile-typecheck",
    }.issubset(services)
    assert "mobile" not in services
    assert services["backend"]["depends_on"] == ["postgres", "redis"]
    assert services["backend-tests"]["command"] == "python -m pytest -v"
    assert services["backend-tests"]["working_dir"] == "/workspace/backend"
    assert ".:/workspace" in services["backend-tests"]["volumes"]
    assert services["backend-tests"]["profiles"] == ["tools"]
    assert "migrate-db" in services
    assert services["migrate-db"]["profiles"] == ["tools"]
    assert services["migrate-db"]["command"] == "alembic upgrade head"
    assert services["migrate-db"]["working_dir"] == "/workspace/backend"
    assert ".:/workspace" in services["migrate-db"]["volumes"]
    assert services["migrate-db"]["env_file"] == ".env.example"
    assert services["migrate-db"]["depends_on"] == ["postgres"]
    assert services["seed-db"]["profiles"] == ["tools"]
    assert services["seed-db"]["command"] == "python -m app.database.seed"
    assert services["mobile-typecheck"]["command"] == "npm run typecheck"
    assert services["mobile-typecheck"]["profiles"] == ["tools"]


def test_backend_dockerfile_includes_tests_for_test_image() -> None:
    dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text()

    assert "COPY tests ./tests" in dockerfile


def test_compose_includes_mobile_openapi_generation_service() -> None:
    compose = (Path(__file__).resolve().parents[2] / "docker-compose.yml").read_text()

    assert "openapi-export:" in compose
    assert "mobile-openapi:" in compose
    assert "python -m app.openapi" in compose
    assert "npm run generate:api" in compose


def test_mobile_openapi_generation_refreshes_volume_dependencies() -> None:
    compose_path = Path(__file__).resolve().parents[2] / "docker-compose.yml"

    with compose_path.open() as compose_file:
        compose = yaml.safe_load(compose_file)

    assert compose["services"]["mobile-openapi"]["command"] == (
        'sh -c "npm install && npm run generate:api"'
    )


def test_mobile_typecheck_does_not_default_api_base_url_to_localhost() -> None:
    compose_path = Path(__file__).resolve().parents[2] / "docker-compose.yml"

    with compose_path.open() as compose_file:
        compose = yaml.safe_load(compose_file)

    assert compose["services"]["mobile-typecheck"]["environment"]["EXPO_PUBLIC_API_BASE_URL"] == (
        "${EXPO_PUBLIC_API_BASE_URL-}"
    )


def test_alembic_env_uses_psycopg_driver_for_plain_postgresql_urls() -> None:
    env = (Path(__file__).resolve().parents[1] / "migrations" / "env.py").read_text()
    compact_env = " ".join(env.split())

    assert "def sqlalchemy_database_url(database_url: str) -> str:" in env
    assert 'database_url.startswith("postgresql://")' in env
    assert 'database_url.replace("postgresql://", "postgresql+psycopg://", 1)' in env
    assert "url=sqlalchemy_database_url(settings.database_url)" in env
    assert "create_engine( sqlalchemy_database_url(settings.database_url)" in compact_env
