# Stock Search And Select Design

## Goal

Build issue #2: let a mobile user search supported US-listed common Stocks, select exactly one primary Stock, cache that selection locally, and relaunch into the cached Stock Detail path.

## Scope

In scope:

- Backend supported Stock search endpoint backed by the seeded `supported_stocks` table.
- Generated TypeScript API types/client from FastAPI OpenAPI for mobile use.
- First-launch Stock Search screen when no cached primary Stock exists.
- Fixed example Stock chips before search input, labeled as examples rather than popularity or recommendation.
- Local persistence of the selected primary Stock.
- Stock Detail placeholder route/state for the selected primary Stock.

Out of scope:

- Forecasts, Stock Predictions, summaries, news, graph data, and market snapshots.
- Popularity ranking, personalized recommendations, or buy/sell/hold language.
- Full navigation library adoption unless the current implementation requires it.
- Unsupported-instrument request workflows beyond excluding unsupported records from search results.

## Architecture

Use a thin vertical slice with small structured modules.

Backend:

- `app/stocks/router.py` owns HTTP routes under `/stocks`.
- `app/stocks/repository.py` owns SQL for reading `supported_stocks`.
- `app/stocks/schemas.py` owns Pydantic response model classes.
- `app/main.py` registers the stock router.

Mobile:

- `mobile/src/api/generated/` stores generated OpenAPI client/types, including generated TypeScript model types for the backend Pydantic response models.
- `mobile/src/api/stocks.ts` wraps generated stock-search calls with the backend base URL.
- `mobile/src/storage/primaryStock.ts` reads/writes the cached primary Stock.
- `mobile/src/screens/StockSearchScreen.tsx` renders search input, example chips, loading/error/empty states, and search results.
- `mobile/src/screens/StockDetailPlaceholderScreen.tsx` renders selected Stock identity and a clear placeholder message.
- `mobile/App.tsx` coordinates first-load cache hydration and screen switching.

## Backend API

Expose:

```http
GET /stocks/search?q={query}
```

Response:

```json
{
  "results": [
    {
      "ticker": "AAPL",
      "companyName": "Apple Inc.",
      "exchange": "NASDAQ"
    }
  ]
}
```

Backend model classes:

```python
class StockSearchResult(BaseModel):
    ticker: str
    company_name: str = Field(serialization_alias="companyName")
    exchange: str


class StockSearchResponse(BaseModel):
    results: list[StockSearchResult]
```

Behavior:

- If `q` is empty or whitespace, return a fixed examples list from supported seeded Stocks.
- If `q` is non-empty, match case-insensitively against `search_text`.
- Return only rows where `is_supported = true`.
- Limit results to 10.
- Sort exact ticker matches first, then ticker prefix matches, then company/exchange matches by ticker.
- Unsupported ETFs, OTC securities, warrants, preferred shares, funds, delisted symbols, and non-US exchanges remain absent because the seeder only inserts supported US common Stocks.

## Examples List

The UI label is `Examples`, not `Popular`, `Recommended`, or `Top`.

The examples are deterministic and come from the backend by calling the same endpoint with an empty query. The backend returns a fixed ticker order from supported seeded data, for example:

```text
AAPL, MSFT, NVDA, TSLA
```

If any example ticker is absent from the database, the backend skips it rather than fabricating data.

## Mobile Flow

On app start:

1. Load cached primary Stock from local storage.
2. If present, render Stock Detail placeholder.
3. If absent, render Stock Search.

On Stock Search:

- Show title `Start with a supported Stock`.
- Show input placeholder `Search ticker or company`.
- Show `Examples` chips before typing.
- When the user types, call `/stocks/search?q=...`.
- Render result rows with ticker, company name, and exchange.
- If there are no results, explain that only supported US-listed common Stocks are searchable.
- If the request fails, show a retryable error message.

On selection:

1. Store `{ ticker, companyName, exchange }` locally as the primary Stock.
2. Render Stock Detail placeholder.

On Stock Detail placeholder:

- Show ticker, company name, and exchange.
- Show message: `Forecasts and predictions are not available yet.`
- Show informational disclaimer: `Trendwise is informational only and does not provide trading recommendations.`
- Provide a `Change Stock` action that clears or replaces the selected Stock by returning to Stock Search.

## Generated API Contract

Mobile must use generated TypeScript types/client code from FastAPI OpenAPI. The generated TypeScript models are the frontend representation of the backend Pydantic model classes; mobile code must import those generated models instead of redefining stock search response shapes by hand.

Implementation must add a Docker-first script command that:

1. Starts or runs the backend OpenAPI export inside Docker.
2. Generates TypeScript client/types into `mobile/src/api/generated/`.
3. Can be repeated locally without manual file copying.

The handwritten mobile stock API wrapper must import generated model types instead of redefining backend response shapes. It should not add TypeScript class wrappers around the generated models unless a later issue has a concrete need.

## Error Handling

Backend:

- Database connection failures return normal FastAPI `500` behavior for now.
- Empty or whitespace query is valid and returns examples.
- Search SQL uses parameters, not string interpolation.

Mobile:

- Cache read failure falls back to Stock Search.
- Cache write failure keeps the user on Stock Search and shows an error.
- Search failure displays a concise message and keeps the input intact.
- Empty search results are not an error.

## Testing

Backend tests:

- Search endpoint returns supported ticker matches.
- Search endpoint returns supported company-name matches.
- Search endpoint excludes unsupported rows.
- Empty query returns fixed examples from rows present in the database.
- Search result order prioritizes exact and prefix ticker matches.

Mobile/type tests:

- TypeScript check passes through Docker.
- Generated API model types are imported by the handwritten stock API wrapper.
- App state types cover `loading`, `search`, and `detail` states.

Script tests:

- `./scripts/dev` exposes the OpenAPI generation command in help text.
- Docker Compose includes the one-shot service used by the generation command.

## Acceptance Criteria Mapping

- Stock Search opens on first launch when no cached primary Stock exists: mobile startup cache branch.
- Search supports ticker and company-name matching for supported US-listed common Stocks only: backend search endpoint and repository tests.
- Unsupported ETFs, OTC securities, warrants, preferred shares, funds, delisted symbols, and non-US exchanges are excluded or clearly rejected: seeder filtering plus search-only supported rows and empty-state copy.
- Selecting a primary Stock stores it locally and navigates to the Stock Detail path: mobile selection handler and cached Stock storage.
- Relaunch opens the cached primary Stock when present: mobile startup cache hydration.
- Mobile uses generated TypeScript API types/client code from FastAPI OpenAPI: generated client folder, wrapper imports, and Docker generation script.

## Self Review

- Placeholder scan: no TBD/TODO placeholders remain.
- Internal consistency: endpoint, response names, mobile storage shape, and generated type usage match across sections.
- Scope check: focused on one vertical slice for issue #2; later forecast/detail work remains out of scope.
- Ambiguity check: “Examples” explicitly avoids popularity, ranking, and recommendation semantics.
