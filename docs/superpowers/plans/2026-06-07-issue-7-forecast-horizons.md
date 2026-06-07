# Issue 7 Forecast Horizons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Forecast Horizon selection work end to end through backend horizon metadata, Stock Detail API contract data, mobile selector UI, and persisted local mobile preference.

**Architecture:** Keep `ForecastHorizon` in `backend/app/forecasts/models.py` as the canonical enum and add a small `backend/app/forecasts/horizons.py` metadata module. Extend Stock Detail with `horizonMetadata`, regenerate the mobile API client, then wire mobile state through AsyncStorage, `getStockDetail`, and a chip selector in `StockDetailScreen`.

**Tech Stack:** Python 3.9, FastAPI, Pydantic v2, pytest, Expo React Native, TypeScript, AsyncStorage, generated OpenAPI TypeScript client.

---

## File Structure

- Create `backend/app/forecasts/horizons.py`: deterministic Forecast Horizon metadata lookup for backend/API consumers.
- Create `backend/tests/forecasts/test_horizons.py`: metadata coverage and semantics tests.
- Modify `backend/app/stocks/schemas.py`: add `StockDetailHorizonMetadata` response schema.
- Modify `backend/app/stocks/router.py`: include horizon metadata in every successful Stock Detail response.
- Modify `backend/tests/stocks/test_stock_detail.py`: prove default/explicit metadata and invalid horizon rejection.
- Regenerate `mobile/src/api/generated/openapi.json` and generated TypeScript models/services after backend schema change.
- Create `mobile/src/storage/forecastHorizon.ts`: persisted mobile Forecast Horizon preference.
- Modify `backend/tests/test_mobile_shell.py`: static mobile checks for horizon preference and selector wiring.
- Modify `mobile/App.tsx`: load, store, and pass selected Forecast Horizon through Stock Detail requests.
- Modify `mobile/src/screens/StockDetailScreen.tsx`: replace static selected-horizon card with selectable chips.

## Task 1: Add Backend Forecast Horizon Metadata

**Files:**
- Create: `backend/app/forecasts/horizons.py`
- Create: `backend/tests/forecasts/test_horizons.py`
- Read: `backend/app/forecasts/models.py`
- Read: `backend/app/forecasts/baseline.py`

- [ ] **Step 1: Write metadata coverage tests**

Create `backend/tests/forecasts/test_horizons.py` with this content:

```python
from app.forecasts.baseline import HORIZON_STEPS
from app.forecasts.horizons import (
    CalendarBasis,
    ForecastHorizonMetadata,
    PricePointBasis,
    TimeBasis,
    all_horizon_metadata,
    get_horizon_metadata,
)
from app.forecasts.models import ForecastHorizon


def test_horizon_metadata_covers_exact_canonical_horizons() -> None:
    metadata = all_horizon_metadata()

    assert set(metadata) == set(ForecastHorizon)
    assert [item.value for item in metadata.values()] == [horizon.value for horizon in ForecastHorizon]


def test_intraday_and_short_term_horizons_use_regular_market_time() -> None:
    assert get_horizon_metadata(ForecastHorizon.thirty_minutes).time_basis == "regular_market"
    assert get_horizon_metadata(ForecastHorizon.one_day).time_basis == "regular_market"
    assert get_horizon_metadata(ForecastHorizon.five_days).time_basis == "regular_market"


def test_longer_horizons_use_calendar_periods_with_trading_session_points() -> None:
    for horizon in (
        ForecastHorizon.seven_days,
        ForecastHorizon.one_month,
        ForecastHorizon.six_months,
        ForecastHorizon.one_year,
    ):
        metadata = get_horizon_metadata(horizon)

        assert metadata.time_basis == "calendar_period"
        assert metadata.price_point_basis == "trading_session"


def test_all_horizons_use_trading_session_price_points() -> None:
    for horizon in ForecastHorizon:
        assert get_horizon_metadata(horizon).price_point_basis == "trading_session"


def test_metadata_expected_point_counts_match_baseline_schedule() -> None:
    for horizon, (expected_count, _interval) in HORIZON_STEPS.items():
        assert get_horizon_metadata(horizon).expected_forecast_point_count == expected_count


def test_one_day_metadata_values_are_explicit() -> None:
    metadata = get_horizon_metadata(ForecastHorizon.one_day)

    assert metadata == ForecastHorizonMetadata(
        value="1d",
        label="1 day",
        time_basis="regular_market",
        price_point_basis="trading_session",
        calendar_basis="regular_market_trading_time",
        news_window_days=3,
        external_factor_weight_scale=1.15,
        expected_forecast_point_count=8,
    )


def test_metadata_type_aliases_match_allowed_literal_values() -> None:
    time_basis: TimeBasis = "regular_market"
    calendar_basis: CalendarBasis = "calendar_period"
    price_point_basis: PricePointBasis = "trading_session"

    assert time_basis == "regular_market"
    assert calendar_basis == "calendar_period"
    assert price_point_basis == "trading_session"
```

- [ ] **Step 2: Run metadata tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest backend/tests/forecasts/test_horizons.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.forecasts.horizons'`.

- [ ] **Step 3: Implement horizon metadata module**

Create `backend/app/forecasts/horizons.py` with this content:

```python
from dataclasses import dataclass
from typing import Literal

from app.forecasts.baseline import HORIZON_STEPS
from app.forecasts.models import ForecastHorizon


TimeBasis = Literal["regular_market", "calendar_period"]
CalendarBasis = Literal["regular_market_trading_time", "calendar_period"]
PricePointBasis = Literal["trading_session"]


@dataclass(frozen=True)
class ForecastHorizonMetadata:
    value: str
    label: str
    time_basis: TimeBasis
    price_point_basis: PricePointBasis
    calendar_basis: CalendarBasis
    news_window_days: int
    external_factor_weight_scale: float
    expected_forecast_point_count: int


HORIZON_METADATA: dict[ForecastHorizon, ForecastHorizonMetadata] = {
    ForecastHorizon.thirty_minutes: ForecastHorizonMetadata(
        value="30m",
        label="30 min",
        time_basis="regular_market",
        price_point_basis="trading_session",
        calendar_basis="regular_market_trading_time",
        news_window_days=1,
        external_factor_weight_scale=1.25,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.thirty_minutes][0],
    ),
    ForecastHorizon.one_day: ForecastHorizonMetadata(
        value="1d",
        label="1 day",
        time_basis="regular_market",
        price_point_basis="trading_session",
        calendar_basis="regular_market_trading_time",
        news_window_days=3,
        external_factor_weight_scale=1.15,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.one_day][0],
    ),
    ForecastHorizon.five_days: ForecastHorizonMetadata(
        value="5d",
        label="5 days",
        time_basis="regular_market",
        price_point_basis="trading_session",
        calendar_basis="regular_market_trading_time",
        news_window_days=7,
        external_factor_weight_scale=1.0,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.five_days][0],
    ),
    ForecastHorizon.seven_days: ForecastHorizonMetadata(
        value="7d",
        label="7 days",
        time_basis="calendar_period",
        price_point_basis="trading_session",
        calendar_basis="calendar_period",
        news_window_days=10,
        external_factor_weight_scale=0.95,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.seven_days][0],
    ),
    ForecastHorizon.one_month: ForecastHorizonMetadata(
        value="1mo",
        label="1 month",
        time_basis="calendar_period",
        price_point_basis="trading_session",
        calendar_basis="calendar_period",
        news_window_days=30,
        external_factor_weight_scale=0.85,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.one_month][0],
    ),
    ForecastHorizon.six_months: ForecastHorizonMetadata(
        value="6mo",
        label="6 months",
        time_basis="calendar_period",
        price_point_basis="trading_session",
        calendar_basis="calendar_period",
        news_window_days=90,
        external_factor_weight_scale=0.7,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.six_months][0],
    ),
    ForecastHorizon.one_year: ForecastHorizonMetadata(
        value="1y",
        label="1 year",
        time_basis="calendar_period",
        price_point_basis="trading_session",
        calendar_basis="calendar_period",
        news_window_days=180,
        external_factor_weight_scale=0.6,
        expected_forecast_point_count=HORIZON_STEPS[ForecastHorizon.one_year][0],
    ),
}


def get_horizon_metadata(horizon: ForecastHorizon) -> ForecastHorizonMetadata:
    return HORIZON_METADATA[horizon]


def all_horizon_metadata() -> dict[ForecastHorizon, ForecastHorizonMetadata]:
    return dict(HORIZON_METADATA)
```

- [ ] **Step 4: Run metadata tests to verify they pass**

Run:

```bash
.venv/bin/python -m pytest backend/tests/forecasts/test_horizons.py -v
```

Expected: PASS, all tests in `backend/tests/forecasts/test_horizons.py` pass.

- [ ] **Step 5: Commit backend metadata module**

Run:

```bash
git add backend/app/forecasts/horizons.py backend/tests/forecasts/test_horizons.py
git commit -m "feat: add forecast horizon metadata"
```

## Task 2: Add Horizon Metadata To Stock Detail API And Generated Client

**Files:**
- Modify: `backend/app/stocks/schemas.py`
- Modify: `backend/app/stocks/router.py`
- Modify: `backend/tests/stocks/test_stock_detail.py`
- Regenerate: `mobile/src/api/generated/openapi.json`
- Regenerate: `mobile/src/api/generated/models/StockDetailResponse.ts`
- Create after generation: `mobile/src/api/generated/models/StockDetailHorizonMetadata.ts`
- Modify after generation: `mobile/src/api/generated/index.ts`

- [ ] **Step 1: Add failing Stock Detail metadata tests**

In `backend/tests/stocks/test_stock_detail.py`, update `test_stock_detail_returns_seeded_supported_stock_for_default_horizon` expected JSON by inserting this block immediately after line containing `"horizon": "1d",`:

```python
        "horizonMetadata": {
            "value": "1d",
            "label": "1 day",
            "timeBasis": "regular_market",
            "pricePointBasis": "trading_session",
            "calendarBasis": "regular_market_trading_time",
            "newsWindowDays": 3,
            "externalFactorWeightScale": 1.15,
            "expectedForecastPointCount": 8,
        },
```

Add these tests below `test_stock_detail_accepts_explicit_valid_horizon`:

```python
def test_stock_detail_returns_metadata_for_explicit_horizon() -> None:
    response = client().get("/stocks/AAPL/detail", params={"horizon": "1mo"})

    assert response.status_code == 200
    assert response.json()["horizon"] == "1mo"
    assert response.json()["horizonMetadata"] == {
        "value": "1mo",
        "label": "1 month",
        "timeBasis": "calendar_period",
        "pricePointBasis": "trading_session",
        "calendarBasis": "calendar_period",
        "newsWindowDays": 30,
        "externalFactorWeightScale": 0.85,
        "expectedForecastPointCount": 10,
    }


def test_stock_detail_rejects_ambiguous_horizon_values_before_repository_lookup() -> None:
    repository = FakeStockDetailRepository()

    for horizon in ("1M", "30M", "2d"):
        response = client(repository).get("/stocks/AAPL/detail", params={"horizon": horizon})

        assert response.status_code == 422

    assert repository.calls == []
```

- [ ] **Step 2: Run Stock Detail tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest backend/tests/stocks/test_stock_detail.py -v
```

Expected: FAIL because `horizonMetadata` is missing from the response.

- [ ] **Step 3: Add Stock Detail metadata schema**

In `backend/app/stocks/schemas.py`, import the metadata literals and add this class above `StockDetailResponse`:

```python
from app.forecasts.horizons import CalendarBasis, PricePointBasis, TimeBasis
```

```python
class StockDetailHorizonMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    value: ForecastHorizon
    label: str
    time_basis: TimeBasis = Field(serialization_alias="timeBasis")
    price_point_basis: PricePointBasis = Field(serialization_alias="pricePointBasis")
    calendar_basis: CalendarBasis = Field(serialization_alias="calendarBasis")
    news_window_days: int = Field(serialization_alias="newsWindowDays")
    external_factor_weight_scale: float = Field(serialization_alias="externalFactorWeightScale")
    expected_forecast_point_count: int = Field(serialization_alias="expectedForecastPointCount")
```

Then update `StockDetailResponse` to include metadata after `horizon`:

```python
class StockDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    stock: StockDetailStock
    horizon: ForecastHorizon
    horizon_metadata: StockDetailHorizonMetadata = Field(serialization_alias="horizonMetadata")
    market: StockDetailMarket
    forecast: StockDetailForecast
    prediction: StockDetailPrediction
    disclaimer: str
```

- [ ] **Step 4: Map metadata in Stock Detail router**

In `backend/app/stocks/router.py`, add imports:

```python
from app.forecasts.horizons import get_horizon_metadata
```

```python
    StockDetailHorizonMetadata,
```

Then, before returning `StockDetailResponse`, add:

```python
    horizon_metadata = get_horizon_metadata(horizon)
```

Update the return value to include:

```python
        horizon_metadata=StockDetailHorizonMetadata(
            value=horizon_metadata.value,
            label=horizon_metadata.label,
            time_basis=horizon_metadata.time_basis,
            price_point_basis=horizon_metadata.price_point_basis,
            calendar_basis=horizon_metadata.calendar_basis,
            news_window_days=horizon_metadata.news_window_days,
            external_factor_weight_scale=horizon_metadata.external_factor_weight_scale,
            expected_forecast_point_count=horizon_metadata.expected_forecast_point_count,
        ),
```

The final return block should include `horizon_metadata` immediately after `horizon=horizon`.

- [ ] **Step 5: Run Stock Detail tests to verify they pass**

Run:

```bash
.venv/bin/python -m pytest backend/tests/stocks/test_stock_detail.py backend/tests/forecasts/test_horizons.py -v
```

Expected: PASS for Stock Detail and horizon metadata tests.

- [ ] **Step 6: Regenerate OpenAPI and mobile client**

Run from repo root:

```bash
./scripts/dev generate-openapi
```

Expected: generated OpenAPI and TypeScript files update. If Docker is unavailable, run these local commands instead:

```bash
cd backend
../.venv/bin/python -m app.openapi ../mobile/src/api/generated/openapi.json
cd ../mobile
npm run generate:api
```

- [ ] **Step 7: Verify generated client contains horizon metadata model**

Run:

```bash
test -f mobile/src/api/generated/models/StockDetailHorizonMetadata.ts
```

Expected: command exits with status 0.

Open `mobile/src/api/generated/models/StockDetailHorizonMetadata.ts` and confirm it has fields equivalent to:

```typescript
import type { ForecastHorizon } from './ForecastHorizon';

export type StockDetailHorizonMetadata = {
    value: ForecastHorizon;
    label: string;
    timeBasis: 'regular_market' | 'calendar_period';
    pricePointBasis: 'trading_session';
    calendarBasis: 'regular_market_trading_time' | 'calendar_period';
    newsWindowDays: number;
    externalFactorWeightScale: number;
    expectedForecastPointCount: number;
};
```

- [ ] **Step 8: Run backend and mobile type checks**

Run:

```bash
.venv/bin/python -m pytest backend/tests/stocks/test_stock_detail.py backend/tests/forecasts/test_horizons.py -v
```

Expected: PASS.

Run:

```bash
cd mobile
npm run typecheck
```

Expected: PASS with no TypeScript errors.

- [ ] **Step 9: Commit Stock Detail contract and generated client**

Run:

```bash
git add backend/app/stocks/schemas.py backend/app/stocks/router.py backend/tests/stocks/test_stock_detail.py mobile/src/api/generated
git commit -m "feat: expose forecast horizon metadata"
```

## Task 3: Add Mobile Forecast Horizon Preference Storage

**Files:**
- Create: `mobile/src/storage/forecastHorizon.ts`
- Modify: `backend/tests/test_mobile_shell.py`
- Read: `mobile/src/storage/primaryStock.ts`
- Read: `mobile/src/api/generated/models/ForecastHorizon.ts`

- [ ] **Step 1: Add failing static tests for horizon preference storage**

Append these tests to `backend/tests/test_mobile_shell.py`:

```python
def test_mobile_declares_forecast_horizon_preference_storage() -> None:
    storage_path = (
        Path(__file__).resolve().parents[2]
        / "mobile"
        / "src"
        / "storage"
        / "forecastHorizon.ts"
    )

    source = storage_path.read_text()

    assert 'const FORECAST_HORIZON_KEY = "trendwise.forecastHorizon"' in source
    assert 'export const DEFAULT_FORECAST_HORIZON: ForecastHorizon = "1d"' in source
    assert '"30m", "1d", "5d", "7d", "1mo", "6mo", "1y"' in source
    assert "FORECAST_HORIZON_LABELS" in source
    assert '"1mo": "1 month"' in source
    assert "loadForecastHorizon" in source
    assert "saveForecastHorizon" in source


def test_mobile_forecast_horizon_storage_rejects_ambiguous_values() -> None:
    source = (
        Path(__file__).resolve().parents[2]
        / "mobile"
        / "src"
        / "storage"
        / "forecastHorizon.ts"
    ).read_text()

    assert 'return DEFAULT_FORECAST_HORIZON' in source
    assert 'value is ForecastHorizon' in source
    assert '"1M"' not in source
    assert '"30M"' not in source
    assert '"2d"' not in source
```

- [ ] **Step 2: Run static tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest backend/tests/test_mobile_shell.py::test_mobile_declares_forecast_horizon_preference_storage backend/tests/test_mobile_shell.py::test_mobile_forecast_horizon_storage_rejects_ambiguous_values -v
```

Expected: FAIL with `FileNotFoundError` for `mobile/src/storage/forecastHorizon.ts`.

- [ ] **Step 3: Implement Forecast Horizon storage module**

Create `mobile/src/storage/forecastHorizon.ts` with this content:

```typescript
import AsyncStorage from "@react-native-async-storage/async-storage";

import type { ForecastHorizon } from "../api/stocks";

const FORECAST_HORIZON_KEY = "trendwise.forecastHorizon";

export const DEFAULT_FORECAST_HORIZON: ForecastHorizon = "1d";
export const FORECAST_HORIZONS: ForecastHorizon[] = ["30m", "1d", "5d", "7d", "1mo", "6mo", "1y"];
export const FORECAST_HORIZON_LABELS: Record<ForecastHorizon, string> = {
  "30m": "30 min",
  "1d": "1 day",
  "5d": "5 days",
  "7d": "7 days",
  "1mo": "1 month",
  "6mo": "6 months",
  "1y": "1 year",
};

export function isForecastHorizon(value: unknown): value is ForecastHorizon {
  return typeof value === "string" && FORECAST_HORIZONS.includes(value as ForecastHorizon);
}

export async function loadForecastHorizon(): Promise<ForecastHorizon> {
  const rawValue = await AsyncStorage.getItem(FORECAST_HORIZON_KEY);
  if (!rawValue) {
    return DEFAULT_FORECAST_HORIZON;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(rawValue);
  } catch {
    return DEFAULT_FORECAST_HORIZON;
  }

  return isForecastHorizon(parsed) ? parsed : DEFAULT_FORECAST_HORIZON;
}

export async function saveForecastHorizon(horizon: ForecastHorizon): Promise<void> {
  await AsyncStorage.setItem(FORECAST_HORIZON_KEY, JSON.stringify(horizon));
}
```

- [ ] **Step 4: Run storage tests and mobile typecheck**

Run:

```bash
.venv/bin/python -m pytest backend/tests/test_mobile_shell.py::test_mobile_declares_forecast_horizon_preference_storage backend/tests/test_mobile_shell.py::test_mobile_forecast_horizon_storage_rejects_ambiguous_values -v
```

Expected: PASS.

Run:

```bash
cd mobile
npm run typecheck
```

Expected: PASS with no TypeScript errors.

- [ ] **Step 5: Commit mobile horizon preference storage**

Run:

```bash
git add mobile/src/storage/forecastHorizon.ts backend/tests/test_mobile_shell.py
git commit -m "feat: persist forecast horizon preference"
```

## Task 4: Wire Mobile Horizon Selector Through Stock Detail

**Files:**
- Modify: `mobile/App.tsx`
- Modify: `mobile/src/screens/StockDetailScreen.tsx`
- Modify: `backend/tests/test_mobile_shell.py`
- Read: `mobile/src/api/stocks.ts`
- Read: `mobile/src/storage/forecastHorizon.ts`

- [ ] **Step 1: Add failing static tests for mobile horizon flow**

Append these tests to `backend/tests/test_mobile_shell.py`:

```python
def test_mobile_app_loads_and_saves_selected_forecast_horizon() -> None:
    app_source = (Path(__file__).resolve().parents[2] / "mobile" / "App.tsx").read_text()

    assert "loadForecastHorizon" in app_source
    assert "saveForecastHorizon" in app_source
    assert "selectedHorizon" in app_source
    assert "handleChangeHorizon" in app_source
    assert "getStockDetail(stock.ticker, horizon)" in app_source
    assert 'getStockDetail(stock.ticker, "1d")' not in app_source


def test_mobile_stock_detail_exposes_forecast_horizon_selector() -> None:
    detail_source = (
        Path(__file__).resolve().parents[2]
        / "mobile"
        / "src"
        / "screens"
        / "StockDetailScreen.tsx"
    ).read_text()

    assert "selectedHorizon" in detail_source
    assert "horizonOptions" in detail_source
    assert "onChangeHorizon" in detail_source
    assert "Forecast horizon" in detail_source
    assert "accessibilityLabel={`Select ${option.label} Forecast Horizon`}" in detail_source
```

- [ ] **Step 2: Run static tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest backend/tests/test_mobile_shell.py::test_mobile_app_loads_and_saves_selected_forecast_horizon backend/tests/test_mobile_shell.py::test_mobile_stock_detail_exposes_forecast_horizon_selector -v
```

Expected: FAIL because `App.tsx` does not load/save selected horizon and `StockDetailScreen.tsx` has no selector props.

- [ ] **Step 3: Update `App.tsx` imports and app state**

In `mobile/App.tsx`, change imports to include `ForecastHorizon` and horizon storage:

```typescript
import { getStockDetail, type ForecastHorizon, type PrimaryStock, type StockDetail } from "./src/api/stocks";
```

```typescript
import {
  DEFAULT_FORECAST_HORIZON,
  FORECAST_HORIZON_LABELS,
  FORECAST_HORIZONS,
  loadForecastHorizon,
  saveForecastHorizon,
} from "./src/storage/forecastHorizon";
```

Add selected horizon state after `appState`:

```typescript
  const [selectedHorizon, setSelectedHorizon] = useState<ForecastHorizon>(DEFAULT_FORECAST_HORIZON);
```

Add a save queue after `savePrimaryStockQueue`:

```typescript
  const saveForecastHorizonQueue = useRef<Promise<void>>(Promise.resolve());
```

- [ ] **Step 4: Update startup hydration in `App.tsx`**

Replace `hydratePrimaryStock` body with:

```typescript
    async function hydratePrimaryStock() {
      try {
        const [cachedStock, cachedHorizon] = await Promise.all([
          loadPrimaryStock(),
          loadForecastHorizon(),
        ]);
        if (isActive) {
          setSelectedHorizon(cachedHorizon);
          if (cachedStock) {
            loadDetailForStock(cachedStock, cachedHorizon);
          } else {
            setAppState({ status: "search" });
          }
        }
      } catch {
        if (isActive) {
          setAppState({ status: "search" });
        }
      }
    }
```

- [ ] **Step 5: Update detail loading and selection flow in `App.tsx`**

Change `loadDetailForStock` signature and request call to:

```typescript
  async function loadDetailForStock(stock: PrimaryStock, horizon: ForecastHorizon = selectedHorizon) {
    const requestId = detailRequestId.current + 1;
    detailRequestId.current = requestId;

    setAppState({ status: "detail-loading", stock });

    try {
      const detail = await getStockDetail(stock.ticker, horizon);
      if (detailRequestId.current === requestId) {
        setDetailError(null);
        setAppState({ status: "detail", stock, detail });
      }
    } catch {
      if (detailRequestId.current === requestId) {
        setDetailError("Could not load Stock details. Try again.");
        setAppState({ status: "detail-error", stock });
      }
    }
  }
```

In `handleSelectStock`, keep the existing save logic and update the load call to:

```typescript
      loadDetailForStock(stock, selectedHorizon);
```

In the retry button handler, update the load call to:

```typescript
            onPress={() => loadDetailForStock(appState.stock, selectedHorizon)}
```

- [ ] **Step 6: Add horizon change handler in `App.tsx`**

Add this function before `handleChangeStock`:

```typescript
  async function handleChangeHorizon(horizon: ForecastHorizon) {
    if (horizon === selectedHorizon) {
      return;
    }

    setSelectedHorizon(horizon);

    try {
      const savePromise = saveForecastHorizonQueue.current.then(() => saveForecastHorizon(horizon));
      saveForecastHorizonQueue.current = savePromise.catch(() => undefined);
      await savePromise;
    } catch {
      setDetailError("Could not save your selected Forecast Horizon. Try again.");
    }

    if (appState.status === "detail" || appState.status === "detail-error" || appState.status === "detail-loading") {
      loadDetailForStock(appState.stock, horizon);
    }
  }
```

When rendering `StockDetailScreen`, pass the new props:

```typescript
        <StockDetailScreen
          detail={appState.detail}
          detailError={detailError}
          horizonOptions={FORECAST_HORIZONS.map((value) => ({
            value,
            label: FORECAST_HORIZON_LABELS[value],
          }))}
          onChangeHorizon={handleChangeHorizon}
          onChangeStock={handleChangeStock}
          selectedHorizon={selectedHorizon}
        />
```

- [ ] **Step 7: Update `StockDetailScreen.tsx` props and imports**

In `mobile/src/screens/StockDetailScreen.tsx`, update imports:

```typescript
import { Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";

import type { ForecastHorizon, StockDetail } from "../api/stocks";
```

Replace props type with:

```typescript
type HorizonOption = {
  value: ForecastHorizon;
  label: string;
};

type StockDetailScreenProps = {
  detail: StockDetail;
  detailError: string | null;
  horizonOptions: HorizonOption[];
  onChangeHorizon: (horizon: ForecastHorizon) => void;
  onChangeStock: () => void;
  selectedHorizon: ForecastHorizon;
};
```

Update function destructuring:

```typescript
export function StockDetailScreen({
  detail,
  detailError,
  horizonOptions,
  onChangeHorizon,
  onChangeStock,
  selectedHorizon,
}: StockDetailScreenProps) {
```

- [ ] **Step 8: Replace static horizon card with selector**

In `StockDetailScreen.tsx`, replace the card beginning with `<Text style={styles.cardKicker}>Selected horizon</Text>` through its closing `</View>` with:

```tsx
        <View style={styles.card}>
          <Text style={styles.cardKicker}>Forecast horizon</Text>
          <View style={styles.horizonChips}>
            {horizonOptions.map((option) => {
              const isSelected = option.value === selectedHorizon;

              return (
                <Pressable
                  accessibilityLabel={`Select ${option.label} Forecast Horizon`}
                  accessibilityRole="button"
                  key={option.value}
                  onPress={() => onChangeHorizon(option.value)}
                  style={[styles.horizonChip, isSelected ? styles.horizonChipSelected : null]}
                >
                  <Text style={[styles.horizonChipText, isSelected ? styles.horizonChipTextSelected : null]}>
                    {option.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
          <View style={styles.predictionFacts}>
            <Text style={styles.fact}>{formatConfidence(prediction.confidence)}</Text>
            <Text style={styles.fact}>{formatExpectedChange(prediction.expectedChangePercent)}</Text>
          </View>
          <Text style={styles.cardFreshness}>{prediction.freshnessLabel}</Text>
        </View>
```

Update graph-unavailable card copy to mention horizon metadata:

```tsx
          <Text style={styles.cardBody}>
            Forecast graph rendering comes later. Backend graph data is loaded for the {detail.horizonMetadata.label} horizon with {detail.horizonMetadata.expectedForecastPointCount} forecast points.
          </Text>
```

- [ ] **Step 9: Add selector styles**

Add these styles to `StyleSheet.create` in `StockDetailScreen.tsx` before `predictionFacts`:

```typescript
  horizonChips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 12,
  },
  horizonChip: {
    backgroundColor: "#e2e8f0",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  horizonChipSelected: {
    backgroundColor: "#2563eb",
  },
  horizonChipText: {
    color: "#334155",
    fontSize: 13,
    fontWeight: "800",
  },
  horizonChipTextSelected: {
    color: "#ffffff",
  },
```

- [ ] **Step 10: Run mobile flow static tests and typecheck**

Run:

```bash
.venv/bin/python -m pytest backend/tests/test_mobile_shell.py::test_mobile_app_loads_and_saves_selected_forecast_horizon backend/tests/test_mobile_shell.py::test_mobile_stock_detail_exposes_forecast_horizon_selector -v
```

Expected: PASS.

Run:

```bash
cd mobile
npm run typecheck
```

Expected: PASS with no TypeScript errors.

- [ ] **Step 11: Commit mobile horizon selector flow**

Run:

```bash
git add mobile/App.tsx mobile/src/screens/StockDetailScreen.tsx backend/tests/test_mobile_shell.py
git commit -m "feat: add forecast horizon selector"
```

## Task 5: Final Verification And Issue Readiness

**Files:**
- Verify: all modified backend and mobile files
- Verify: generated OpenAPI/client files
- Verify: git status and commit history

- [ ] **Step 1: Run full backend test suite**

Run from repo root:

```bash
.venv/bin/python -m pytest -v
```

Expected: PASS, all backend tests pass with 0 failures.

- [ ] **Step 2: Run mobile typecheck**

Run:

```bash
cd mobile
npm run typecheck
```

Expected: PASS with no TypeScript errors.

- [ ] **Step 3: Inspect generated-client drift**

Run:

```bash
git diff -- mobile/src/api/generated
```

Expected: generated diff includes `horizonMetadata` and does not remove canonical `ForecastHorizon` values.

- [ ] **Step 4: Inspect working tree**

Run:

```bash
git status --short --branch
```

Expected: clean working tree on `issue-7-forecast-horizons` after all task commits.

- [ ] **Step 5: Confirm acceptance criteria manually**

Check these facts before claiming completion:

```text
Allowed horizons: backend enum and generated mobile union are exactly 30m, 1d, 5d, 7d, 1mo, 6mo, 1y.
Invalid horizons: tests cover 1M, 30M, and 2d returning 422 before repository lookup.
Default horizon: Stock Detail default remains 1d and returns 1d metadata.
Regular-market horizons: metadata marks 30m, 1d, and 5d as regular_market.
Calendar horizons: metadata marks 7d, 1mo, 6mo, and 1y as calendar_period with trading_session price points.
Changing horizon: mobile selector saves the chosen horizon and reloads Stock Detail with it.
Persistence: mobile AsyncStorage key trendwise.forecastHorizon stores only canonical values.
Boundaries: graph rendering remains issue #8; summary/news/key-factor UI remains issue #9; refresh jobs remain issue #12.
```

- [ ] **Step 6: If any files remain uncommitted, commit only intended implementation files**

Run:

```bash
git status --short
```

If intended implementation files remain, stage only those files and commit with an appropriate message. Do not stage local artifacts such as `.venv/`, `node_modules/`, `.pytest_cache/`, `backend/trendwise_backend.egg-info/`, or unintended lockfile churn from local dependency installation.

- [ ] **Step 7: Prepare completion summary**

Report:

```text
Implemented issue #7 on branch issue-7-forecast-horizons.
Backend verification: .venv/bin/python -m pytest -v -> pass count from output.
Mobile verification: npm run typecheck -> passed.
Key changes: horizon metadata contract, Stock Detail horizonMetadata, generated client update, mobile persisted horizon selector.
Deferred by design: graph rendering (#8), summary/news/key-factor UI (#9), refresh jobs (#12).
```
