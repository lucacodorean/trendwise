import csv
from pathlib import Path


DEFAULT_SEED_FILE = Path(__file__).resolve().parents[1] / "seed_data" / "supported_stocks.csv"


class SupportedStocksSeeder:
    name = "supported_stocks"

    def __init__(self, seed_file: Path = DEFAULT_SEED_FILE) -> None:
        self.seed_file = seed_file

    def run(self, connection: object) -> None:
        with connection.cursor() as cursor:
            with self.seed_file.open(newline="") as seed_data:
                for row in csv.DictReader(seed_data):
                    if not self._is_supported_common_stock(row):
                        continue

                    ticker = row["ticker"].strip().upper()
                    company_name = row["company_name"].strip()
                    exchange = row["exchange"].strip()
                    params = {
                        "ticker": ticker,
                        "company_name": company_name,
                        "exchange": exchange,
                        "instrument_type": row["instrument_type"].strip(),
                        "region": row["region"].strip(),
                        "is_supported": True,
                        "search_text": f"{ticker} {company_name} {exchange}".lower(),
                    }
                    cursor.execute(
                        """
                        INSERT INTO stocks (
                            ticker,
                            company_name,
                            exchange,
                            instrument_type,
                            region,
                            is_supported,
                            search_text
                        ) VALUES (
                            %(ticker)s,
                            %(company_name)s,
                            %(exchange)s,
                            %(instrument_type)s,
                            %(region)s,
                            %(is_supported)s,
                            %(search_text)s
                        )
                        ON CONFLICT (ticker) DO UPDATE SET
                            company_name = EXCLUDED.company_name,
                            exchange = EXCLUDED.exchange,
                            instrument_type = EXCLUDED.instrument_type,
                            region = EXCLUDED.region,
                            is_supported = EXCLUDED.is_supported,
                            search_text = EXCLUDED.search_text
                        """,
                        params,
                    )

        connection.commit()

    def _is_supported_common_stock(self, row: dict[str, str]) -> bool:
        return (
            row["is_supported"].strip().lower() == "true"
            and row["instrument_type"].strip() == "common_stock"
            and row["region"].strip() == "US"
        )
