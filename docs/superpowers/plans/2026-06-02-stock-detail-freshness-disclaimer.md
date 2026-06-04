# Stock Detail Freshness And Disclaimer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the issue 3 single-Stock Detail vertical slice with repository-backed seeded detail data, strict Forecast Horizon validation, freshness labels, no-advice disclaimer copy, and a Hero Summary mobile screen.

**Architecture:** Keep the backend change inside the existing `app.stocks` and `app.database.seeders` patterns. The backend exposes one combined `/stocks/{ticker}/detail` payload backed by scoped stock-detail seed tables. The mobile app consumes the generated OpenAPI client through a thin handwritten wrapper and replaces the current placeholder detail screen with a typed loading/error/render flow.

**Tech Stack:** FastAPI, Pydantic, psycopg, pytest, Expo React Native, TypeScript, openapi-typescript-codegen.

---

## File Structure

- Create: `backend/tests/stocks/test_stock_detail.py` for endpoint, validation, copy, and unavailable-state tests.
- Modify: `backend/tests/stocks/test_stock_search.py` only if shared test helpers need type tweaks; prefer no changes.
- Modify: `backend/app/stocks/schemas.py` to add Forecast Horizon, detail response, market, forecast, and prediction schemas.
- Modify: `backend/app/stocks/repository.py` to add the detail repository protocol and Postgres implementation while preserving search behavior.
- Modify: `backend/app/stocks/router.py` to add `GET /stocks/{ticker}/detail`.
- Create: `backend/app/database/seed_data/stock_detail.csv` for local fallback detail rows.
- Create: `backend/app/database/seeders/stock_detail.py` for scoped issue 3 tables and seed upserts.
- Modify: `backend/app/database/seeders/__init__.py` to run the new seeder after supported stocks.
- Modify: `backend/tests/database/test_seeders.py` to test the stock-detail seeder.
- Modify: `mobile/src/api/generated/openapi.json` and generated client/model files by running OpenAPI generation, not hand-editing generated TypeScript.
- Modify: `mobile/src/api/stocks.ts` to expose `getStockDetail` and generated detail types.
- Create: `mobile/src/screens/StockDetailScreen.tsx` for the Hero Summary UI.
- Modify: `mobile/App.tsx` to fetch and render detail data instead of the placeholder screen.
- Keep: `mobile/src/screens/StockDetailPlaceholderScreen.tsx` can remain unused for one commit, then delete if no imports remain.

## Task 1: Add Backend Detail Contract Tests

**Files:**

- Create: `backend/tests/stocks/test_stock_detail.py`
- Modify later: `backend/app/stocks/router.py`
- Modify later: `backend/app/stocks/schemas.py`
- Modify later: `backend/app/stocks/repository.py`

- [ ] **Step 1: Write failing endpoint tests**

Create `backend/tests/stocks/test_stock_detail.py`:

```python
from collections.abc import Iterator
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.stocks.repository import get_stock_detail_repository


class FakeStockDetailRepository:
    def get_detail(self, ticker: str, horizon: str):
        if ticker.upper() == "ZZZZ":
            return None
        if ticker.upper() == "MSFT":
            return {
                "stock": {
                    "ticker": "MSFT",
                    "company_name": "Microsoft Corporation",
                    "exchange": "NASDAQ",
                },
                "market": None,
                "forecast": None,
                "prediction": None,
            }
        return {
            "stock": {
                "ticker": "AAPL",
                "company_name": "Apple Inc.",
                "exchange": "NASDAQ",
            },
            "market": {
                "latest_price": 214.35,
                "daily_change": 2.62,
                "daily_change_percent": 1.24,
                "observed_at": datetime(2026, 6, 2, 13, 30, tzinfo=timezone.utc),
            },
            "forecast": {
                "status": "unavailable",
                "generated_at": datetime(2026, 6, 2, 13, 15, tzinfo=timezone.utc),
            },
            "prediction": {
                "direction": "bullish",
                "confidence": 0.68,
                "expected_change_percent": 0.8,
                "risk_level": "medium",
                "generated_at": datetime(2026, 6, 2, 13, 18, tzinfo=timezone.utc),
            },
        }


def override_detail_repository() -> Iterator[FakeStockDetailRepository]:
    yield FakeStockDetailRepository()


def client() -> TestClient:
    app.dependency_overrides[get_stock_detail_repository] = override_detail_repository
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_stock_detail_returns_seeded_supported_stock_for_default_horizon() -> None:
    response = client().get("/stocks/AAPL/detail")

    assert response.status_code == 200
    assert response.json() == {
        "stock": {
            "ticker": "AAPL",
            "companyName": "Apple Inc.",
            "exchange": "NASDAQ",
        },
        "horizon": "1d",
        "market": {
            "status": "available",
            "latestPrice": 214.35,
            "dailyChange": 2.62,
            "dailyChangePercent": 1.24,
            "observedAt": "2026-06-02T13:30:00Z",
            "freshnessLabel": "Market data fresh at 2026-06-02T13:30:00Z",
        },
        "forecast": {
            "status": "unavailable",
            "generatedAt": "2026-06-02T13:15:00Z",
            "freshnessLabel": "Forecast checked at 2026-06-02T13:15:00Z",
        },
        "prediction": {
            "status": "available",
            "direction": "bullish",
            "confidence": 0.68,
            "expectedChangePercent": 0.8,
            "riskLevel": "medium",
            "generatedAt": "2026-06-02T13:18:00Z",
            "freshnessLabel": "Prediction fresh at 2026-06-02T13:18:00Z",
        },
        "disclaimer": "Trendwise outputs are informational estimates only. They are not financial advice or trading recommendations.",
    }


def test_stock_detail_accepts_explicit_valid_horizon() -> None:
    response = client().get("/stocks/AAPL/detail", params={"horizon": "5d"})

    assert response.status_code == 200
    assert response.json()["horizon"] == "5d"


def test_stock_detail_rejects_invalid_horizon_before_repository_lookup() -> None:
    response = client().get("/stocks/AAPL/detail", params={"horizon": "2d"})

    assert response.status_code == 422


def test_stock_detail_returns_404_for_unsupported_ticker() -> None:
    response = client().get("/stocks/ZZZZ/detail")

    assert response.status_code == 404
    assert response.json() == {"detail": "Supported Stock not found"}


def test_stock_detail_returns_unavailable_sections_for_missing_detail_rows() -> None:
    response = client().get("/stocks/MSFT/detail")

    assert response.status_code == 200
    body = response.json()
    assert body["market"] == {
        "status": "unavailable",
        "latestPrice": None,
        "dailyChange": None,
        "dailyChangePercent": None,
        "observedAt": None,
        "freshnessLabel": "Market data unavailable",
    }
    assert body["forecast"]["status"] == "unavailable"
    assert body["prediction"]["status"] == "unavailable"


def test_stock_detail_copy_does_not_use_recommendation_language() -> None:
    response = client().get("/stocks/AAPL/detail")

    serialized = str(response.json()).lower()

    assert "buy" not in serialized
    assert "sell" not in serialized
    assert "hold" not in serialized
    assert "bullish" in serialized
```

- [ ] **Step 2: Run tests to verify they fail for missing dependency**

Run: `cd backend && pytest tests/stocks/test_stock_detail.py -v`

Expected: FAIL with an import error mentioning `get_stock_detail_repository` or route/schema names not existing.

- [ ] **Step 3: Commit failing tests**

```bash
git add backend/tests/stocks/test_stock_detail.py
git commit -m "test: specify stock detail endpoint"
```

## Task 2: Implement Backend Detail Schemas And Route

**Files:**

- Modify: `backend/app/stocks/schemas.py`
- Modify: `backend/app/stocks/repository.py`
- Modify: `backend/app/stocks/router.py`
- Test: `backend/tests/stocks/test_stock_detail.py`

- [ ] **Step 1: Add schemas and enum**

Append these definitions to `backend/app/stocks/schemas.py` after the existing search schemas:

```python
from datetime import datetime, timezone
from enum import Enum
from typing import Literal


class ForecastHorizon(str, Enum):
    THIRTY_MINUTES = "30m"
    ONE_DAY = "1d"
    FIVE_DAYS = "5d"
    SEVEN_DAYS = "7d"
    ONE_MONTH = "1mo"
    SIX_MONTHS = "6mo"
    ONE_YEAR = "1y"


class StockIdentity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ticker: str
    company_name: str = Field(serialization_alias="companyName")
    exchange: str


class StockMarketDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: Literal["available", "unavailable"]
    latest_price: float | None = Field(serialization_alias="latestPrice")
    daily_change: float | None = Field(serialization_alias="dailyChange")
    daily_change_percent: float | None = Field(serialization_alias="dailyChangePercent")
    observed_at: datetime | None = Field(serialization_alias="observedAt")
    freshness_label: str = Field(serialization_alias="freshnessLabel")


class StockForecastDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: Literal["unavailable"]
    generated_at: datetime | None = Field(serialization_alias="generatedAt")
    freshness_label: str = Field(serialization_alias="freshnessLabel")


class StockPredictionDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: Literal["available", "unavailable"]
    direction: Literal["bullish", "bearish", "neutral"] | None
    confidence: float | None
    expected_change_percent: float | None = Field(serialization_alias="expectedChangePercent")
    risk_level: Literal["low", "medium", "high"] | None = Field(serialization_alias="riskLevel")
    generated_at: datetime | None = Field(serialization_alias="generatedAt")
    freshness_label: str = Field(serialization_alias="freshnessLabel")


class StockDetailResponse(BaseModel):
    stock: StockIdentity
    horizon: ForecastHorizon
    market: StockMarketDetail
    forecast: StockForecastDetail
    prediction: StockPredictionDetail
    disclaimer: str


DISCLAIMER = (
    "Trendwise outputs are informational estimates only. "
    "They are not financial advice or trading recommendations."
)


def iso_freshness_timestamp(value: datetime) -> str:
    normalized = value.astimezone(timezone.utc).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")
```

Also move the new imports to the top of the file so there are no duplicate import blocks. The final import section should be:

```python
from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
```

- [ ] **Step 2: Add repository protocol stub and dependency**

Modify `backend/app/stocks/repository.py` to add typed detail rows and dependency. Add these imports near the top:

```python
from datetime import datetime
```

Add these types below `StockRow`:

```python
class MarketDetailRow(TypedDict):
    latest_price: float
    daily_change: float
    daily_change_percent: float
    observed_at: datetime


class ForecastDetailRow(TypedDict):
    status: str
    generated_at: datetime


class PredictionDetailRow(TypedDict):
    direction: str
    confidence: float
    expected_change_percent: float
    risk_level: str
    generated_at: datetime


class StockDetailRow(TypedDict):
    stock: StockRow
    market: MarketDetailRow | None
    forecast: ForecastDetailRow | None
    prediction: PredictionDetailRow | None
```

Add this protocol below `StockSearchRepository`:

```python
class StockDetailRepository(Protocol):
    def get_detail(self, ticker: str, horizon: str) -> StockDetailRow | None: ...
```

Add this implementation below `PostgresStockSearchRepository`:

```python
@dataclass
class PostgresStockDetailRepository:
    connection: object

    def get_detail(self, ticker: str, horizon: str) -> StockDetailRow | None:
        normalized_ticker = ticker.strip().upper()
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT ticker, company_name, exchange
                FROM supported_stocks
                WHERE ticker = %(ticker)s
                  AND is_supported = TRUE
                """,
                {"ticker": normalized_ticker},
            )
            stock_row = cursor.fetchone()
            if stock_row is None:
                return None

            cursor.execute(
                """
                SELECT latest_price, daily_change, daily_change_percent, observed_at
                FROM stock_market_details
                WHERE ticker = %(ticker)s
                """,
                {"ticker": normalized_ticker},
            )
            market_row = cursor.fetchone()

            cursor.execute(
                """
                SELECT status, generated_at
                FROM stock_forecast_details
                WHERE ticker = %(ticker)s
                  AND horizon = %(horizon)s
                """,
                {"ticker": normalized_ticker, "horizon": horizon},
            )
            forecast_row = cursor.fetchone()

            cursor.execute(
                """
                SELECT direction, confidence, expected_change_percent, risk_level, generated_at
                FROM stock_prediction_details
                WHERE ticker = %(ticker)s
                  AND horizon = %(horizon)s
                """,
                {"ticker": normalized_ticker, "horizon": horizon},
            )
            prediction_row = cursor.fetchone()

        return {
            "stock": {
                "ticker": stock_row[0],
                "company_name": stock_row[1],
                "exchange": stock_row[2],
            },
            "market": None
            if market_row is None
            else {
                "latest_price": float(market_row[0]),
                "daily_change": float(market_row[1]),
                "daily_change_percent": float(market_row[2]),
                "observed_at": market_row[3],
            },
            "forecast": None
            if forecast_row is None
            else {"status": forecast_row[0], "generated_at": forecast_row[1]},
            "prediction": None
            if prediction_row is None
            else {
                "direction": prediction_row[0],
                "confidence": float(prediction_row[1]),
                "expected_change_percent": float(prediction_row[2]),
                "risk_level": prediction_row[3],
                "generated_at": prediction_row[4],
            },
        }
```

Add this dependency at the bottom:

```python
def get_stock_detail_repository() -> Iterator[StockDetailRepository]:
    with open_database_connection() as connection:
        yield PostgresStockDetailRepository(connection)
```

- [ ] **Step 3: Add route and response builder**

Modify `backend/app/stocks/router.py` imports to include `HTTPException` and detail schemas:

```python
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
    StockDetailResponse,
    StockForecastDetail,
    StockIdentity,
    StockMarketDetail,
    StockPredictionDetail,
    StockSearchResponse,
    StockSearchResult,
    iso_freshness_timestamp,
)
```

Append this route after `search_stocks`:

```python
@router.get("/{ticker}/detail", response_model=StockDetailResponse, operation_id="getStockDetail")
def get_stock_detail(
    ticker: str,
    repository: Annotated[StockDetailRepository, Depends(get_stock_detail_repository)],
    horizon: Annotated[ForecastHorizon, Query()] = ForecastHorizon.ONE_DAY,
) -> StockDetailResponse:
    detail = repository.get_detail(ticker, horizon.value)
    if detail is None:
        raise HTTPException(status_code=404, detail="Supported Stock not found")

    market = detail["market"]
    forecast = detail["forecast"]
    prediction = detail["prediction"]

    return StockDetailResponse(
        stock=StockIdentity(
            ticker=detail["stock"]["ticker"],
            company_name=detail["stock"]["company_name"],
            exchange=detail["stock"]["exchange"],
        ),
        horizon=horizon,
        market=StockMarketDetail(
            status="unavailable" if market is None else "available",
            latest_price=None if market is None else market["latest_price"],
            daily_change=None if market is None else market["daily_change"],
            daily_change_percent=None if market is None else market["daily_change_percent"],
            observed_at=None if market is None else market["observed_at"],
            freshness_label="Market data unavailable"
            if market is None
            else f"Market data fresh at {iso_freshness_timestamp(market['observed_at'])}",
        ),
        forecast=StockForecastDetail(
            status="unavailable",
            generated_at=None if forecast is None else forecast["generated_at"],
            freshness_label="Forecast unavailable"
            if forecast is None
            else f"Forecast checked at {iso_freshness_timestamp(forecast['generated_at'])}",
        ),
        prediction=StockPredictionDetail(
            status="unavailable" if prediction is None else "available",
            direction=None if prediction is None else prediction["direction"],
            confidence=None if prediction is None else prediction["confidence"],
            expected_change_percent=None
            if prediction is None
            else prediction["expected_change_percent"],
            risk_level=None if prediction is None else prediction["risk_level"],
            generated_at=None if prediction is None else prediction["generated_at"],
            freshness_label="Prediction unavailable"
            if prediction is None
            else f"Prediction fresh at {iso_freshness_timestamp(prediction['generated_at'])}",
        ),
        disclaimer=DISCLAIMER,
    )
```

- [ ] **Step 4: Run endpoint tests**

Run: `cd backend && pytest tests/stocks/test_stock_detail.py -v`

Expected: PASS.

- [ ] **Step 5: Run existing stock search tests**

Run: `cd backend && pytest tests/stocks/test_stock_search.py -v`

Expected: PASS.

- [ ] **Step 6: Commit backend route and schema**

```bash
git add backend/app/stocks/schemas.py backend/app/stocks/repository.py backend/app/stocks/router.py backend/tests/stocks/test_stock_detail.py
git commit -m "feat: add stock detail endpoint"
```

## Task 3: Add Stock Detail Seeder And Repository Tests

**Files:**

- Create: `backend/app/database/seed_data/stock_detail.csv`
- Create: `backend/app/database/seeders/stock_detail.py`
- Modify: `backend/app/database/seeders/__init__.py`
- Modify: `backend/tests/database/test_seeders.py`
- Test: `backend/tests/database/test_seeders.py`

- [ ] **Step 1: Add failing seeder test**

Append to `backend/tests/database/test_seeders.py`:

```python
from app.database.seeders.stock_detail import StockDetailSeeder


def test_stock_detail_seeder_creates_detail_tables_and_upserts_rows(tmp_path: Path) -> None:
    seed_file = tmp_path / "stock_detail.csv"
    seed_file.write_text(
        "ticker,horizon,latest_price,daily_change,daily_change_percent,observed_at,forecast_status,forecast_generated_at,prediction_direction,prediction_confidence,prediction_expected_change_percent,prediction_risk_level,prediction_generated_at\n"
        "AAPL,1d,214.35,2.62,1.24,2026-06-02T13:30:00Z,unavailable,2026-06-02T13:15:00Z,bullish,0.68,0.8,medium,2026-06-02T13:18:00Z\n"
    )
    connection = RecordingConnection()

    StockDetailSeeder(seed_file=seed_file).run(connection)

    executions = connection.cursor_instance.executions
    assert "CREATE TABLE IF NOT EXISTS stock_market_details" in executions[0][0]
    assert "CREATE TABLE IF NOT EXISTS stock_forecast_details" in executions[1][0]
    assert "CREATE TABLE IF NOT EXISTS stock_prediction_details" in executions[2][0]
    market_params = [params for sql, params in executions if "INSERT INTO stock_market_details" in sql]
    forecast_params = [params for sql, params in executions if "INSERT INTO stock_forecast_details" in sql]
    prediction_params = [params for sql, params in executions if "INSERT INTO stock_prediction_details" in sql]
    assert market_params == [
        {
            "ticker": "AAPL",
            "latest_price": 214.35,
            "daily_change": 2.62,
            "daily_change_percent": 1.24,
            "observed_at": "2026-06-02T13:30:00Z",
        }
    ]
    assert forecast_params == [
        {
            "ticker": "AAPL",
            "horizon": "1d",
            "status": "unavailable",
            "generated_at": "2026-06-02T13:15:00Z",
        }
    ]
    assert prediction_params == [
        {
            "ticker": "AAPL",
            "horizon": "1d",
            "direction": "bullish",
            "confidence": 0.68,
            "expected_change_percent": 0.8,
            "risk_level": "medium",
            "generated_at": "2026-06-02T13:18:00Z",
        }
    ]
    assert connection.commits == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/database/test_seeders.py::test_stock_detail_seeder_creates_detail_tables_and_upserts_rows -v`

Expected: FAIL with `ModuleNotFoundError` for `app.database.seeders.stock_detail`.

- [ ] **Step 3: Add seed data file**

Create `backend/app/database/seed_data/stock_detail.csv`:

```csv
ticker,horizon,latest_price,daily_change,daily_change_percent,observed_at,forecast_status,forecast_generated_at,prediction_direction,prediction_confidence,prediction_expected_change_percent,prediction_risk_level,prediction_generated_at
AAPL,1d,214.35,2.62,1.24,2026-06-02T13:30:00Z,unavailable,2026-06-02T13:15:00Z,bullish,0.68,0.8,medium,2026-06-02T13:18:00Z
MSFT,1d,423.85,-1.12,-0.26,2026-06-02T13:30:00Z,unavailable,2026-06-02T13:15:00Z,neutral,0.55,0.1,low,2026-06-02T13:18:00Z
NVDA,1d,118.74,3.18,2.75,2026-06-02T13:30:00Z,unavailable,2026-06-02T13:15:00Z,bullish,0.72,1.4,high,2026-06-02T13:18:00Z
TSLA,1d,182.63,-4.91,-2.62,2026-06-02T13:30:00Z,unavailable,2026-06-02T13:15:00Z,bearish,0.64,-1.1,high,2026-06-02T13:18:00Z
```

- [ ] **Step 4: Implement stock detail seeder**

Create `backend/app/database/seeders/stock_detail.py`:

```python
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
                        {
                            "ticker": ticker,
                            "latest_price": float(row["latest_price"]),
                            "daily_change": float(row["daily_change"]),
                            "daily_change_percent": float(row["daily_change_percent"]),
                            "observed_at": row["observed_at"].strip(),
                        },
                    )
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
                        {
                            "ticker": ticker,
                            "horizon": horizon,
                            "status": row["forecast_status"].strip(),
                            "generated_at": row["forecast_generated_at"].strip(),
                        },
                    )
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
                        {
                            "ticker": ticker,
                            "horizon": horizon,
                            "direction": row["prediction_direction"].strip(),
                            "confidence": float(row["prediction_confidence"]),
                            "expected_change_percent": float(row["prediction_expected_change_percent"]),
                            "risk_level": row["prediction_risk_level"].strip(),
                            "generated_at": row["prediction_generated_at"].strip(),
                        },
                    )

        connection.commit()
```

- [ ] **Step 5: Register seeder**

Modify `backend/app/database/seeders/__init__.py`:

```python
from app.database.seeders.stock_detail import StockDetailSeeder
from app.database.seeders.supported_stocks import SupportedStocksSeeder

SEEDERS = [SupportedStocksSeeder(), StockDetailSeeder()]
```

- [ ] **Step 6: Run seeder tests**

Run: `cd backend && pytest tests/database/test_seeders.py -v`

Expected: PASS.

- [ ] **Step 7: Run backend stock tests**

Run: `cd backend && pytest tests/stocks -v`

Expected: PASS.

- [ ] **Step 8: Commit seeder changes**

```bash
git add backend/app/database/seed_data/stock_detail.csv backend/app/database/seeders/stock_detail.py backend/app/database/seeders/__init__.py backend/tests/database/test_seeders.py
git commit -m "feat: seed stock detail data"
```

## Task 4: Regenerate OpenAPI And Mobile Client

**Files:**

- Modify: `mobile/src/api/generated/openapi.json`
- Modify: `mobile/src/api/generated/services/StocksService.ts`
- Create: generated model files under `mobile/src/api/generated/models/`
- Modify: `mobile/src/api/generated/index.ts`

- [ ] **Step 1: Generate OpenAPI JSON**

Run: `cd backend && python -m app.openapi ../mobile/src/api/generated/openapi.json`

Expected: command exits 0 and `mobile/src/api/generated/openapi.json` contains `/stocks/{ticker}/detail`.

- [ ] **Step 2: Regenerate TypeScript client**

Run: `cd mobile && npm run generate:api`

Expected: command exits 0 and `mobile/src/api/generated/services/StocksService.ts` includes `getStockDetail`.

- [ ] **Step 3: Inspect generated files**

Run: `git diff -- mobile/src/api/generated`

Expected: generated schemas include `StockDetailResponse`, `StockMarketDetail`, `StockForecastDetail`, `StockPredictionDetail`, and `ForecastHorizon` or equivalent enum schema.

- [ ] **Step 4: Commit generated API client**

```bash
git add mobile/src/api/generated
git commit -m "chore: regenerate stock detail api client"
```

## Task 5: Add Mobile Detail API Wrapper

**Files:**

- Modify: `mobile/src/api/stocks.ts`
- Test/check: `mobile/src/api/stocks.ts`

- [ ] **Step 1: Add generated detail types and wrapper**

Modify `mobile/src/api/stocks.ts` imports:

```ts
import {
  OpenAPI,
  StocksService,
  type StockDetailResponse,
  type StockSearchResult,
} from "./generated";
```

Add exports after `export type PrimaryStock = StockSearchResult;`:

```ts
export type StockDetail = StockDetailResponse;
export type ForecastHorizon = NonNullable<Parameters<typeof StocksService.getStockDetail>[0]["horizon"]>;
```

Add this function after `searchStocks`:

```ts
export async function getStockDetail(
  ticker: string,
  horizon: ForecastHorizon = "1d",
): Promise<StockDetail> {
  return StocksService.getStockDetail({ ticker, horizon });
}
```

- [ ] **Step 2: Run TypeScript check to verify generated names**

Run: `cd mobile && npm run typecheck`

Expected: PASS. If it fails because the generated method parameter type differs, use the generated `StocksService.getStockDetail` signature exactly and keep the public wrapper signature as `getStockDetail(ticker: string, horizon = "1d")`.

- [ ] **Step 3: Commit API wrapper**

```bash
git add mobile/src/api/stocks.ts
git commit -m "feat: add mobile stock detail api wrapper"
```

## Task 6: Build Hero Summary Stock Detail Screen

**Files:**

- Create: `mobile/src/screens/StockDetailScreen.tsx`
- Modify later: `mobile/App.tsx`
- Delete later: `mobile/src/screens/StockDetailPlaceholderScreen.tsx` if unused

- [ ] **Step 1: Create the screen component**

Create `mobile/src/screens/StockDetailScreen.tsx`:

```tsx
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";

import type { StockDetail } from "../api/stocks";

type StockDetailScreenProps = {
  detail: StockDetail;
  detailError: string | null;
  onChangeStock: () => void;
};

function formatPrice(value: number | null | undefined): string {
  if (typeof value !== "number") {
    return "Unavailable";
  }
  return `$${value.toFixed(2)}`;
}

function formatSignedPercent(value: number | null | undefined): string {
  if (typeof value !== "number") {
    return "Change unavailable";
  }
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}% today`;
}

function formatExpectedChange(value: number | null | undefined): string {
  if (typeof value !== "number") {
    return "Expected change unavailable";
  }
  const sign = value > 0 ? "+" : "";
  return `Expected change ${sign}${value.toFixed(2)}%`;
}

function formatConfidence(value: number | null | undefined): string {
  if (typeof value !== "number") {
    return "Confidence unavailable";
  }
  return `${Math.round(value * 100)}% confidence`;
}

function titleCase(value: string | null | undefined): string {
  if (!value) {
    return "Unavailable";
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function StockDetailScreen({
  detail,
  detailError,
  onChangeStock,
}: StockDetailScreenProps) {
  const isPositiveChange = (detail.market.dailyChangePercent ?? 0) >= 0;

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.hero}>
          <View style={styles.heroTopRow}>
            <Text style={styles.exchange}>{detail.stock.exchange}</Text>
            <Pressable
              accessibilityLabel="Change selected Stock"
              accessibilityRole="button"
              onPress={onChangeStock}
              style={styles.changeButton}
            >
              <Text style={styles.changeButtonText}>Change</Text>
            </Pressable>
          </View>

          <Text style={styles.ticker}>{detail.stock.ticker}</Text>
          <Text style={styles.company}>{detail.stock.companyName}</Text>

          <View style={styles.priceRow}>
            <View>
              <Text style={styles.price}>{formatPrice(detail.market.latestPrice)}</Text>
              <Text style={isPositiveChange ? styles.positiveChange : styles.negativeChange}>
                {formatSignedPercent(detail.market.dailyChangePercent)}
              </Text>
            </View>
            <Text style={styles.marketFreshness}>{detail.market.freshnessLabel}</Text>
          </View>
        </View>

        {detailError ? <Text style={styles.error}>{detailError}</Text> : null}

        <View style={styles.metricGrid}>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Direction</Text>
            <Text style={styles.metricValue}>{titleCase(detail.prediction.direction)}</Text>
          </View>
          <View style={styles.metricCardWarm}>
            <Text style={styles.metricLabelWarm}>Risk Level</Text>
            <Text style={styles.metricValue}>{titleCase(detail.prediction.riskLevel)}</Text>
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardKicker}>Prediction · {detail.horizon}</Text>
          <Text style={styles.cardTitle}>{formatConfidence(detail.prediction.confidence)}</Text>
          <Text style={styles.cardBody}>{formatExpectedChange(detail.prediction.expectedChangePercent)}</Text>
          <Text style={styles.freshness}>{detail.prediction.freshnessLabel}</Text>
        </View>

        <View style={styles.disclaimer}>
          <Text style={styles.disclaimerText}>{detail.disclaimer}</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardKicker}>Forecast</Text>
          <Text style={styles.cardTitle}>Forecast graph unavailable</Text>
          <Text style={styles.cardBody}>
            The forecast graph will appear when graph rendering is added.
          </Text>
          <Text style={styles.freshness}>{detail.forecast.freshnessLabel}</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: "#f8fafc",
    flex: 1,
  },
  content: {
    padding: 24,
    paddingBottom: 40,
  },
  hero: {
    backgroundColor: "#0f172a",
    borderRadius: 28,
    padding: 22,
  },
  heroTopRow: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  exchange: {
    color: "#bfdbfe",
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1.2,
  },
  changeButton: {
    backgroundColor: "#60a5fa",
    borderRadius: 999,
    paddingHorizontal: 14,
    paddingVertical: 9,
  },
  changeButtonText: {
    color: "#0f172a",
    fontWeight: "900",
  },
  ticker: {
    color: "#ffffff",
    fontSize: 44,
    fontWeight: "900",
    marginTop: 18,
  },
  company: {
    color: "#dbeafe",
    fontSize: 17,
    fontWeight: "700",
    marginTop: 4,
  },
  priceRow: {
    alignItems: "flex-end",
    flexDirection: "row",
    justifyContent: "space-between",
    marginTop: 24,
  },
  price: {
    color: "#ffffff",
    fontSize: 34,
    fontWeight: "900",
  },
  positiveChange: {
    color: "#86efac",
    fontSize: 16,
    fontWeight: "800",
    marginTop: 4,
  },
  negativeChange: {
    color: "#fecaca",
    fontSize: 16,
    fontWeight: "800",
    marginTop: 4,
  },
  marketFreshness: {
    color: "#bfdbfe",
    flexShrink: 1,
    fontSize: 12,
    lineHeight: 17,
    marginLeft: 16,
    textAlign: "right",
  },
  error: {
    color: "#b91c1c",
    marginTop: 16,
  },
  metricGrid: {
    flexDirection: "row",
    gap: 12,
    marginTop: 16,
  },
  metricCard: {
    backgroundColor: "#ecfeff",
    borderRadius: 18,
    flex: 1,
    padding: 16,
  },
  metricCardWarm: {
    backgroundColor: "#fef3c7",
    borderRadius: 18,
    flex: 1,
    padding: 16,
  },
  metricLabel: {
    color: "#0e7490",
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  metricLabelWarm: {
    color: "#92400e",
    fontSize: 11,
    fontWeight: "900",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  metricValue: {
    color: "#0f172a",
    fontSize: 20,
    fontWeight: "900",
    marginTop: 8,
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 22,
    marginTop: 16,
    padding: 18,
  },
  cardKicker: {
    color: "#2563eb",
    fontSize: 12,
    fontWeight: "900",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  cardTitle: {
    color: "#0f172a",
    fontSize: 21,
    fontWeight: "900",
    marginTop: 10,
  },
  cardBody: {
    color: "#334155",
    fontSize: 15,
    lineHeight: 22,
    marginTop: 8,
  },
  freshness: {
    color: "#64748b",
    fontSize: 12,
    marginTop: 12,
  },
  disclaimer: {
    backgroundColor: "#e0f2fe",
    borderRadius: 18,
    marginTop: 16,
    padding: 14,
  },
  disclaimerText: {
    color: "#0c4a6e",
    fontSize: 13,
    lineHeight: 19,
  },
});
```

- [ ] **Step 2: Run TypeScript check and expect unused screen is acceptable**

Run: `cd mobile && npm run typecheck`

Expected: PASS if the new `StockDetail` type properties match generated aliases. If property names differ, inspect the generated `StockDetailResponse.ts` model and update this screen to use those exact generated property names.

- [ ] **Step 3: Commit screen component**

```bash
git add mobile/src/screens/StockDetailScreen.tsx
git commit -m "feat: add stock detail hero screen"
```

## Task 7: Wire Mobile App Detail Fetching

**Files:**

- Modify: `mobile/App.tsx`
- Delete: `mobile/src/screens/StockDetailPlaceholderScreen.tsx` if unused
- Test/check: `mobile/App.tsx`

- [ ] **Step 1: Replace placeholder imports and state**

Modify imports in `mobile/App.tsx`:

```tsx
import { useEffect, useState } from "react";
import { ActivityIndicator, SafeAreaView, StyleSheet, Text } from "react-native";
import { StatusBar } from "expo-status-bar";

import { getStockDetail, type PrimaryStock, type StockDetail } from "./src/api/stocks";
import { StockDetailScreen } from "./src/screens/StockDetailScreen";
import { StockSearchScreen } from "./src/screens/StockSearchScreen";
```

Replace the `AppState` type:

```tsx
type AppState =
  | { status: "loading" }
  | { status: "search" }
  | { status: "detail-loading"; stock: PrimaryStock }
  | { status: "detail"; stock: PrimaryStock; detail: StockDetail };
```

- [ ] **Step 2: Add detail loading helper**

Inside `App`, before `useEffect`, add:

```tsx
  async function loadDetailForStock(stock: PrimaryStock) {
    setAppState({ status: "detail-loading", stock });
    try {
      const detail = await getStockDetail(stock.ticker, "1d");
      setDetailError(null);
      setAppState({ status: "detail", stock, detail });
    } catch {
      setDetailError("Stock detail is unavailable. Check the backend and try again.");
      setAppState({ status: "detail-loading", stock });
    }
  }
```

- [ ] **Step 3: Use helper during hydration and selection**

Replace the successful cached stock branch inside `hydratePrimaryStock`:

```tsx
          if (cachedStock) {
            setAppState({ status: "detail-loading", stock: cachedStock });
            loadDetailForStock(cachedStock);
          } else {
            setAppState({ status: "search" });
          }
```

Replace `handleSelectStock` success body:

```tsx
      setSelectionError(null);
      setDetailError(null);
      loadDetailForStock(stock);
```

- [ ] **Step 4: Render detail loading and detail screen**

Replace the placeholder render block:

```tsx
      {appState.status === "detail-loading" ? (
        <SafeAreaView style={styles.loadingScreen}>
          <ActivityIndicator color="#60a5fa" />
          {detailError ? <Text style={styles.loadingError}>{detailError}</Text> : null}
        </SafeAreaView>
      ) : null}
      {appState.status === "detail" ? (
        <StockDetailScreen
          detail={appState.detail}
          detailError={detailError}
          onChangeStock={handleChangeStock}
        />
      ) : null}
```

Add this style:

```tsx
  loadingError: {
    color: "#fecaca",
    lineHeight: 22,
    marginTop: 16,
    paddingHorizontal: 24,
    textAlign: "center",
  },
```

- [ ] **Step 5: Delete unused placeholder screen**

Run: `git rm mobile/src/screens/StockDetailPlaceholderScreen.tsx`

Expected: file is removed and no imports reference it.

- [ ] **Step 6: Run TypeScript check**

Run: `cd mobile && npm run typecheck`

Expected: PASS.

- [ ] **Step 7: Commit mobile wiring**

```bash
git add mobile/App.tsx mobile/src/screens/StockDetailScreen.tsx
git add -u mobile/src/screens/StockDetailPlaceholderScreen.tsx
git commit -m "feat: load stock detail on mobile"
```

## Task 8: End-To-End Verification

**Files:**

- Verify only unless failures require fixes.

- [ ] **Step 1: Run backend stock tests**

Run: `cd backend && pytest tests/stocks -v`

Expected: PASS.

- [ ] **Step 2: Run backend seeder tests**

Run: `cd backend && pytest tests/database/test_seeders.py -v`

Expected: PASS.

- [ ] **Step 3: Run mobile typecheck**

Run: `cd mobile && npm run typecheck`

Expected: PASS.

- [ ] **Step 4: Verify OpenAPI includes detail endpoint**

Run: `cd backend && python -m app.openapi ../mobile/src/api/generated/openapi.json`

Expected: command exits 0 and does not remove the stock-detail endpoint.

- [ ] **Step 5: Inspect final diff for recommendation language**

Run: `git diff -- . ':!docs/superpowers/plans/2026-06-02-stock-detail-freshness-disclaimer.md'`

Expected: no UI/API copy uses `buy`, `sell`, or `hold` except historical docs outside implementation files.

- [ ] **Step 6: Commit verification fixes when verification changed files**

If verification required fixes, commit them:

```bash
git add backend mobile
git commit -m "fix: complete stock detail verification"
```

If no fixes were needed, do not create an empty commit.

## Self-Review

- Spec coverage: backend combined endpoint, horizon enum validation, seeded repository data, Hero Summary UI, freshness labels, no-advice disclaimer, unavailable forecast placeholder, generated client, and tests are covered by Tasks 1-8.
- Placeholder scan: the plan avoids deferred work instructions and gives exact code or commands for each implementation step.
- Type consistency: backend response aliases use `companyName`, `latestPrice`, `dailyChange`, `dailyChangePercent`, `observedAt`, `freshnessLabel`, `expectedChangePercent`, `riskLevel`, and `generatedAt`; mobile code uses the same generated TypeScript property names.
