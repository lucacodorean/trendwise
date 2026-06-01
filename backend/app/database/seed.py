from app.database.connection import open_database_connection
from app.database.seeders import SEEDERS
from app.database.seeders.runner import run_seeders


def main() -> None:
    with open_database_connection() as connection:
        run_seeders(connection, SEEDERS)


if __name__ == "__main__":
    main()
