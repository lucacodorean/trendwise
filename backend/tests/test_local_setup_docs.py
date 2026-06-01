from pathlib import Path


def test_readme_documents_local_prototype_startup() -> None:
    readme = (Path(__file__).resolve().parents[2] / "README.md").read_text()

    assert "./scripts/dev up" in readme
    assert "./scripts/dev test" in readme
    assert "./scripts/dev typecheck" in readme
    assert "./scripts/dev update" in readme
    assert ".env.example" in readme
