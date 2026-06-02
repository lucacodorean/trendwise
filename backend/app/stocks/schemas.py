from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


DISCLAIMER = "Trendwise outputs are informational estimates only. They are not financial advice or trading recommendations."


class ForecastHorizon(str, Enum):
    thirty_minutes = "30m"
    one_day = "1d"
    five_days = "5d"
    seven_days = "7d"
    one_month = "1mo"
    six_months = "6mo"
    one_year = "1y"


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


class StockDetailPrediction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str
    direction: Optional[Literal["bullish", "bearish", "neutral"]]
    confidence: Optional[float]
    expected_change_percent: Optional[float] = Field(serialization_alias="expectedChangePercent")
    risk_level: Optional[Literal["low", "medium", "high"]] = Field(serialization_alias="riskLevel")
    generated_at: Optional[str] = Field(serialization_alias="generatedAt")
    freshness_label: str = Field(serialization_alias="freshnessLabel")


class StockDetailResponse(BaseModel):
    stock: StockDetailStock
    horizon: ForecastHorizon
    market: StockDetailMarket
    forecast: StockDetailForecast
    prediction: StockDetailPrediction
    disclaimer: str
