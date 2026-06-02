import json
from pathlib import Path


def test_mobile_shell_declares_expo_typescript_start_script() -> None:
    mobile_path = Path(__file__).resolve().parents[2] / "mobile"

    package_json = json.loads((mobile_path / "package.json").read_text())

    assert package_json["scripts"]["start"] == "expo start"
    assert "expo" in package_json["dependencies"]
    assert "typescript" in package_json["devDependencies"]
    assert (mobile_path / "App.tsx").exists()
    assert (mobile_path / "app.json").exists()


def test_mobile_config_does_not_point_physical_devices_at_localhost() -> None:
    app_json = json.loads(
        (Path(__file__).resolve().parents[2] / "mobile" / "app.json").read_text()
    )

    assert "localhost" not in json.dumps(app_json)


def test_mobile_api_derives_backend_url_from_expo_dev_server_when_env_is_missing() -> None:
    stocks_api = (
        Path(__file__).resolve().parents[2] / "mobile" / "src" / "api" / "stocks.ts"
    ).read_text()

    assert "NativeModules.SourceCode.scriptURL" in stocks_api
    assert "http://${host}:8000" in stocks_api
    assert '?? "http://localhost:8000"' not in stocks_api
