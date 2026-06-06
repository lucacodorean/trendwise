from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Literal, Optional


ForecastDirection = Literal["bullish", "bearish", "neutral"]
RiskLevel = Literal["low", "medium", "high"]
KeyFactorPolarity = Literal["positive", "negative", "neutral"]


class ForecastHorizon(str, Enum):
    thirty_minutes = "30m"
    one_day = "1d"
    five_days = "5d"
    seven_days = "7d"
    one_month = "1mo"
    six_months = "6mo"
    one_year = "1y"


@dataclass(frozen=True)
class StockIdentity:
    ticker: str
    company_name: str
    exchange: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ticker", self.ticker.strip().upper())
        object.__setattr__(self, "company_name", self.company_name.strip())
        object.__setattr__(self, "exchange", self.exchange.strip())


@dataclass(frozen=True)
class MarketSnapshotInput:
    latest_price: float
    daily_change: Optional[float]
    daily_change_percent: Optional[float]
    observed_at: datetime
    source_id: Optional[int] = None


@dataclass(frozen=True)
class HistoricalPricePoint:
    timestamp: datetime
    close: float


@dataclass(frozen=True)
class CompanyNewsSignal:
    source_id: Optional[int]
    title: str
    published_at: datetime


@dataclass(frozen=True)
class ExternalFactorSignal:
    source_id: Optional[int]
    factor_type: str
    label: str
    observed_at: datetime


@dataclass(frozen=True)
class ForecastInput:
    stock: StockIdentity
    horizon: ForecastHorizon
    market_snapshot: MarketSnapshotInput
    historical_prices: list[HistoricalPricePoint]
    company_news: list[CompanyNewsSignal]
    external_factors: list[ExternalFactorSignal]


@dataclass(frozen=True)
class ForecastLinePoint:
    sequence: int
    timestamp: datetime
    expected_value: float
    lower_bound: float
    upper_bound: float


@dataclass(frozen=True)
class ForecastCandlestick:
    sequence: int
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class ForecastPrediction:
    direction: ForecastDirection
    confidence: float
    expected_change_percent: float
    risk_level: RiskLevel


@dataclass(frozen=True)
class KeyFactorInput:
    factor_type: str
    source_reference_type: Optional[str]
    source_id: Optional[int]
    label: str
    value: Optional[float]
    rationale: Optional[str]
    polarity: KeyFactorPolarity
    weight: Optional[float]


@dataclass(frozen=True)
class ForecastGenerationResult:
    stock: StockIdentity
    horizon: ForecastHorizon
    generated_at: datetime
    line_points: list[ForecastLinePoint]
    candlesticks: list[ForecastCandlestick]
    prediction: ForecastPrediction
    key_factors: list[KeyFactorInput]
