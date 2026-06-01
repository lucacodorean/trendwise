from typing import Protocol


class DatabaseSeeder(Protocol):
    name: str

    def run(self, connection: object) -> None:
        """Seed database records using the provided connection."""
