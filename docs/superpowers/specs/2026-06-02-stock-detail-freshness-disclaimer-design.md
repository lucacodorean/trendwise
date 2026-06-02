# Stock Detail Freshness And Disclaimer Design

## Issue

Issue 3: Render single-Stock detail with freshness and disclaimer.

## Goal

Deliver the first repository-backed single Stock Detail vertical slice. A selected supported Stock should open a mobile detail screen showing identity, latest price context, freshness labels, a compact informational disclaimer, a Stock Prediction card, and a forecast-unavailable placeholder.

The feature must not use buy, sell, or hold recommendation language. Stock Predictions are analytical signals only.

## Scope

Included:

- Combined backend stock-detail endpoint for one primary Stock and one Forecast Horizon.
- Forecast Horizon validation backed by an explicit canonical enum or allowlist.
- Repository-backed detail data with local seeded fallback rows for supported example stocks.
- Mobile Stock Detail screen using a price-forward Hero Summary layout.
- Freshness labels for market data, forecast, and prediction.
- Compact disclaimer that states outputs are estimates, not financial advice or trading recommendations.
- Forecast section placeholder with an unavailable state, not a graph.

Excluded:

- Forecast graph rendering.
- Company News and Stock Summary sections.
- Comparison Stocks.
- Provider adapters and ML-generated predictions.
- Full persistence foundation for every future domain record.

## Backend API

Add a combined detail endpoint under the existing stocks router:

```http
GET /stocks/{ticker}/detail?horizon=1d
```

The endpoint validates that `{ticker}` is a supported Stock and that `horizon` is one of the canonical Forecast Horizons:

- `30m`
- `1d`
- `5d`
- `7d`
- `1mo`
- `6mo`
- `1y`

The default horizon is `1d`. Invalid values such as `1M`, `30M`, `2d`, empty strings, or arbitrary text return a validation error before repository lookup.

The response is optimized for the mobile Stock Detail screen and includes:

- `stock`: ticker, company name, and exchange.
- `horizon`: selected Forecast Horizon.
- `market`: latest price, daily change amount, daily change percent, timestamp, and freshness label.
- `prediction`: direction, confidence, expected change, Risk Level, timestamp, and freshness label.
- `forecast`: status, timestamp, and freshness label. For this issue, status is `unavailable`.
- `disclaimer`: compact no-advice disclaimer text.

Prediction direction values are limited to `bullish`, `bearish`, and `neutral`. Risk Level values are limited to `low`, `medium`, and `high`.

## Persistence And Seed Data

Keep persistence scoped to issue 3. Add only the repository-backed records needed to serve the detail response:

- Supported Stock identity is read from the existing `supported_stocks` table.
- Market detail rows store latest price, daily change amount, daily change percent, and observed timestamp.
- Forecast detail rows store selected horizon, unavailable status, and freshness timestamp.
- Prediction detail rows store selected horizon, direction, confidence, expected change, Risk Level, and generated timestamp.

Seeders create local detail rows for example supported stocks so the selected examples render immediately during local development. If a supported Stock has no detail rows, the endpoint returns the Stock identity plus unavailable market, forecast, and prediction sections instead of inventing unstored values.

## Mobile UI

Replace the placeholder Stock Detail screen with a real detail screen using the Hero Summary layout:

- A large price-forward hero card shows exchange, ticker, company name, latest price, daily change, market freshness, and the `Change Stock` action.
- Compact metric cards show direction and Risk Level, followed by a prediction section with confidence, expected change, selected horizon, and prediction freshness.
- Forecast and prediction freshness labels are visible near the prediction and forecast sections.
- The disclaimer is visible and compact.
- The forecast section renders an unavailable placeholder, not a graph.

The app fetches detail data after selecting a Stock and after hydrating a cached primary Stock. Loading state is a simple spinner. If detail loading fails, the screen shows an error message and keeps the `Change Stock` action available.

## Data Flow

1. User searches for and selects a supported primary Stock.
2. Mobile saves the primary Stock and enters detail mode.
3. Detail mode calls `GET /stocks/{ticker}/detail?horizon=1d`.
4. Backend validates ticker support and Forecast Horizon.
5. Repository reads seeded detail rows and builds the combined response.
6. Mobile renders the Hero Summary Stock Detail screen from generated API client types.

The same fetch happens when the app hydrates a cached primary Stock at startup.

## Error Handling

- Unsupported ticker returns a client error, expected as `404`.
- Invalid Forecast Horizon returns a FastAPI/Pydantic validation error, expected as `422`.
- Missing detail data for a supported Stock is represented with unavailable market, forecast, and prediction sections.
- Network or API failure on mobile shows a concise detail error and preserves the ability to change the selected Stock.
- API and UI copy must not contain buy, sell, or hold recommendation language.

## Testing

Backend tests:

- Successful seeded detail response for a supported stock and default horizon.
- Successful detail response for an explicit valid horizon.
- Invalid horizon rejection for values such as `1M`, `30M`, and `2d`.
- Unsupported ticker error.
- Response prediction direction is limited to `bullish`, `bearish`, or `neutral`.
- Response copy does not include buy, sell, or hold language.
- Freshness fields are present for market data, forecast, and prediction.
- Seeder/repository tests prove local fallback rows are stored and retrieved.

Mobile tests/checks:

- TypeScript typecheck passes with generated API types.
- Detail fetch path compiles and renders the required fields.
- Existing search and selection behavior remains intact.

## OpenAPI And Generated Client

The backend OpenAPI schema should include the stock-detail endpoint and schemas. After backend changes, regenerate the mobile API client so the Stock Detail screen consumes generated response types rather than handwritten API shapes where practical.

## Acceptance Criteria Mapping

- Combined stock-detail endpoint: covered by `GET /stocks/{ticker}/detail?horizon=1d`.
- Identity, price, and daily change: covered by `stock` and `market` response sections and Hero Summary UI.
- Freshness labels: covered by market, forecast, and prediction freshness fields.
- Disclaimer: backend-provided disclaimer rendered in the UI.
- Prediction card: covered by direction, confidence, expected change, and Risk Level fields.
- No recommendation language: covered by API/UI copy constraints and tests.
