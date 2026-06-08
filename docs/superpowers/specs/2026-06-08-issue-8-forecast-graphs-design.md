# Issue 8: Line And Candlestick Forecast Graphs Design

## Context

Issue 8 renders Forecast Graphs for a single Stock on the mobile Stock Detail screen. Issue 6 already added backend line forecast points and Candlestick Forecast data. Issue 7 added Forecast Horizon selection and metadata. This issue turns that contract into a visible graph with a persisted graph type preference.

The graph must use actual Stock price values for single-stock detail. It must not normalize values, because normalized comparison movement is reserved for later Stock Comparison work.

## Scope

Build a single-stock Forecast Graph for the selected Forecast Horizon.

The graph supports:

- Line Forecast as the first-use default.
- Candlestick Forecast as a selectable graph type.
- Local graph type persistence across app restarts.
- Historical actual-price context before the forecast segment.
- A visually distinct forecast segment.
- Visible uncertainty through dashed line limits in Line Forecast mode and OHLC high/low ranges in Candlestick Forecast mode.

This issue omits extended-hours movement in the prototype. Extended-hours data must not be shown unless a later issue adds a distinct label and visual style.

## Recommended Approach

Use `react-native-svg` plus custom graph components.

This adds one rendering dependency while keeping chart semantics under product control. It supports custom line paths, dashed uncertainty limits, forecast boundary markers, and Candlestick Forecast rendering without depending on a high-level chart library whose defaults may hide the historical/forecast distinction.

Rejected alternatives:

- A higher-level chart library would be faster for a basic line chart but weaker for custom Forecast Graph semantics and candlestick uncertainty display.
- Plain React Native `View` rendering would avoid a dependency but makes accurate paths, dashed bounds, and candlesticks awkward.

## Backend Contract

Extend the Stock Detail forecast payload with a minimal historical graph series, serialized as `historicalPoints`.

Each historical graph point must include:

- `sequence`: integer ordering within the historical segment.
- `timestamp`: UTC timestamp string.
- `value`: actual observed price value.

Historical points must represent actual price values. They must be sourced from stored Market Snapshots or historical price data already available through the Stock Detail repository and seed path. The prototype uses regular-session values only.

The existing forecast fields remain:

- `forecast.linePoints`: expected value, lower bound, upper bound, timestamp, sequence.
- `forecast.candlesticks`: open, high, low, close, timestamp, sequence.

The backend does not add new forecast model logic in this issue. It only exposes historical context needed for honest graph rendering.

## Mobile Data Flow

Add `mobile/src/storage/graphType.ts` as the graph type preference module.

The module should define:

- AsyncStorage key `trendwise.graphType`.
- Supported values: `line` and `candlestick`.
- Default graph type: `line`.
- A validator that rejects unsupported values and falls back to `line`.
- `loadGraphType` and `saveGraphType` functions.

`App.tsx` should load graph type preference during startup alongside primary Stock and Forecast Horizon. It should keep selected graph type in state and pass it to `StockDetailScreen`.

Changing graph type should:

- Update UI state immediately.
- Save the local preference.
- Not call the backend.
- Not change the selected Forecast Horizon.

Forecast Horizon changes continue to reload Stock Detail from the backend. Graph type only changes how the existing Stock Detail forecast payload is rendered.

## Mobile Components

Create `mobile/src/components/ForecastGraph.tsx` as the graph card boundary.

`ForecastGraph` should receive:

- The selected Stock Detail data needed for graph rendering.
- The selected graph type.
- A focused `onChangeGraphType` callback.

Keep chart math in small local helper functions inside `ForecastGraph.tsx` unless the file becomes hard to follow. Helpers should normalize screen coordinates from actual price values, not normalized comparison movement.

`StockDetailScreen` should replace the current “Forecast graph unavailable” card with `ForecastGraph`.

## Visual Design

Use a focused dark Forecast Graph card.

Header:

- Title identifies the selected Forecast Horizon and graph type.
- A segmented selector sits inside the graph card for `Line` and `Candlestick`.

Line Forecast body:

- Historical actual prices render in muted gray.
- Forecast expected values render in bright blue.
- Upper and lower uncertainty limits render as dashed blue lines.
- A vertical divider marks where forecast output begins.
- Text labels distinguish `Historical` and `Forecast`.

Candlestick Forecast body:

- Forecast candles use backend-provided OHLC values.
- Historical context remains visually distinct and must not look like model output.
- Bullish and bearish candle colors must have enough contrast against the dark card.
- The forecast-start divider remains visible.

Scale and labels:

- Use actual price values on one shared y-axis across historical and forecast values.
- Include compact min/max or range copy so users can understand the price scale without a full production chart axis.
- Do not show normalized percentages in single-stock detail.

## Error Handling

If the selected graph type has no forecast array data, show a graph-card empty state that says Forecast Graph data is unavailable for the selected horizon. Do not use the legacy `forecast.status` string alone to hide graph data when forecast arrays are present.

If historical context is missing but forecast data exists, render the forecast segment and explicitly label historical context as unavailable. Do not fabricate historical points from forecast values.

If graph type preference loading fails, fall back to `line`.

If graph type preference saving fails, keep the selected UI state and surface a detail error using the existing error pattern.

## Testing

Backend tests should cover:

- Stock Detail response includes `forecast.historicalPoints` with actual price values.
- Historical points are ordered and distinct from forecast line points.
- Default and explicit Forecast Horizon detail responses include historical graph context when available.
- Generated OpenAPI includes the historical point model.

Mobile/static tests should cover:

- `react-native-svg` is declared as a dependency.
- Graph type storage declares key `trendwise.graphType`, default `line`, valid values `line` and `candlestick`, and fallback validation.
- `App.tsx` loads and saves graph type preference.
- `StockDetailScreen` renders `ForecastGraph` instead of the unavailable placeholder.
- `ForecastGraph` exposes the graph type selector with accessible labels.
- `ForecastGraph` includes labels or copy for historical data, forecast data, and uncertainty range.

Verification should include:

- Backend test suite or targeted backend tests for Stock Detail contract.
- Generated mobile API client regeneration after backend schema changes.
- Mobile TypeScript typecheck.

## Acceptance Mapping

- Single-stock graph uses actual price values rather than normalized comparison movement: covered by shared actual-price y-axis and historical point contract.
- Historical and forecasted values are visually distinct: covered by muted historical styling, bright forecast styling, and forecast-start divider.
- Line Forecast is the default graph type on first use: covered by `graphType` storage default.
- Candlestick Forecast can be selected and uses backend-provided derived OHLC forecast data: covered by graph type selector and `forecast.candlesticks` rendering.
- Forecast uncertainty is visible through expected values and uncertainty ranges: covered by dashed upper/lower bounds in Line Forecast mode and high/low OHLC ranges in Candlestick Forecast mode.
- Graph type preference persists locally across app restarts: covered by AsyncStorage graph type module and app startup hydration.
- Extended-hours movement is shown only if visually distinct and labeled, or omitted from the prototype: covered by explicitly omitting extended-hours movement in this issue.

## Non-Goals

- No Stock Comparison graph.
- No normalized movement graph.
- No new backend forecast model logic.
- No Stock Summary, Company News, or Key Factor UI.
- No live refresh jobs.
- No extended-hours rendering.
