from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TypedDict


class PersistenceIds(TypedDict):
    stock_id: int
    market_snapshot_id: int
    forecast_run_id: int
    prediction_run_id: int


class PersistenceRoundTrip(TypedDict):
    stock_id: int
    ticker: str
    company_name: str
    exchange: str
    market_snapshot_id: int
    forecast_run_id: int
    horizon: str
    prediction_run_id: Optional[int]


@dataclass
class PostgresPersistenceRepository:
    connection: object

    def store_snapshot_forecast_prediction(
        self,
        *,
        ticker: str,
        company_name: str,
        exchange: str,
        horizon: str,
        latest_price: float,
        daily_change: float,
        daily_change_percent: float,
        observed_at: datetime,
        forecast_status: str,
        forecast_generated_at: datetime,
        prediction_direction: str,
        prediction_confidence: float,
        prediction_expected_change_percent: float,
        prediction_risk_level: str,
        prediction_generated_at: datetime,
    ) -> PersistenceIds:
        normalized_ticker = ticker.strip().upper()
        normalized_company_name = company_name.strip()
        normalized_exchange = exchange.strip()

        try:
            with self.connection.cursor() as cursor:
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
                    RETURNING id
                    """,
                    {
                        "ticker": normalized_ticker,
                        "company_name": normalized_company_name,
                        "exchange": normalized_exchange,
                        "instrument_type": "common_stock",
                        "region": "US",
                        "is_supported": True,
                        "search_text": f"{normalized_ticker} {normalized_company_name} {normalized_exchange}".lower(),
                    },
                )
                stock_id = cursor.fetchone()[0]

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
                    {
                        "stock_id": stock_id,
                        "provider": "application",
                        "latest_price": latest_price,
                        "daily_change": daily_change,
                        "daily_change_percent": daily_change_percent,
                        "observed_at": observed_at,
                    },
                )
                market_snapshot_id = cursor.fetchone()[0]

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
                    {
                        "stock_id": stock_id,
                        "horizon": horizon,
                        "status": forecast_status,
                        "generated_at": forecast_generated_at,
                    },
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
                        "stock_id": stock_id,
                        "horizon": horizon,
                        "forecast_run_id": forecast_run_id,
                        "direction": prediction_direction,
                        "confidence": prediction_confidence,
                        "expected_change_percent": prediction_expected_change_percent,
                        "risk_level": prediction_risk_level,
                        "generated_at": prediction_generated_at,
                    },
                )
                prediction_run_id = cursor.fetchone()[0]

            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

        return {
            "stock_id": stock_id,
            "market_snapshot_id": market_snapshot_id,
            "forecast_run_id": forecast_run_id,
            "prediction_run_id": prediction_run_id,
        }

    def get_snapshot_forecast_prediction(
        self, ticker: str, horizon: str
    ) -> Optional[PersistenceRoundTrip]:
        normalized_ticker = ticker.strip().upper()

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    s.id,
                    s.ticker,
                    s.company_name,
                    s.exchange,
                    ms.id,
                    fr.id,
                    fr.horizon,
                    pr.id
                FROM stocks s
                JOIN forecast_runs fr
                  ON fr.stock_id = s.id
                JOIN forecast_source_market_snapshots fsms
                  ON fsms.forecast_run_id = fr.id
                JOIN market_snapshots ms
                  ON ms.id = fsms.market_snapshot_id
                LEFT JOIN prediction_runs pr
                  ON pr.forecast_run_id = fr.id
                WHERE s.ticker = %(ticker)s
                  AND fr.horizon = %(horizon)s
                ORDER BY fr.generated_at DESC, fr.id DESC, pr.generated_at DESC, pr.id DESC
                LIMIT 1
                """,
                {"ticker": normalized_ticker, "horizon": horizon},
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return {
            "stock_id": row[0],
            "ticker": row[1],
            "company_name": row[2],
            "exchange": row[3],
            "market_snapshot_id": row[4],
            "forecast_run_id": row[5],
            "horizon": row[6],
            "prediction_run_id": row[7],
        }
