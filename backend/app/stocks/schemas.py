from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.forecasts.horizons import CalendarBasis, TimeBasis
from app.forecasts.models import ForecastHorizon


DISCLAIMER = "Trendwise outputs are informational estimates only. They are not financial advice or trading recommendations."


def format_utc_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class StockSearchResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ticker: str
    company_name: str = Field(serialization_alias="companyName")
    exchange: str


class StockSearchResponse(BaseModel):
    results: list[StockSearchResult]


class StockDetailStock(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ticker: str
    company_name: str = Field(serialization_alias="companyName")
    exchange: str


class StockDetailMarket(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    latest_price: Optional[float] = Field(serialization_alias="latestPrice")
    daily_change: Optional[float] = Field(serialization_alias="dailyChange")
    daily_change_percent: Optional[float] = Field(serialization_alias="dailyChangePercent")
    observed_at: Optional[str] = Field(serialization_alias="observedAt")
    freshness_label: str = Field(serialization_alias="freshnessLabel")


class StockDetailForecast(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    generated_at: Optional[str] = Field(serialization_alias="generatedAt")
    freshness_label: str = Field(serialization_alias="freshnessLabel")
    historical_points: list["StockDetailForecastHistoricalPoint"] = Field(
        default_factory=list,
        serialization_alias="historicalPoints",
    )
    line_points: list["StockDetailForecastLinePoint"] = Field(
        default_factory=list,
        serialization_alias="linePoints",
    )
    candlesticks: list["StockDetailForecastCandlestick"] = Field(default_factory=list)


class StockDetailForecastHistoricalPoint(BaseModel):
    sequence: int
    timestamp: str
    value: float


class StockDetailForecastLinePoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sequence: int
    timestamp: str
    expected_value: float = Field(serialization_alias="expectedValue")
    lower_bound: float = Field(serialization_alias="lowerBound")
    upper_bound: float = Field(serialization_alias="upperBound")


class StockDetailForecastCandlestick(BaseModel):
    sequence: int
    timestamp: str
    open: float
    high: float
    low: float
    close: float


class StockDetailPrediction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    direction: Optional[Literal["bullish", "bearish", "neutral"]]
    confidence: Optional[float]
    expected_change_percent: Optional[float] = Field(serialization_alias="expectedChangePercent")
    risk_level: Optional[Literal["low", "medium", "high"]] = Field(serialization_alias="riskLevel")
    generated_at: Optional[str] = Field(serialization_alias="generatedAt")
    freshness_label: str = Field(serialization_alias="freshnessLabel")
    key_factors: list["StockDetailKeyFactor"] = Field(
        default_factory=list,
        serialization_alias="keyFactors",
    )


class StockDetailKeyFactor(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    factor_type: str = Field(serialization_alias="factorType")
    source_reference_type: Optional[str] = Field(serialization_alias="sourceReferenceType")
    source_id: Optional[int] = Field(serialization_alias="sourceId")
    label: str
    value: Optional[float]
    rationale: Optional[str]
    polarity: Literal["positive", "negative", "neutral"]
    weight: Optional[float]


class StockDetailPricePointBasis(str, Enum):
    trading_session = "trading_session"


class StockDetailHorizonMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    value: ForecastHorizon
    label: str
    time_basis: TimeBasis = Field(serialization_alias="timeBasis")
    price_point_basis: StockDetailPricePointBasis = Field(serialization_alias="pricePointBasis")
    calendar_basis: CalendarBasis = Field(serialization_alias="calendarBasis")
    news_window_days: int = Field(serialization_alias="newsWindowDays")
    external_factor_weight_scale: float = Field(serialization_alias="externalFactorWeightScale")
    expected_forecast_point_count: int = Field(serialization_alias="expectedForecastPointCount")


class StockDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    stock: StockDetailStock
    horizon: ForecastHorizon
    horizon_metadata: StockDetailHorizonMetadata = Field(serialization_alias="horizonMetadata")
    market: StockDetailMarket
    forecast: StockDetailForecast
    prediction: StockDetailPrediction
    disclaimer: str
