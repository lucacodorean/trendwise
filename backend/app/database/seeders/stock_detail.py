import csv
from pathlib import Path


DEFAULT_SEED_FILE = Path(__file__).resolve().parents[1] / "seed_data" / "stock_detail.csv"


class StockDetailSeeder:
    name = "stock_detail"

    def __init__(self, seed_file: Path = DEFAULT_SEED_FILE) -> None:
        self.seed_file = seed_file

    def run(self, connection: object) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_market_details (
                    ticker TEXT PRIMARY KEY REFERENCES supported_stocks(ticker),
                    latest_price NUMERIC NOT NULL,
                    daily_change NUMERIC NOT NULL,
                    daily_change_percent NUMERIC NOT NULL,
                    observed_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_forecast_details (
                    ticker TEXT NOT NULL REFERENCES supported_stocks(ticker),
                    horizon TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status = 'unavailable'),
                    generated_at TIMESTAMPTZ NOT NULL,
                    PRIMARY KEY (ticker, horizon)
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_prediction_details (
                    ticker TEXT NOT NULL REFERENCES supported_stocks(ticker),
                    horizon TEXT NOT NULL,
                    direction TEXT NOT NULL CHECK (direction IN ('bullish', 'bearish', 'neutral')),
                    confidence NUMERIC NOT NULL,
                    expected_change_percent NUMERIC NOT NULL,
                    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
                    generated_at TIMESTAMPTZ NOT NULL,
                    PRIMARY KEY (ticker, horizon)
                )
                """
            )

            with self.seed_file.open(newline="") as seed_data:
                for row in csv.DictReader(seed_data):
                    ticker = row["ticker"].strip().upper()
                    horizon = row["horizon"].strip()

                    market_params = {
                        "ticker": ticker,
                        "latest_price": float(row["latest_price"]),
                        "daily_change": float(row["daily_change"]),
                        "daily_change_percent": float(row["daily_change_percent"]),
                        "observed_at": row["observed_at"].strip(),
                    }
                    cursor.execute(
                        """
                        INSERT INTO stock_market_details (
                            ticker,
                            latest_price,
                            daily_change,
                            daily_change_percent,
                            observed_at
                        ) VALUES (
                            %(ticker)s,
                            %(latest_price)s,
                            %(daily_change)s,
                            %(daily_change_percent)s,
                            %(observed_at)s
                        )
                        ON CONFLICT (ticker) DO UPDATE SET
                            latest_price = EXCLUDED.latest_price,
                            daily_change = EXCLUDED.daily_change,
                            daily_change_percent = EXCLUDED.daily_change_percent,
                            observed_at = EXCLUDED.observed_at
                        """,
                        market_params,
                    )

                    forecast_params = {
                        "ticker": ticker,
                        "horizon": horizon,
                        "status": row["forecast_status"].strip(),
                        "generated_at": row["forecast_generated_at"].strip(),
                    }
                    cursor.execute(
                        """
                        INSERT INTO stock_forecast_details (
                            ticker,
                            horizon,
                            status,
                            generated_at
                        ) VALUES (
                            %(ticker)s,
                            %(horizon)s,
                            %(status)s,
                            %(generated_at)s
                        )
                        ON CONFLICT (ticker, horizon) DO UPDATE SET
                            status = EXCLUDED.status,
                            generated_at = EXCLUDED.generated_at
                        """,
                        forecast_params,
                    )

                    prediction_params = {
                        "ticker": ticker,
                        "horizon": horizon,
                        "direction": row["prediction_direction"].strip(),
                        "confidence": float(row["prediction_confidence"]),
                        "expected_change_percent": float(
                            row["prediction_expected_change_percent"]
                        ),
                        "risk_level": row["prediction_risk_level"].strip(),
                        "generated_at": row["prediction_generated_at"].strip(),
                    }
                    cursor.execute(
                        """
                        INSERT INTO stock_prediction_details (
                            ticker,
                            horizon,
                            direction,
                            confidence,
                            expected_change_percent,
                            risk_level,
                            generated_at
                        ) VALUES (
                            %(ticker)s,
                            %(horizon)s,
                            %(direction)s,
                            %(confidence)s,
                            %(expected_change_percent)s,
                            %(risk_level)s,
                            %(generated_at)s
                        )
                        ON CONFLICT (ticker, horizon) DO UPDATE SET
                            direction = EXCLUDED.direction,
                            confidence = EXCLUDED.confidence,
                            expected_change_percent = EXCLUDED.expected_change_percent,
                            risk_level = EXCLUDED.risk_level,
                            generated_at = EXCLUDED.generated_at
                        """,
                        prediction_params,
                    )

        connection.commit()
