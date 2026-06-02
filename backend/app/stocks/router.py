from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.stocks.repository import (
    StockDetailRepository,
    StockSearchRepository,
    get_stock_detail_repository,
    get_stock_search_repository,
)
from app.stocks.schemas import (
    DISCLAIMER,
    ForecastHorizon,
    StockDetailForecast,
    StockDetailMarket,
    StockDetailPrediction,
    StockDetailResponse,
    StockDetailStock,
    StockSearchResponse,
    StockSearchResult,
    format_utc_datetime,
)


router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/search", response_model=StockSearchResponse, operation_id="searchStocks")
def search_stocks(
    repository: Annotated[StockSearchRepository, Depends(get_stock_search_repository)],
    q: Annotated[str, Query()] = "",
) -> StockSearchResponse:
    rows = repository.examples() if q.strip() == "" else repository.search(q)
    return StockSearchResponse(
        results=[
            StockSearchResult(
                ticker=row["ticker"],
                company_name=row["company_name"],
                exchange=row["exchange"],
            )
            for row in rows
        ]
    )


@router.get(
    "/{ticker}/detail",
    response_model=StockDetailResponse,
    operation_id="getStockDetail",
)
def get_stock_detail(
    ticker: str,
    repository: Annotated[StockDetailRepository, Depends(get_stock_detail_repository)],
    horizon: Annotated[ForecastHorizon, Query()] = ForecastHorizon.one_day,
) -> StockDetailResponse:
    detail = repository.get_detail(ticker, horizon.value)
    if detail is None:
        raise HTTPException(status_code=404, detail="Supported Stock not found")

    market_row = detail["market"]
    if market_row is None:
        market = StockDetailMarket(
            status="unavailable",
            latest_price=None,
            daily_change=None,
            daily_change_percent=None,
            observed_at=None,
            freshness_label="Market data unavailable",
        )
    else:
        observed_at = format_utc_datetime(market_row["observed_at"])
        market = StockDetailMarket(
            status="available",
            latest_price=market_row["latest_price"],
            daily_change=market_row["daily_change"],
            daily_change_percent=market_row["daily_change_percent"],
            observed_at=observed_at,
            freshness_label=f"Market data fresh at {observed_at}",
        )

    forecast_row = detail["forecast"]
    if forecast_row is None:
        forecast = StockDetailForecast(
            status="unavailable",
            generated_at=None,
            freshness_label="Forecast unavailable",
        )
    else:
        forecast_generated_at = format_utc_datetime(forecast_row["generated_at"])
        forecast = StockDetailForecast(
            status=forecast_row["status"],
            generated_at=forecast_generated_at,
            freshness_label=f"Forecast checked at {forecast_generated_at}",
        )

    prediction_row = detail["prediction"]
    if prediction_row is None:
        prediction = StockDetailPrediction(
            status="unavailable",
            direction=None,
            confidence=None,
            expected_change_percent=None,
            risk_level=None,
            generated_at=None,
            freshness_label="Prediction unavailable",
        )
    else:
        prediction_generated_at = format_utc_datetime(prediction_row["generated_at"])
        prediction = StockDetailPrediction(
            status="available",
            direction=prediction_row["direction"],
            confidence=prediction_row["confidence"],
            expected_change_percent=prediction_row["expected_change_percent"],
            risk_level=prediction_row["risk_level"],
            generated_at=prediction_generated_at,
            freshness_label=f"Prediction fresh at {prediction_generated_at}",
        )

    return StockDetailResponse(
        stock=StockDetailStock(
            ticker=detail["stock"]["ticker"],
            company_name=detail["stock"]["company_name"],
            exchange=detail["stock"]["exchange"],
        ),
        horizon=horizon,
        market=market,
        forecast=forecast,
        prediction=prediction,
        disclaimer=DISCLAIMER,
    )
