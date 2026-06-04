import csv
from pathlib import Path


DEFAULT_SEED_FILE = Path(__file__).resolve().parents[1] / "seed_data" / "stock_detail.csv"


class StockDetailSeeder:
    name = "stock_detail"

    def __init__(self, seed_file: Path = DEFAULT_SEED_FILE) -> None:
        self.seed_file = seed_file

    def run(self, connection: object) -> None:
        with connection.cursor() as cursor:
            with self.seed_file.open(newline="") as seed_data:
                for row in csv.DictReader(seed_data):
                    ticker = row["ticker"].strip().upper()
                    horizon = row["horizon"].strip()

                    cursor.execute(
                        "SELECT id FROM stocks WHERE ticker = %(ticker)s",
                        {"ticker": ticker},
                    )
                    stock_row = cursor.fetchone()
                    if stock_row is None:
                        continue
                    stock_id = stock_row[0]

                    market_params = {
                        "latest_price": float(row["latest_price"]),
                        "daily_change": float(row["daily_change"]),
                        "daily_change_percent": float(row["daily_change_percent"]),
                        "observed_at": row["observed_at"].strip(),
                    }
                    cursor.execute(
                        """
                        INSERT INTO market_snapshots (
                            stock_id,
                            provider,
                            latest_price,
                            daily_change,
                            daily_change_percent,
                            observed_at
                        ) VALUES (
                            %(stock_id)s,
                            %(provider)s,
                            %(latest_price)s,
                            %(daily_change)s,
                            %(daily_change_percent)s,
                            %(observed_at)s
                        )
                        ON CONFLICT (stock_id, provider, observed_at) DO UPDATE SET
                            latest_price = EXCLUDED.latest_price,
                            daily_change = EXCLUDED.daily_change,
                            daily_change_percent = EXCLUDED.daily_change_percent
                        RETURNING id
                        """,
                        {**market_params, "stock_id": stock_id, "provider": "seed"},
                    )
                    market_snapshot_id = cursor.fetchone()[0]

                    forecast_params = {
                        "horizon": horizon,
                        "status": row["forecast_status"].strip(),
                        "generated_at": row["forecast_generated_at"].strip(),
                    }
                    cursor.execute(
                        """
                        INSERT INTO forecast_runs (
                            stock_id,
                            horizon,
                            status,
                            generated_at
                        ) VALUES (
                            %(stock_id)s,
                            %(horizon)s,
                            %(status)s,
                            %(generated_at)s
                        )
                        ON CONFLICT (stock_id, horizon, generated_at) DO UPDATE SET
                            status = EXCLUDED.status
                        RETURNING id
                        """,
                        {**forecast_params, "stock_id": stock_id},
                    )
                    forecast_run_id = cursor.fetchone()[0]

                    cursor.execute(
                        """
                        INSERT INTO forecast_source_market_snapshots (
                            forecast_run_id,
                            market_snapshot_id
                        ) VALUES (
                            %(forecast_run_id)s,
                            %(market_snapshot_id)s
                        )
                        ON CONFLICT (forecast_run_id, market_snapshot_id) DO NOTHING
                        """,
                        {
                            "forecast_run_id": forecast_run_id,
                            "market_snapshot_id": market_snapshot_id,
                        },
                    )

                    prediction_params = {
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
                        INSERT INTO prediction_runs (
                            stock_id,
                            horizon,
                            forecast_run_id,
                            direction,
                            confidence,
                            expected_change_percent,
                            risk_level,
                            generated_at
                        ) VALUES (
                            %(stock_id)s,
                            %(horizon)s,
                            %(forecast_run_id)s,
                            %(direction)s,
                            %(confidence)s,
                            %(expected_change_percent)s,
                            %(risk_level)s,
                            %(generated_at)s
                        )
                        ON CONFLICT (stock_id, horizon, forecast_run_id, generated_at) DO UPDATE SET
                            direction = EXCLUDED.direction,
                            confidence = EXCLUDED.confidence,
                            expected_change_percent = EXCLUDED.expected_change_percent,
                            risk_level = EXCLUDED.risk_level
                        """,
                        {
                            **prediction_params,
                            "stock_id": stock_id,
                            "forecast_run_id": forecast_run_id,
                        },
                    )

        connection.commit()
