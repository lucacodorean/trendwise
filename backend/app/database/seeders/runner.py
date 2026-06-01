from collections.abc import Iterable

from app.database.seeders.base import DatabaseSeeder


def run_seeders(connection: object, seeders: Iterable[DatabaseSeeder]) -> None:
    for seeder in seeders:
        seeder.run(connection)
