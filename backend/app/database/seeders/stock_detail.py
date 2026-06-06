import csv
import json
from pathlib import Path


DEFAULT_SEED_FILE = Path(__file__).resolve().parents[1] / "seed_data" / "stock_detail.csv"


def _json_array(row: dict[str, str], column: str) -> list[object]:
    value = row.get(column, "").strip()
    if not value:
        return []
    return json.loads(value)


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
                        RETURNING id
                        """,
                        {
                            **prediction_params,
                            "stock_id": stock_id,
                            "forecast_run_id": forecast_run_id,
                        },
                    )
                    prediction_run_id = cursor.fetchone()[0]

                    for point in _json_array(row, "forecast_line_points"):
                        cursor.execute(
                            """
                            INSERT INTO forecast_line_points (
                                forecast_run_id,
                                sequence,
                                timestamp,
                                expected_value,
                                lower_bound,
                                upper_bound
                            ) VALUES (
                                %(forecast_run_id)s,
                                %(sequence)s,
                                %(timestamp)s,
                                %(expected_value)s,
                                %(lower_bound)s,
                                %(upper_bound)s
                            )
                            ON CONFLICT (forecast_run_id, sequence) DO UPDATE SET
                                timestamp = EXCLUDED.timestamp,
                                expected_value = EXCLUDED.expected_value,
                                lower_bound = EXCLUDED.lower_bound,
                                upper_bound = EXCLUDED.upper_bound
                            """,
                            {
                                "forecast_run_id": forecast_run_id,
                                "sequence": point["sequence"],
                                "timestamp": point["timestamp"],
                                "expected_value": point["expected_value"],
                                "lower_bound": point["lower_bound"],
                                "upper_bound": point["upper_bound"],
                            },
                        )

                    for candlestick in _json_array(row, "forecast_candlesticks"):
                        cursor.execute(
                            """
                            INSERT INTO forecast_candlesticks (
                                forecast_run_id,
                                sequence,
                                timestamp,
                                open_price,
                                high_price,
                                low_price,
                                close_price
                            ) VALUES (
                                %(forecast_run_id)s,
                                %(sequence)s,
                                %(timestamp)s,
                                %(open_price)s,
                                %(high_price)s,
                                %(low_price)s,
                                %(close_price)s
                            )
                            ON CONFLICT (forecast_run_id, sequence) DO UPDATE SET
                                timestamp = EXCLUDED.timestamp,
                                open_price = EXCLUDED.open_price,
                                high_price = EXCLUDED.high_price,
                                low_price = EXCLUDED.low_price,
                                close_price = EXCLUDED.close_price
                            """,
                            {
                                "forecast_run_id": forecast_run_id,
                                "sequence": candlestick["sequence"],
                                "timestamp": candlestick["timestamp"],
                                "open_price": candlestick["open"],
                                "high_price": candlestick["high"],
                                "low_price": candlestick["low"],
                                "close_price": candlestick["close"],
                            },
                        )

                    for sequence, factor in enumerate(
                        _json_array(row, "prediction_key_factors"), start=1
                    ):
                        cursor.execute(
                            """
                            INSERT INTO prediction_key_factors (
                                prediction_run_id,
                                sequence,
                                factor_type,
                                source_reference_type,
                                source_id,
                                label,
                                numeric_value,
                                rationale,
                                polarity,
                                weight
                            ) VALUES (
                                %(prediction_run_id)s,
                                %(sequence)s,
                                %(factor_type)s,
                                %(source_reference_type)s,
                                %(source_id)s,
                                %(label)s,
                                %(numeric_value)s,
                                %(rationale)s,
                                %(polarity)s,
                                %(weight)s
                            )
                            ON CONFLICT (prediction_run_id, sequence) DO UPDATE SET
                                factor_type = EXCLUDED.factor_type,
                                source_reference_type = EXCLUDED.source_reference_type,
                                source_id = EXCLUDED.source_id,
                                label = EXCLUDED.label,
                                numeric_value = EXCLUDED.numeric_value,
                                rationale = EXCLUDED.rationale,
                                polarity = EXCLUDED.polarity,
                                weight = EXCLUDED.weight
                            """,
                            {
                                "prediction_run_id": prediction_run_id,
                                "sequence": sequence,
                                "factor_type": factor["factor_type"],
                                "source_reference_type": factor["source_reference_type"],
                                "source_id": factor["source_id"],
                                "label": factor["label"],
                                "numeric_value": factor["value"],
                                "rationale": factor["rationale"],
                                "polarity": factor["polarity"],
                                "weight": factor["weight"],
                            },
                        )

        connection.commit()
