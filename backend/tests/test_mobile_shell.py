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
