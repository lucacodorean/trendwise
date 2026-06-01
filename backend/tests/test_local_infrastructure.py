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
        "mobile",
        "mobile-typecheck",
    }.issubset(services)
    assert services["backend"]["depends_on"] == ["postgres", "redis"]
    assert services["backend-tests"]["command"] == "python -m pytest -v"
    assert services["backend-tests"]["working_dir"] == "/workspace/backend"
    assert ".:/workspace" in services["backend-tests"]["volumes"]
    assert services["backend-tests"]["profiles"] == ["tools"]
    assert services["seed-db"]["profiles"] == ["tools"]
    assert services["seed-db"]["command"] == "python -m app.database.seed"
    assert services["mobile"]["command"] == "npm start -- --host lan"
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
