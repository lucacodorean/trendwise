from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TypedDict

from app.forecasts.models import (
    ForecastCandlestick,
    ForecastLinePoint,
    ForecastPrediction,
    KeyFactorInput,
)


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
        try:
            with self.connection.cursor() as cursor:
                ids = self._insert_snapshot_forecast_prediction(
                    cursor,
                    ticker=ticker,
                    company_name=company_name,
                    exchange=exchange,
                    horizon=horizon,
                    latest_price=latest_price,
                    daily_change=daily_change,
                    daily_change_percent=daily_change_percent,
                    observed_at=observed_at,
                    forecast_status=forecast_status,
                    forecast_generated_at=forecast_generated_at,
                    prediction_direction=prediction_direction,
                    prediction_confidence=prediction_confidence,
                    prediction_expected_change_percent=prediction_expected_change_percent,
                    prediction_risk_level=prediction_risk_level,
                    prediction_generated_at=prediction_generated_at,
                )

            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

        return ids

    def store_detailed_forecast_prediction(
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
        line_points: list[ForecastLinePoint],
        candlesticks: list[ForecastCandlestick],
        prediction: ForecastPrediction,
        prediction_generated_at: datetime,
        key_factors: list[KeyFactorInput],
        company_news_ids: list[int],
        external_factor_ids: list[int],
    ) -> PersistenceIds:
        try:
            with self.connection.cursor() as cursor:
                ids = self._insert_snapshot_forecast_prediction(
                    cursor,
                    ticker=ticker,
                    company_name=company_name,
                    exchange=exchange,
                    horizon=horizon,
                    latest_price=latest_price,
                    daily_change=daily_change,
                    daily_change_percent=daily_change_percent,
                    observed_at=observed_at,
                    forecast_status=forecast_status,
                    forecast_generated_at=forecast_generated_at,
                    prediction_direction=prediction.direction,
                    prediction_confidence=prediction.confidence,
                    prediction_expected_change_percent=prediction.expected_change_percent,
                    prediction_risk_level=prediction.risk_level,
                    prediction_generated_at=prediction_generated_at,
                )
                forecast_run_id = ids["forecast_run_id"]
                prediction_run_id = ids["prediction_run_id"]

                for point in line_points:
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
                            "sequence": point.sequence,
                            "timestamp": point.timestamp,
                            "expected_value": point.expected_value,
                            "lower_bound": point.lower_bound,
                            "upper_bound": point.upper_bound,
                        },
                    )

                for candlestick in candlesticks:
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
                            "sequence": candlestick.sequence,
                            "timestamp": candlestick.timestamp,
                            "open_price": candlestick.open,
                            "high_price": candlestick.high,
                            "low_price": candlestick.low,
                            "close_price": candlestick.close,
                        },
                    )

                for company_news_id in company_news_ids:
                    cursor.execute(
                        """
                        INSERT INTO forecast_source_company_news (
                            forecast_run_id,
                            company_news_id
                        ) VALUES (
                            %(forecast_run_id)s,
                            %(company_news_id)s
                        )
                        ON CONFLICT (forecast_run_id, company_news_id) DO NOTHING
                        """,
                        {
                            "forecast_run_id": forecast_run_id,
                            "company_news_id": company_news_id,
                        },
                    )

                for external_factor_id in external_factor_ids:
                    cursor.execute(
                        """
                        INSERT INTO forecast_source_external_factors (
                            forecast_run_id,
                            external_factor_id
                        ) VALUES (
                            %(forecast_run_id)s,
                            %(external_factor_id)s
                        )
                        ON CONFLICT (forecast_run_id, external_factor_id) DO NOTHING
                        """,
                        {
                            "forecast_run_id": forecast_run_id,
                            "external_factor_id": external_factor_id,
                        },
                    )

                for sequence, key_factor in enumerate(key_factors, start=1):
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
                            "factor_type": key_factor.factor_type,
                            "source_reference_type": key_factor.source_reference_type,
                            "source_id": key_factor.source_id,
                            "label": key_factor.label,
                            "numeric_value": key_factor.value,
                            "rationale": key_factor.rationale,
                            "polarity": key_factor.polarity,
                            "weight": key_factor.weight,
                        },
                    )

            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

        return ids

    def _insert_snapshot_forecast_prediction(
        self,
        cursor: object,
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
