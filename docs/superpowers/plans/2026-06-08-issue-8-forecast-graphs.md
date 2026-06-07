# Issue 8 Forecast Graphs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render single-stock Line and Candlestick Forecast Graphs with historical actual-price context and persisted graph type preference.

**Architecture:** Extend the Stock Detail forecast contract with `historicalPoints` sourced from existing `market_snapshots`, regenerate the mobile API client, then add a focused `ForecastGraph` component rendered with `react-native-svg`. Keep Forecast Horizon as the backend reload trigger; graph type is local UI state and persists through AsyncStorage.

**Tech Stack:** Python 3.9, FastAPI, Pydantic v2, pytest, Expo React Native, TypeScript, `react-native-svg`, AsyncStorage, generated OpenAPI TypeScript client.

---

## File Structure

- Modify `backend/app/stocks/repository.py`: add typed historical graph point rows and query recent actual prices from `market_snapshots`.
- Modify `backend/app/stocks/schemas.py`: add `StockDetailForecastHistoricalPoint` and include `historical_points` serialized as `historicalPoints`.
- Modify `backend/app/stocks/router.py`: map repository historical points into API response objects.
- Modify `backend/tests/stocks/test_stock_detail.py`: prove repository mapping and API response include historical actual-price points.
- Regenerate `mobile/src/api/generated/openapi.json` and generated TypeScript models.
- Modify `mobile/src/api/stocks.ts`: re-export generated forecast point/candlestick types needed by the graph component.
- Modify `mobile/package.json` and `mobile/package-lock.json`: add `react-native-svg`.
- Create `mobile/src/storage/graphType.ts`: persist `line` or `candlestick`, defaulting to `line`.
- Modify `mobile/App.tsx`: hydrate, save, and pass selected graph type through the detail screen.
- Modify `mobile/src/screens/StockDetailScreen.tsx`: pass graph props and replace the unavailable card with `ForecastGraph`.
- Create `mobile/src/components/ForecastGraph.tsx`: focused dark graph card with SVG line/candlestick rendering, dashed uncertainty limits, and empty states.
- Modify `backend/tests/test_mobile_shell.py`: static checks for dependency, storage, wiring, and graph UI copy.
- Modify `mobile/src/appState.test.ts`: include `historicalPoints` in typed fixture after generated client changes.

## Task 1: Add Historical Graph Points To Stock Detail Backend Contract

**Files:**
- Modify: `backend/tests/stocks/test_stock_detail.py`
- Modify: `backend/app/stocks/repository.py`
- Modify: `backend/app/stocks/schemas.py`
- Modify: `backend/app/stocks/router.py`

- [ ] **Step 1: Add failing repository and API tests for historical graph points**

In `backend/tests/stocks/test_stock_detail.py`, update `FakeStockDetailRepository.details["AAPL"]["forecast"]` so the forecast dict contains `historical_points` before `line_points`:

```python
                    "historical_points": [
                        {
                            "sequence": 1,
                            "timestamp": datetime(2026, 6, 2, 12, 30, tzinfo=timezone.utc),
                            "value": 211.7,
                        },
                        {
                            "sequence": 2,
                            "timestamp": datetime(2026, 6, 2, 13, 30, tzinfo=timezone.utc),
                            "value": 214.35,
                        },
                    ],
```

In `test_postgres_stock_detail_repository_maps_supported_stock_detail_rows`, add the historical rows list immediately after the forecast row tuple `(10, "unavailable", forecast_generated_at),`:

```python
            [
                (
                    1,
                    datetime(2026, 6, 2, 12, 30, tzinfo=timezone.utc),
                    Decimal("211.70"),
                ),
                (
                    2,
                    datetime(2026, 6, 2, 13, 30, tzinfo=timezone.utc),
                    Decimal("214.35"),
                ),
            ],
```

In the expected repository `detail["forecast"]` dict, add:

```python
            "historical_points": [
                {
                    "sequence": 1,
                    "timestamp": datetime(2026, 6, 2, 12, 30, tzinfo=timezone.utc),
                    "value": 211.7,
                },
                {
                    "sequence": 2,
                    "timestamp": datetime(2026, 6, 2, 13, 30, tzinfo=timezone.utc),
                    "value": 214.35,
                },
            ],
```

Update the expected executed params list in the same test so it includes the historical query after the forecast lookup:

```python
    assert [params for _, params in connection.cursor_instance.executed] == [
        {"ticker": "AAPL"},
        {"stock_id": 1},
        {"stock_id": 1, "horizon": "1d"},
        {"stock_id": 1},
        {"forecast_run_id": 10},
        {"forecast_run_id": 10},
        {"forecast_run_id": 10},
        {"prediction_run_id": 11},
    ]
```

Update the SQL assertions in the same test:

```python
    assert "FROM market_snapshots" in sql
    assert "ROW_NUMBER() OVER (ORDER BY observed_at ASC, id ASC)" in sql
    prediction_query = connection.cursor_instance.executed[6][0]
```

In `test_stock_detail_returns_seeded_supported_stock_for_default_horizon`, add this block in the expected `forecast` JSON before `linePoints`:

```python
            "historicalPoints": [
                {
                    "sequence": 1,
                    "timestamp": "2026-06-02T12:30:00Z",
                    "value": 211.7,
                },
                {
                    "sequence": 2,
                    "timestamp": "2026-06-02T13:30:00Z",
                    "value": 214.35,
                },
            ],
```

In `test_stock_detail_returns_unavailable_sections_for_missing_detail_rows`, add:

```python
    assert body["forecast"]["historicalPoints"] == []
```

- [ ] **Step 2: Run Stock Detail tests and verify they fail**

Run:

```bash
.venv/bin/python -m pytest backend/tests/stocks/test_stock_detail.py -v
```

Expected: FAIL because `historical_points` / `historicalPoints` are missing from repository and API mapping.

- [ ] **Step 3: Add repository historical point types and query**

In `backend/app/stocks/repository.py`, add this `TypedDict` after `StockForecastDetailRow`:

```python
class StockForecastHistoricalPointRow(TypedDict):
    sequence: int
    timestamp: datetime
    value: float
```

Update `StockForecastDetailRow` to include historical points:

```python
class StockForecastDetailRow(TypedDict):
    id: int
    status: str
    generated_at: datetime
    historical_points: list["StockForecastHistoricalPointRow"]
    line_points: list["StockForecastLinePointRow"]
    candlesticks: list["StockForecastCandlestickRow"]
```

In `PostgresStockDetailRepository.get_detail`, add a local list before the forecast detail queries:

```python
            historical_points: list[StockForecastHistoricalPointRow] = []
            line_points: list[StockForecastLinePointRow] = []
            candlesticks: list[StockForecastCandlestickRow] = []
```

Replace the existing two-list initialization:

```python
            line_points: list[StockForecastLinePointRow] = []
            candlesticks: list[StockForecastCandlestickRow] = []
```

with:

```python
            historical_points: list[StockForecastHistoricalPointRow] = []
            line_points: list[StockForecastLinePointRow] = []
            candlesticks: list[StockForecastCandlestickRow] = []
```

Inside `if forecast is not None:`, before the `forecast_line_points` query, add:

```python
                cursor.execute(
                    """
                    SELECT sequence, observed_at, latest_price
                    FROM (
                        SELECT
                            ROW_NUMBER() OVER (ORDER BY observed_at ASC, id ASC) AS sequence,
                            observed_at,
                            latest_price
                        FROM (
                            SELECT id, observed_at, latest_price
                            FROM market_snapshots
                            WHERE stock_id = %(stock_id)s
                            ORDER BY observed_at DESC, id DESC
                            LIMIT 8
                        ) recent_market_snapshots
                    ) ordered_market_snapshots
                    ORDER BY sequence ASC
                    """,
                    {"stock_id": stock_id},
                )
                historical_points = [
                    {
                        "sequence": row[0],
                        "timestamp": row[1],
                        "value": numeric_to_float(row[2]),
                    }
                    for row in cursor.fetchall()
                ]
```

In the returned forecast dict, add `historical_points` before `line_points`:

```python
            "forecast": None
            if forecast is None
            else {
                "status": forecast[1],
                "generated_at": forecast[2],
                "historical_points": historical_points,
                "line_points": line_points,
                "candlesticks": candlesticks,
            },
```

- [ ] **Step 4: Add backend response schema and router mapping**

In `backend/app/stocks/schemas.py`, update `StockDetailForecast` so it includes `historical_points` before `line_points`:

```python
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
```

Add this schema class immediately before `StockDetailForecastLinePoint`:

```python
class StockDetailForecastHistoricalPoint(BaseModel):
    sequence: int
    timestamp: str
    value: float
```

In `backend/app/stocks/router.py`, add `StockDetailForecastHistoricalPoint` to the schema imports:

```python
    StockDetailForecastHistoricalPoint,
```

In the `StockDetailForecast(...)` construction for available forecasts, add `historical_points` before `line_points`:

```python
            historical_points=[
                StockDetailForecastHistoricalPoint(
                    sequence=point["sequence"],
                    timestamp=format_utc_datetime(point["timestamp"]),
                    value=point["value"],
                )
                for point in forecast_row["historical_points"]
            ],
```

- [ ] **Step 5: Run backend contract tests and verify they pass**

Run:

```bash
.venv/bin/python -m pytest backend/tests/stocks/test_stock_detail.py -v
```

Expected: PASS for all Stock Detail tests.

- [ ] **Step 6: Commit backend historical graph contract**

Run:

```bash
git add backend/app/stocks/repository.py backend/app/stocks/schemas.py backend/app/stocks/router.py backend/tests/stocks/test_stock_detail.py
git commit -m "feat: expose historical forecast graph points"
```

## Task 2: Regenerate OpenAPI Client And Add SVG Dependency

**Files:**
- Regenerate: `mobile/src/api/generated/openapi.json`
- Regenerate: `mobile/src/api/generated/models/StockDetailForecast.ts`
- Create after generation: `mobile/src/api/generated/models/StockDetailForecastHistoricalPoint.ts`
- Modify after generation: `mobile/src/api/generated/index.ts`
- Modify: `mobile/src/api/stocks.ts`
- Modify: `mobile/package.json`
- Modify: `mobile/package-lock.json`
- Modify: `mobile/src/appState.test.ts`

- [ ] **Step 1: Regenerate OpenAPI and generated mobile client**

Run from repo root:

```bash
./scripts/dev generate-openapi
```

Expected: generated OpenAPI and TypeScript files update. If Docker is unavailable, run:

```bash
cd backend
../.venv/bin/python -m app.openapi ../mobile/src/api/generated/openapi.json
cd ../mobile
npm run generate:api
```

- [ ] **Step 2: Verify generated historical point model exists**

Run:

```bash
test -f mobile/src/api/generated/models/StockDetailForecastHistoricalPoint.ts
```

Expected: command exits with status 0.

Open `mobile/src/api/generated/models/StockDetailForecastHistoricalPoint.ts` and confirm it contains this shape:

```typescript
export type StockDetailForecastHistoricalPoint = {
    sequence: number;
    timestamp: string;
    value: number;
};
```

Open `mobile/src/api/generated/models/StockDetailForecast.ts` and confirm it imports and exposes `historicalPoints`:

```typescript
import type { StockDetailForecastHistoricalPoint } from './StockDetailForecastHistoricalPoint';

export type StockDetailForecast = {
    candlesticks?: Array<StockDetailForecastCandlestick>;
    freshnessLabel: string;
    generatedAt: (string | null);
    historicalPoints?: Array<StockDetailForecastHistoricalPoint>;
    linePoints?: Array<StockDetailForecastLinePoint>;
    status: string;
};
```

- [ ] **Step 3: Add `react-native-svg` dependency**

Run:

```bash
cd mobile
npm install react-native-svg
```

Expected: `mobile/package.json` includes `react-native-svg` in `dependencies`, and `mobile/package-lock.json` is updated.

- [ ] **Step 4: Re-export graph-related generated types**

In `mobile/src/api/stocks.ts`, update the generated import to include these types:

```typescript
  type StockDetailForecastCandlestick,
  type StockDetailForecastHistoricalPoint,
  type StockDetailForecastLinePoint,
```

The top import should become:

```typescript
import {
  OpenAPI,
  StocksService,
  type ForecastHorizon,
  type StockDetailForecastCandlestick,
  type StockDetailForecastHistoricalPoint,
  type StockDetailForecastLinePoint,
  type StockDetailResponse,
  type StockSearchResult,
} from "./generated";
```

Update the exports below the existing type aliases:

```typescript
export type PrimaryStock = StockSearchResult;
export type StockDetail = StockDetailResponse;
export type {
  ForecastHorizon,
  StockDetailForecastCandlestick,
  StockDetailForecastHistoricalPoint,
  StockDetailForecastLinePoint,
};
```

- [ ] **Step 5: Update mobile typed fixture for historical points**

In `mobile/src/appState.test.ts`, update the `forecast` fixture so it includes `historicalPoints: []`:

```typescript
  forecast: {
    freshnessLabel: "fresh",
    generatedAt: null,
    historicalPoints: [],
    status: "available",
  },
```

- [ ] **Step 6: Run backend contract tests and mobile typecheck**

Run:

```bash
.venv/bin/python -m pytest backend/tests/stocks/test_stock_detail.py -v
```

Expected: PASS.

Run:

```bash
cd mobile
npm run typecheck
```

Expected: PASS with no TypeScript errors.

- [ ] **Step 7: Commit generated client and dependency update**

Run:

```bash
git add mobile/package.json mobile/package-lock.json mobile/src/api/generated mobile/src/api/stocks.ts mobile/src/appState.test.ts
git commit -m "feat: add forecast graph client contract"
```

## Task 3: Add Mobile Graph Type Preference Storage And App Wiring

**Files:**
- Create: `mobile/src/storage/graphType.ts`
- Modify: `backend/tests/test_mobile_shell.py`
- Modify: `mobile/App.tsx`
- Modify: `mobile/src/screens/StockDetailScreen.tsx`

- [ ] **Step 1: Add failing static tests for graph type storage and app wiring**

Append these tests to `backend/tests/test_mobile_shell.py`:

```python
def test_mobile_declares_graph_type_preference_storage() -> None:
    storage_path = (
        Path(__file__).resolve().parents[2]
        / "mobile"
        / "src"
        / "storage"
        / "graphType.ts"
    )

    source = storage_path.read_text()

    assert 'const GRAPH_TYPE_KEY = "trendwise.graphType"' in source
    assert 'export type GraphType = "line" | "candlestick"' in source
    assert 'export const DEFAULT_GRAPH_TYPE: GraphType = "line"' in source
    assert 'export const GRAPH_TYPES: GraphType[] = ["line", "candlestick"]' in source
    assert "value is GraphType" in source
    assert "loadGraphType" in source
    assert "saveGraphType" in source


def test_mobile_app_loads_and_saves_selected_graph_type() -> None:
    app_source = (Path(__file__).resolve().parents[2] / "mobile" / "App.tsx").read_text()

    assert "loadGraphType" in app_source
    assert "saveGraphType" in app_source
    assert "selectedGraphType" in app_source
    assert "handleChangeGraphType" in app_source
    assert "saveGraphTypeQueue" in app_source
    assert "onChangeGraphType={handleChangeGraphType}" in app_source
    assert "selectedGraphType={selectedGraphType}" in app_source
```

- [ ] **Step 2: Run static tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest backend/tests/test_mobile_shell.py::test_mobile_declares_graph_type_preference_storage backend/tests/test_mobile_shell.py::test_mobile_app_loads_and_saves_selected_graph_type -v
```

Expected: FAIL with `FileNotFoundError` for `graphType.ts` and/or missing app wiring strings.

- [ ] **Step 3: Implement graph type storage module**

Create `mobile/src/storage/graphType.ts` with this content:

```typescript
import AsyncStorage from "@react-native-async-storage/async-storage";

const GRAPH_TYPE_KEY = "trendwise.graphType";

export type GraphType = "line" | "candlestick";

export const DEFAULT_GRAPH_TYPE: GraphType = "line";
export const GRAPH_TYPES: GraphType[] = ["line", "candlestick"];
export const GRAPH_TYPE_LABELS: Record<GraphType, string> = {
  line: "Line",
  candlestick: "Candlestick",
};

export function isGraphType(value: unknown): value is GraphType {
  return typeof value === "string" && GRAPH_TYPES.includes(value as GraphType);
}

export async function loadGraphType(): Promise<GraphType> {
  const rawValue = await AsyncStorage.getItem(GRAPH_TYPE_KEY);
  if (!rawValue) {
    return DEFAULT_GRAPH_TYPE;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(rawValue);
  } catch {
    return DEFAULT_GRAPH_TYPE;
  }

  return isGraphType(parsed) ? parsed : DEFAULT_GRAPH_TYPE;
}

export async function saveGraphType(graphType: GraphType): Promise<void> {
  await AsyncStorage.setItem(GRAPH_TYPE_KEY, JSON.stringify(graphType));
}
```

- [ ] **Step 4: Wire graph type through `App.tsx`**

In `mobile/App.tsx`, add graph type imports after the forecast horizon storage import:

```typescript
import {
  DEFAULT_GRAPH_TYPE,
  GRAPH_TYPE_LABELS,
  GRAPH_TYPES,
  type GraphType,
  loadGraphType,
  saveGraphType,
} from "./src/storage/graphType";
```

Add selected graph type state after selected horizon state:

```typescript
  const [selectedGraphType, setSelectedGraphType] = useState<GraphType>(DEFAULT_GRAPH_TYPE);
```

Add a save queue after `saveForecastHorizonQueue`:

```typescript
  const saveGraphTypeQueue = useRef<Promise<void>>(Promise.resolve());
```

In `hydratePrimaryStock`, change the `Promise.all` call to include graph type:

```typescript
        const [cachedStock, cachedHorizon, cachedGraphType] = await Promise.all([
          loadPrimaryStock(),
          loadForecastHorizon(),
          loadGraphType(),
        ]);
```

Inside `if (isActive)`, set graph type before loading details:

```typescript
          setSelectedHorizon(cachedHorizon);
          setSelectedGraphType(cachedGraphType);
```

Add this function before `handleChangeStock`:

```typescript
  async function handleChangeGraphType(graphType: GraphType) {
    if (graphType === selectedGraphType) {
      return;
    }

    setSelectedGraphType(graphType);

    try {
      const savePromise = saveGraphTypeQueue.current.then(() => saveGraphType(graphType));
      saveGraphTypeQueue.current = savePromise.catch(() => undefined);
      await savePromise;
    } catch {
      setDetailError("Could not save your selected Forecast Graph type. Try again.");
    }
  }
```

When rendering `StockDetailScreen`, pass graph type props after horizon props:

```tsx
          graphTypeOptions={GRAPH_TYPES.map((value) => ({
            value,
            label: GRAPH_TYPE_LABELS[value],
          }))}
          onChangeGraphType={handleChangeGraphType}
          selectedGraphType={selectedGraphType}
```

- [ ] **Step 5: Update `StockDetailScreen.tsx` props for graph type**

In `mobile/src/screens/StockDetailScreen.tsx`, add import:

```typescript
import type { GraphType } from "../storage/graphType";
```

Add this type after `HorizonOption`:

```typescript
type GraphTypeOption = {
  value: GraphType;
  label: string;
};
```

Update `StockDetailScreenProps`:

```typescript
type StockDetailScreenProps = {
  detail: StockDetail;
  detailError: string | null;
  graphTypeOptions: GraphTypeOption[];
  horizonOptions: HorizonOption[];
  onChangeGraphType: (graphType: GraphType) => void;
  onChangeHorizon: (horizon: ForecastHorizon) => void;
  onChangeStock: () => void;
  selectedGraphType: GraphType;
  selectedHorizon: ForecastHorizon;
};
```

Update function destructuring:

```typescript
export function StockDetailScreen({
  detail,
  detailError,
  graphTypeOptions,
  horizonOptions,
  onChangeGraphType,
  onChangeHorizon,
  onChangeStock,
  selectedGraphType,
  selectedHorizon,
}: StockDetailScreenProps) {
```

Do not render `ForecastGraph` yet in this task; that comes in Task 4.

- [ ] **Step 6: Run graph type storage tests and mobile typecheck**

Run:

```bash
.venv/bin/python -m pytest backend/tests/test_mobile_shell.py::test_mobile_declares_graph_type_preference_storage backend/tests/test_mobile_shell.py::test_mobile_app_loads_and_saves_selected_graph_type -v
```

Expected: PASS.

Run:

```bash
cd mobile
npm run typecheck
```

Expected: PASS with no TypeScript errors.

- [ ] **Step 7: Commit graph type preference wiring**

Run:

```bash
git add backend/tests/test_mobile_shell.py mobile/App.tsx mobile/src/screens/StockDetailScreen.tsx mobile/src/storage/graphType.ts
git commit -m "feat: persist forecast graph type preference"
```

## Task 4: Render ForecastGraph With Line And Candlestick Modes

**Files:**
- Create: `mobile/src/components/ForecastGraph.tsx`
- Modify: `mobile/src/screens/StockDetailScreen.tsx`
- Modify: `backend/tests/test_mobile_shell.py`

- [ ] **Step 1: Add failing static tests for graph rendering**

Append these tests to `backend/tests/test_mobile_shell.py`:

```python
def test_mobile_declares_svg_dependency_for_forecast_graph() -> None:
    package_json = json.loads(
        (Path(__file__).resolve().parents[2] / "mobile" / "package.json").read_text()
    )

    assert "react-native-svg" in package_json["dependencies"]


def test_mobile_stock_detail_renders_forecast_graph_component() -> None:
    detail_source = (
        Path(__file__).resolve().parents[2]
        / "mobile"
        / "src"
        / "screens"
        / "StockDetailScreen.tsx"
    ).read_text()

    assert "ForecastGraph" in detail_source
    assert "Forecast graph unavailable" not in detail_source
    assert "selectedGraphType={selectedGraphType}" in detail_source
    assert "onChangeGraphType={onChangeGraphType}" in detail_source


def test_mobile_forecast_graph_exposes_required_visual_semantics() -> None:
    graph_source = (
        Path(__file__).resolve().parents[2]
        / "mobile"
        / "src"
        / "components"
        / "ForecastGraph.tsx"
    ).read_text()

    assert "react-native-svg" in graph_source
    assert "Forecast Graph" in graph_source
    assert "Historical" in graph_source
    assert "Forecast" in graph_source
    assert "Uncertainty range" in graph_source
    assert "strokeDasharray" in graph_source
    assert "Select Line Forecast Graph" in graph_source
    assert "Select Candlestick Forecast Graph" in graph_source
    assert "historicalPoints" in graph_source
    assert "linePoints" in graph_source
    assert "candlesticks" in graph_source
    assert "Forecast Graph data is unavailable" in graph_source
    assert "Historical context unavailable" in graph_source
```

- [ ] **Step 2: Run graph rendering static tests to verify they fail**

Run:

```bash
.venv/bin/python -m pytest backend/tests/test_mobile_shell.py::test_mobile_declares_svg_dependency_for_forecast_graph backend/tests/test_mobile_shell.py::test_mobile_stock_detail_renders_forecast_graph_component backend/tests/test_mobile_shell.py::test_mobile_forecast_graph_exposes_required_visual_semantics -v
```

Expected: FAIL until `ForecastGraph` exists and `StockDetailScreen` uses it. The dependency test should already pass if Task 2 installed `react-native-svg`.

- [ ] **Step 3: Create `ForecastGraph.tsx`**

Create `mobile/src/components/ForecastGraph.tsx` with this content:

```tsx
import { Pressable, StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Line, Path, Rect } from "react-native-svg";

import type {
  StockDetail,
  StockDetailForecastCandlestick,
  StockDetailForecastHistoricalPoint,
  StockDetailForecastLinePoint,
} from "../api/stocks";
import type { GraphType } from "../storage/graphType";

type GraphTypeOption = {
  value: GraphType;
  label: string;
};

type ChartPoint = {
  sequence: number;
  timestamp: string;
  value: number;
};

type ForecastGraphProps = {
  detail: StockDetail;
  graphTypeOptions: GraphTypeOption[];
  onChangeGraphType: (graphType: GraphType) => void;
  selectedGraphType: GraphType;
};

const CHART_WIDTH = 320;
const CHART_HEIGHT = 180;
const CHART_PADDING = 18;
const FORECAST_COLOR = "#60a5fa";
const HISTORICAL_COLOR = "#94a3b8";
const UNCERTAINTY_COLOR = "#93c5fd";
const DIVIDER_COLOR = "#facc15";

export function ForecastGraph({
  detail,
  graphTypeOptions,
  onChangeGraphType,
  selectedGraphType,
}: ForecastGraphProps) {
  const { forecast, horizonMetadata, stock } = detail;
  const historicalPoints = forecast.historicalPoints ?? [];
  const linePoints = forecast.linePoints ?? [];
  const candlesticks = forecast.candlesticks ?? [];
  const hasForecastData = selectedGraphType === "candlestick" ? candlesticks.length > 0 : linePoints.length > 0;

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View>
          <Text style={styles.kicker}>Forecast Graph</Text>
          <Text style={styles.title}>
            {stock.ticker} {horizonMetadata.label} {selectedGraphType === "line" ? "Line" : "Candlestick"} Forecast
          </Text>
        </View>
        <View style={styles.segmentedControl}>
          {graphTypeOptions.map((option) => {
            const isSelected = option.value === selectedGraphType;

            return (
              <Pressable
                accessibilityLabel={`Select ${option.label} Forecast Graph`}
                accessibilityRole="button"
                accessibilityState={{ selected: isSelected }}
                key={option.value}
                onPress={() => onChangeGraphType(option.value)}
                style={[styles.segment, isSelected ? styles.segmentSelected : null]}
              >
                <Text style={[styles.segmentText, isSelected ? styles.segmentTextSelected : null]}>
                  {option.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {!hasForecastData ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>Forecast Graph data is unavailable</Text>
          <Text style={styles.emptyBody}>Graph data is unavailable for the selected horizon.</Text>
        </View>
      ) : (
        <View>
          <Svg height={CHART_HEIGHT} viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} width="100%">
            {selectedGraphType === "candlestick"
              ? renderCandlestickGraph(historicalPoints, candlesticks)
              : renderLineGraph(historicalPoints, linePoints)}
          </Svg>
          <View style={styles.legendRow}>
            <Text style={styles.legendHistorical}>
              {historicalPoints.length > 0 ? "Historical actual price" : "Historical context unavailable"}
            </Text>
            <Text style={styles.legendForecast}>Forecast</Text>
            <Text style={styles.legendUncertainty}>Uncertainty range</Text>
          </View>
          <Text style={styles.rangeCopy}>{getRangeCopy(historicalPoints, linePoints, candlesticks)}</Text>
        </View>
      )}
      <Text style={styles.freshness}>{forecast.freshnessLabel}</Text>
    </View>
  );
}

function renderLineGraph(
  historicalPoints: StockDetailForecastHistoricalPoint[],
  linePoints: StockDetailForecastLinePoint[],
) {
  const historicalChartPoints = historicalPoints.map((point) => ({
    sequence: point.sequence,
    timestamp: point.timestamp,
    value: point.value,
  }));
  const expectedPoints = linePoints.map((point) => ({
    sequence: point.sequence,
    timestamp: point.timestamp,
    value: point.expectedValue,
  }));
  const lowerPoints = linePoints.map((point) => ({
    sequence: point.sequence,
    timestamp: point.timestamp,
    value: point.lowerBound,
  }));
  const upperPoints = linePoints.map((point) => ({
    sequence: point.sequence,
    timestamp: point.timestamp,
    value: point.upperBound,
  }));
  const scale = createScale([
    ...historicalChartPoints,
    ...expectedPoints,
    ...lowerPoints,
    ...upperPoints,
  ]);
  const forecastStartX = scale.x(historicalChartPoints.length);

  return (
    <>
      <Line x1={forecastStartX} x2={forecastStartX} y1={8} y2={CHART_HEIGHT - 8} stroke={DIVIDER_COLOR} strokeWidth={2} />
      {historicalChartPoints.length > 1 ? (
        <Path d={toPath(historicalChartPoints, scale, 0)} fill="none" stroke={HISTORICAL_COLOR} strokeWidth={3} />
      ) : null}
      <Path d={toPath(expectedPoints, scale, historicalChartPoints.length)} fill="none" stroke={FORECAST_COLOR} strokeWidth={3} />
      <Path d={toPath(upperPoints, scale, historicalChartPoints.length)} fill="none" stroke={UNCERTAINTY_COLOR} strokeDasharray="6 6" strokeWidth={2} />
      <Path d={toPath(lowerPoints, scale, historicalChartPoints.length)} fill="none" stroke={UNCERTAINTY_COLOR} strokeDasharray="6 6" strokeWidth={2} />
      {expectedPoints.map((point, index) => (
        <Circle cx={scale.x(index + historicalChartPoints.length)} cy={scale.y(point.value)} fill={FORECAST_COLOR} key={`${point.timestamp}-${point.sequence}`} r={3} />
      ))}
    </>
  );
}

function renderCandlestickGraph(
  historicalPoints: StockDetailForecastHistoricalPoint[],
  candlesticks: StockDetailForecastCandlestick[],
) {
  const historicalChartPoints = historicalPoints.map((point) => ({
    sequence: point.sequence,
    timestamp: point.timestamp,
    value: point.value,
  }));
  const candleValues = candlesticks.flatMap((candlestick) => [
    { sequence: candlestick.sequence, timestamp: candlestick.timestamp, value: candlestick.open },
    { sequence: candlestick.sequence, timestamp: candlestick.timestamp, value: candlestick.high },
    { sequence: candlestick.sequence, timestamp: candlestick.timestamp, value: candlestick.low },
    { sequence: candlestick.sequence, timestamp: candlestick.timestamp, value: candlestick.close },
  ]);
  const scale = createScale([...historicalChartPoints, ...candleValues]);
  const forecastStartX = scale.x(historicalChartPoints.length);
  const candleWidth = Math.max(5, Math.min(14, CHART_WIDTH / Math.max(candlesticks.length + historicalChartPoints.length, 1) / 2));

  return (
    <>
      <Line x1={forecastStartX} x2={forecastStartX} y1={8} y2={CHART_HEIGHT - 8} stroke={DIVIDER_COLOR} strokeWidth={2} />
      {historicalChartPoints.length > 1 ? (
        <Path d={toPath(historicalChartPoints, scale, 0)} fill="none" stroke={HISTORICAL_COLOR} strokeWidth={3} />
      ) : null}
      {candlesticks.map((candlestick, index) => {
        const x = scale.x(index + historicalChartPoints.length);
        const openY = scale.y(candlestick.open);
        const closeY = scale.y(candlestick.close);
        const highY = scale.y(candlestick.high);
        const lowY = scale.y(candlestick.low);
        const isBullish = candlestick.close >= candlestick.open;
        const color = isBullish ? "#86efac" : "#fca5a5";

        return (
          <React.Fragment key={`${candlestick.timestamp}-${candlestick.sequence}`}>
            <Line x1={x} x2={x} y1={highY} y2={lowY} stroke={color} strokeWidth={2} />
            <Rect
              fill={color}
              height={Math.max(Math.abs(closeY - openY), 3)}
              rx={2}
              width={candleWidth}
              x={x - candleWidth / 2}
              y={Math.min(openY, closeY)}
            />
          </React.Fragment>
        );
      })}
    </>
  );
}

function createScale(points: ChartPoint[]) {
  const values = points.map((point) => point.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const range = maxValue - minValue || 1;
  const domainPadding = range * 0.08;
  const paddedMin = minValue - domainPadding;
  const paddedMax = maxValue + domainPadding;
  const paddedRange = paddedMax - paddedMin || 1;
  const maxIndex = Math.max(points.length - 1, 1);

  return {
    x: (index: number) => CHART_PADDING + (index / maxIndex) * (CHART_WIDTH - CHART_PADDING * 2),
    y: (value: number) => CHART_HEIGHT - CHART_PADDING - ((value - paddedMin) / paddedRange) * (CHART_HEIGHT - CHART_PADDING * 2),
  };
}

function toPath(points: ChartPoint[], scale: ReturnType<typeof createScale>, offset: number): string {
  return points
    .map((point, index) => `${index === 0 ? "M" : "L"}${scale.x(index + offset)} ${scale.y(point.value)}`)
    .join(" ");
}

function getRangeCopy(
  historicalPoints: StockDetailForecastHistoricalPoint[],
  linePoints: StockDetailForecastLinePoint[],
  candlesticks: StockDetailForecastCandlestick[],
): string {
  const values = [
    ...historicalPoints.map((point) => point.value),
    ...linePoints.flatMap((point) => [point.expectedValue, point.lowerBound, point.upperBound]),
    ...candlesticks.flatMap((candlestick) => [candlestick.open, candlestick.high, candlestick.low, candlestick.close]),
  ];
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);

  return `Actual price scale ${formatPrice(minValue)} to ${formatPrice(maxValue)}`;
}

function formatPrice(value: number): string {
  return `$${value.toFixed(2)}`;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#0f172a",
    borderRadius: 24,
    padding: 20,
  },
  header: {
    gap: 14,
  },
  kicker: {
    color: "#93c5fd",
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  title: {
    color: "#f8fafc",
    fontSize: 22,
    fontWeight: "900",
    marginTop: 6,
  },
  segmentedControl: {
    alignSelf: "flex-start",
    backgroundColor: "#1e293b",
    borderRadius: 999,
    flexDirection: "row",
    gap: 4,
    padding: 4,
  },
  segment: {
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  segmentSelected: {
    backgroundColor: "#60a5fa",
  },
  segmentText: {
    color: "#cbd5e1",
    fontSize: 12,
    fontWeight: "900",
  },
  segmentTextSelected: {
    color: "#082f49",
  },
  emptyState: {
    backgroundColor: "#1e293b",
    borderRadius: 18,
    marginTop: 16,
    padding: 18,
  },
  emptyTitle: {
    color: "#f8fafc",
    fontSize: 18,
    fontWeight: "900",
  },
  emptyBody: {
    color: "#cbd5e1",
    lineHeight: 20,
    marginTop: 8,
  },
  legendRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 8,
  },
  legendHistorical: {
    color: HISTORICAL_COLOR,
    fontSize: 12,
    fontWeight: "800",
  },
  legendForecast: {
    color: FORECAST_COLOR,
    fontSize: 12,
    fontWeight: "800",
  },
  legendUncertainty: {
    color: UNCERTAINTY_COLOR,
    fontSize: 12,
    fontWeight: "800",
  },
  rangeCopy: {
    color: "#cbd5e1",
    fontSize: 13,
    marginTop: 10,
  },
  freshness: {
    color: "#94a3b8",
    fontSize: 13,
    marginTop: 16,
  },
});
```

- [ ] **Step 4: Fix missing React fragment import**

The component uses `React.Fragment`, so update the first import line in `ForecastGraph.tsx` to:

```tsx
import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
```

Expected: `React.Fragment` is available for candlestick elements.

- [ ] **Step 5: Replace graph placeholder in `StockDetailScreen.tsx`**

In `mobile/src/screens/StockDetailScreen.tsx`, add the component import:

```typescript
import { ForecastGraph } from "../components/ForecastGraph";
```

Replace the unavailable graph card:

```tsx
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Forecast graph unavailable</Text>
          <Text style={styles.cardBody}>
            Forecast graph rendering comes later. Backend graph data is loaded for the {detail.horizonMetadata.label} horizon with {detail.horizonMetadata.expectedForecastPointCount} forecast points.
          </Text>
          <Text style={styles.cardFreshness}>{forecast.freshnessLabel}</Text>
        </View>
```

with:

```tsx
        <ForecastGraph
          detail={detail}
          graphTypeOptions={graphTypeOptions}
          onChangeGraphType={onChangeGraphType}
          selectedGraphType={selectedGraphType}
        />
```

The `const { forecast, market, prediction, stock } = detail;` destructure can become:

```typescript
  const { market, prediction, stock } = detail;
```

because `forecast` is no longer used directly in this screen.

- [ ] **Step 6: Run graph static tests and mobile typecheck**

Run:

```bash
.venv/bin/python -m pytest backend/tests/test_mobile_shell.py::test_mobile_declares_svg_dependency_for_forecast_graph backend/tests/test_mobile_shell.py::test_mobile_stock_detail_renders_forecast_graph_component backend/tests/test_mobile_shell.py::test_mobile_forecast_graph_exposes_required_visual_semantics -v
```

Expected: PASS.

Run:

```bash
cd mobile
npm run typecheck
```

Expected: PASS with no TypeScript errors.

- [ ] **Step 7: Commit ForecastGraph rendering**

Run:

```bash
git add backend/tests/test_mobile_shell.py mobile/src/components/ForecastGraph.tsx mobile/src/screens/StockDetailScreen.tsx
git commit -m "feat: render forecast graph card"
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

- [ ] **Step 3: Run mobile test script**

Run:

```bash
cd mobile
npm test
```

Expected: PASS. The TypeScript test build and Node tests complete successfully.

- [ ] **Step 4: Inspect generated-client drift**

Run:

```bash
git diff HEAD~3 -- mobile/src/api/generated
```

Expected: generated diff includes `StockDetailForecastHistoricalPoint`, adds `historicalPoints` to `StockDetailForecast`, and does not remove canonical `ForecastHorizon` values.

- [ ] **Step 5: Inspect dependency changes**

Run:

```bash
git diff HEAD~3 -- mobile/package.json mobile/package-lock.json
```

Expected: diff includes `react-native-svg` and no unrelated package churn beyond the lockfile entries required by npm.

- [ ] **Step 6: Inspect working tree**

Run:

```bash
git status --short --branch
```

Expected: clean working tree on `issue-8` after all task commits.

- [ ] **Step 7: Confirm acceptance criteria manually**

Check these facts before claiming completion:

```text
Single-stock actual prices: ForecastGraph scale uses actual historical `value`, forecast expected/lower/upper, and candlestick OHLC values.
Historical distinction: ForecastGraph labels historical actual price separately and uses muted gray styling plus a forecast divider.
Forecast distinction: ForecastGraph labels forecast data and uses bright forecast styling.
Line default: graphType storage default is `line`.
Candlestick selectable: graph type selector includes `Candlestick` and renders backend `forecast.candlesticks`.
Uncertainty visible: line mode renders dashed upper/lower uncertainty limits with `strokeDasharray`; candlestick mode uses high/low ranges.
Persistence: AsyncStorage key `trendwise.graphType` stores only `line` or `candlestick`.
Extended hours: no extended-hours movement is rendered.
Boundaries: no comparison graph, normalized movement graph, summaries, news, key-factor UI, or refresh jobs were added.
```

- [ ] **Step 8: If any files remain uncommitted, commit only intended implementation files**

Run:

```bash
git status --short
```

If intended implementation files remain, stage only those files and commit with an appropriate message. Do not stage local artifacts such as `.venv/`, `node_modules/`, `.pytest_cache/`, `backend/trendwise_backend.egg-info/`, `.superpowers/`, or unintended dependency churn.

- [ ] **Step 9: Prepare completion summary**

Report:

```text
Implemented issue #8 on branch issue-8.
Backend verification: .venv/bin/python -m pytest -v -> pass count from output.
Mobile verification: npm run typecheck -> passed; npm test -> passed.
Key changes: Stock Detail historicalPoints contract, generated mobile client update, react-native-svg graph card, persisted graph type selector.
Deferred by design: comparison graph, normalized movement graph, summary/news/key-factor UI, refresh jobs, extended-hours rendering.
```
