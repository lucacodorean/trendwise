# Issue 7: Forecast Horizons End To End Design

## Summary

Issue #7 makes Forecast Horizon selection an end-to-end product behavior across backend validation, Stock Detail contract data, and mobile preference state. The selected Forecast Horizon becomes the shared input that drives the Stock Detail response sections for graph data, Stock Prediction, Key Factors, and future Stock Summary or Company News consumers.

This design uses the existing canonical horizon enum introduced during issue #6 and adds explicit horizon metadata plus a mobile selector. It does not implement the full Forecast Graph UI, visible Stock Summary UI, Company News cards, Key Factor presentation, refresh jobs, or live Yahoo orchestration.

## Current Context

- `backend/app/forecasts/models.py` already defines canonical `ForecastHorizon` values: `30m`, `1d`, `5d`, `7d`, `1mo`, `6mo`, and `1y`.
- `backend/app/stocks/router.py` already defaults Stock Detail to `ForecastHorizon.one_day` and lets FastAPI reject unsupported enum values before repository lookup.
- `backend/app/forecasts/baseline.py` already generates line points, candlesticks, predictions, and key factor inputs for every canonical horizon.
- `mobile/src/api/generated/models/ForecastHorizon.ts` already contains the strict generated TypeScript union.
- `mobile/App.tsx` currently always loads Stock Detail with `"1d"`.
- `mobile/src/screens/StockDetailScreen.tsx` currently shows the selected horizon as static text and does not let the user change it.
- `mobile/src/storage/primaryStock.ts` already provides an AsyncStorage pattern for persisted local preference state.

## Scope

### In Scope

- Keep allowed Forecast Horizons exactly `30m`, `1d`, `5d`, `7d`, `1mo`, `6mo`, and `1y`.
- Keep default Forecast Horizon as `1d`.
- Reject ambiguous or unsupported values such as `1M`, `30M`, and `2d`.
- Add backend horizon metadata that describes each horizon's interpretation for graph, summary/news, and External Factor consumers.
- Include the requested horizon metadata in the Stock Detail API response.
- Regenerate OpenAPI and mobile generated client files after the response shape changes.
- Add a mobile Forecast Horizon selector on Stock Detail.
- Persist the user's last selected Forecast Horizon locally.
- Reload Stock Detail with the selected horizon when the selector changes.
- Preserve one selected Forecast Horizon as the shared input for graph data, prediction data, key factor inputs, and future summary/news inputs.

### Out Of Scope

- Full Forecast Graph rendering. That remains issue #8.
- Full Stock Summary, Company News, and Key Factor UI. That remains issue #9.
- Background refresh jobs, tracked Stock rules, admin CLI, and live orchestration. That remains issue #12.
- Comparison Stock behavior. This issue only affects the current single-Stock Detail flow.
- New database tables or migrations. Horizon metadata is deterministic contract data, not persisted state.

## Backend Design

### Horizon Metadata Module

Add a focused backend module for Forecast Horizon interpretation, for example `backend/app/forecasts/horizons.py`. It should depend on `ForecastHorizon` from `backend/app/forecasts/models.py` and expose one lookup function.

The metadata shape should include:

- `value`: the canonical horizon value.
- `label`: readable display label.
- `time_basis`: `regular_market` or `calendar_period`.
- `price_point_basis`: always `trading_session` for this prototype.
- `news_window_days`: deterministic window for future Stock Summary and Company News consumers.
- `external_factor_weight_scale`: deterministic multiplier for future External Factor weighting.
- `expected_forecast_point_count`: expected baseline graph point count for the horizon.

Recommended metadata values:

| Horizon | Label | Time Basis | Price Point Basis | News Window Days | Factor Weight Scale | Expected Point Count |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `30m` | `30 min` | `regular_market` | `trading_session` | 1 | 1.25 | 6 |
| `1d` | `1 day` | `regular_market` | `trading_session` | 3 | 1.15 | 8 |
| `5d` | `5 days` | `regular_market` | `trading_session` | 7 | 1.00 | 5 |
| `7d` | `7 days` | `calendar_period` | `trading_session` | 10 | 0.95 | 7 |
| `1mo` | `1 month` | `calendar_period` | `trading_session` | 30 | 0.85 | 10 |
| `6mo` | `6 months` | `calendar_period` | `trading_session` | 90 | 0.70 | 12 |
| `1y` | `1 year` | `calendar_period` | `trading_session` | 180 | 0.60 | 12 |

`30m`, `1d`, and `5d` are interpreted through regular-market trading time where required. `7d`, `1mo`, `6mo`, and `1y` are interpreted as calendar periods, while their price points are still represented through trading sessions.

### Stock Detail Contract

Extend `StockDetailResponse` with a `horizon_metadata` field serialized as `horizonMetadata` in JSON. The existing `horizon` field remains as the selected canonical enum value.

Example response fragment:

```json
{
  "horizon": "1d",
  "horizonMetadata": {
    "value": "1d",
    "label": "1 day",
    "timeBasis": "regular_market",
    "pricePointBasis": "trading_session",
    "newsWindowDays": 3,
    "externalFactorWeightScale": 1.15,
    "expectedForecastPointCount": 8
  }
}
```

The router should derive metadata from the validated enum value and include it in every successful Stock Detail response. Repository behavior should stay unchanged: `repository.get_detail(ticker, horizon.value)` still filters forecast and prediction rows by selected horizon.

### Validation

No compatibility aliases should be added. Inputs such as `1M`, `30M`, `2d`, empty strings, and arbitrary text should remain invalid and should fail before repository lookup.

## Mobile Design

### Forecast Horizon Preference Storage

Add a mobile storage module parallel to `mobile/src/storage/primaryStock.ts`, for example `mobile/src/storage/forecastHorizon.ts`.

It should:

- Use AsyncStorage key `trendwise.forecastHorizon`.
- Return `"1d"` when no valid cached horizon exists.
- Validate cached strings against the generated `ForecastHorizon` union values.
- Ignore malformed JSON, unsupported strings, and non-string values by falling back to `"1d"`.
- Save only canonical `ForecastHorizon` values.

### App State And Data Flow

`mobile/App.tsx` should track the selected Forecast Horizon in state.

Startup flow:

1. Load cached primary Stock.
2. Load cached Forecast Horizon.
3. If a primary Stock exists, load Stock Detail using the cached horizon.
4. If no primary Stock exists, show Stock Search while retaining the cached horizon for the next detail load.

Selection flow:

1. User chooses a Stock.
2. Save the primary Stock.
3. Load Stock Detail using the current selected Forecast Horizon.

Horizon change flow:

1. User taps a horizon chip.
2. If the value is already selected, do nothing.
3. Save the selected Forecast Horizon.
4. Reload Stock Detail for the current Stock with the new Forecast Horizon.
5. Keep the selected horizon visible if the reload fails and show the existing detail error state.

This ensures graph data, prediction data, key factors, and future summary/news inputs all change together because the backend returns one Stock Detail payload for the selected horizon.

### Stock Detail Selector UI

Replace the static selected-horizon card in `mobile/src/screens/StockDetailScreen.tsx` with selectable horizon chips.

The screen should receive:

- `selectedHorizon: ForecastHorizon`.
- `horizonOptions`: list of canonical values and labels, preferably derived from backend metadata when available or from a local constant matching the generated union.
- `onChangeHorizon(horizon: ForecastHorizon): void`.

The selector should:

- Show all canonical horizons.
- Visually distinguish the selected chip.
- Sit near the top of Stock Detail before prediction metrics.
- Use readable labels while preserving canonical values in accessibility labels or supporting text.
- Keep the existing graph-unavailable card and mention that graph data is loaded for the selected horizon.

## OpenAPI And Generated Client

Because Stock Detail response shape changes, regenerate the OpenAPI document and generated mobile TypeScript client files using the repo's existing generation path.

Generated files expected to change include:

- `mobile/src/api/generated/openapi.json`
- `mobile/src/api/generated/models/StockDetailResponse.ts`
- A new generated model for horizon metadata, depending on codegen output.
- `mobile/src/api/generated/index.ts`

The generated `ForecastHorizon` union should remain exactly `"30m" | "1d" | "5d" | "7d" | "1mo" | "6mo" | "1y"`.

## Testing Strategy

### Backend Tests

Add or update tests to prove:

- The metadata lookup covers all and only canonical horizons.
- `30m`, `1d`, and `5d` have `time_basis="regular_market"`.
- `7d`, `1mo`, `6mo`, and `1y` have `time_basis="calendar_period"`.
- All horizons have `price_point_basis="trading_session"`.
- Metadata expected point counts match baseline generator output counts.
- Stock Detail default response includes `horizonMetadata` for `1d`.
- Stock Detail explicit horizon response includes matching metadata for the requested horizon.
- Invalid horizons such as `1M`, `30M`, and `2d` return `422` before repository lookup.

### Mobile Tests And Checks

Use the lightest test approach consistent with current repo patterns:

- Add backend-style static tests if there is no mobile test runner configured.
- Verify the Forecast Horizon storage module defines the canonical values and default fallback.
- Verify `App.tsx` no longer hardcodes `"1d"` for every detail load.
- Verify `StockDetailScreen.tsx` exposes selectable horizon controls.
- Run `npm run typecheck` to prove TypeScript wiring works with generated API types.

### Verification Commands

Run these before completion:

```bash
.venv/bin/python -m pytest -v
```

```bash
npm run typecheck
```

## Acceptance Criteria Mapping

- Allowed Forecast Horizons are exactly `30m`, `1d`, `5d`, `7d`, `1mo`, `6mo`, and `1y`: covered by existing enum plus metadata coverage tests.
- Ambiguous or unsupported values such as `1M`, `30M`, and `2d` are rejected: covered by API validation tests.
- Default Forecast Horizon is `1d`: covered by existing route default plus response metadata tests.
- `30m`, `1d`, and `5d` use regular-market trading time where required: covered by horizon metadata.
- `7d`, `1mo`, `6mo`, and `1y` use calendar periods represented through trading-session price points: covered by horizon metadata.
- Changing Forecast Horizon updates graph, prediction, summary inputs, news window, and External Factor weighting together: covered by Stock Detail reload flow and backend metadata contract. Full graph and summary/news UI rendering remain in #8 and #9.
- Mobile persists the last selected Forecast Horizon locally: covered by AsyncStorage preference module and mobile app flow.

## Risks And Mitigations

- Risk: Issue #7 expands into graph and summary/news UI. Mitigation: keep #7 to selector plus contract; leave full rendering to #8 and #9.
- Risk: Metadata diverges from baseline generator point counts. Mitigation: add tests comparing metadata counts with `HORIZON_STEPS` output counts.
- Risk: Mobile local constants drift from backend metadata. Mitigation: generated `ForecastHorizon` remains the type boundary, and labels can be local only for display until a dedicated horizon-options endpoint exists.
- Risk: `npm install` rewrites lockfile optional peer entries under local npm. Mitigation: avoid using `npm install` as an implementation step unless dependency changes require it; use existing `node_modules` and restore unintended lockfile churn.

## Implementation Boundaries

This issue should complete with a working mobile horizon selector and a backend Stock Detail contract ready for follow-up issue work. It should not claim that Forecast Graphs, Stock Summaries, Company News rendering, or live refresh jobs are complete.
