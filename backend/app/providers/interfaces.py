from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol


@dataclass(frozen=True)
class SupportedStock:
    ticker: str
    company_name: str
    exchange: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ticker", self.ticker.strip().upper())
        object.__setattr__(self, "company_name", self.company_name.strip())
        object.__setattr__(self, "exchange", self.exchange.strip())


@dataclass(frozen=True)
class PricePoint:
    timestamp: datetime
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: float
    volume: Optional[int]


@dataclass(frozen=True)
class MarketDataResult:
    stock: SupportedStock
    provider: str
    latest_price: float
    previous_close: Optional[float]
    market_status: Optional[str]
    observed_at: datetime
    historical_prices: list[PricePoint]


@dataclass(frozen=True)
class CompanyNewsItem:
    stock: SupportedStock
    provider: str
    title: str
    url: Optional[str]
    publisher: Optional[str]
    published_at: datetime
    provider_id: Optional[str]


@dataclass(frozen=True)
class StockSummaryInput:
    stock: SupportedStock
    market_data: Optional[MarketDataResult]
    news_items: list[CompanyNewsItem]


@dataclass(frozen=True)
class StockSummaryResult:
    stock: SupportedStock
    summary: str
    generated_at: datetime


class ProviderError(Exception):
    pass


class ProviderTransportError(ProviderError):
    pass


class ProviderMissingDataError(ProviderError):
    pass


class ProviderStaleDataError(ProviderError):
    pass


class ProviderMalformedDataError(ProviderError):
    pass


class ProviderUnsupportedStockError(ProviderError):
    pass


class MarketDataProvider(Protocol):
    def get_market_data(self, stock: SupportedStock) -> MarketDataResult:
        ...


class CompanyNewsProvider(Protocol):
    def get_company_news(self, stock: SupportedStock) -> list[CompanyNewsItem]:
        ...


class SummaryProvider(Protocol):
    def generate_summary(self, summary_input: StockSummaryInput) -> StockSummaryResult:
        ...
