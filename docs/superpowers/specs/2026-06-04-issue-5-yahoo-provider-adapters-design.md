# Issue 5 Yahoo Provider Adapters Design

## Goal

Add replaceable provider seams for market data, Company News, and summary generation, with Yahoo Finance as the prototype market/news provider.

This design implements issue #5 only. It returns normalized provider data that future ingestion jobs can persist. It does not add persistence writes, refresh jobs, route fallback behavior, or summary generation logic beyond the interface seam.

## Architecture

Create a new `backend/app/providers/` module for provider interfaces, normalized provider data shapes, Yahoo adapters, and provider-focused tests.

Provider consumers should depend on protocols rather than Yahoo-specific classes:

- `MarketDataProvider` fetches normalized market data for one supported Stock.
- `CompanyNewsProvider` fetches compact Company News metadata for one supported Stock.
- `SummaryProvider` defines the future seam for generating Stock Summaries from structured inputs.

Yahoo-specific implementation details should stay inside a Yahoo adapter module. API routes, storage repositories, and forecast logic should not import Yahoo code directly.

## Normalized Market Data

The Yahoo market adapter returns a normalized result containing:

- Stock identity fields: ticker, company name when available, exchange when available.
- Historical price points with timestamp, open, high, low, close, and volume when available.
- Latest price.
- Previous close when available.
- Market status when Yahoo exposes a usable value.
- Observation timestamp for the provider fetch or latest market point.

The adapter should preserve the domain distinction between observed Market Snapshots and computed Stock Forecasts. It should return observed data only, not forecasts or predictions.

## Normalized Company News

The Yahoo news adapter returns compact Company News metadata suitable for Company News cards:

- Title.
- URL when available.
- Publisher or source when available.
- Published timestamp.
- Provider identifier when available.

To respect raw news licensing boundaries, normalized Company News must not expose raw article bodies, scrape article content, or store large raw provider payloads as domain data. Tests may use small fixture payloads, but production-facing normalized objects should contain compact metadata only.

## Supported Stock Boundary

Provider entry points accept a supported Stock object or validated supported Stock fields rather than arbitrary free-form symbols. The adapter can normalize ticker casing, but callers remain responsible for enforcing the supported Stock list before provider calls.

If a provider response resolves to a different symbol or lacks enough identity information to confirm the requested Stock, the adapter should treat the response as malformed rather than silently returning mismatched data.

## Error Handling

Provider errors should be explicit and testable:

- Missing data: response succeeds but lacks required fields.
- Stale data: response data is older than the caller's accepted freshness window.
- Malformed data: response shape or values cannot be normalized safely.
- Unsupported response: provider indicates the symbol is unavailable or incompatible.
- Transport error: HTTP/network/client failure.

Adapters may return partial optional fields only when required fields remain valid. Required fields for market data are ticker identity, latest price, and observation timestamp. Required fields for news items are title and published timestamp.

## Testing

Add provider tests under `backend/tests/providers/` using fake HTTP clients or injected response fixtures. Tests should not perform live Yahoo calls.

Coverage should include:

- Successful Yahoo market normalization, including historical prices, latest price, previous close, metadata, and market status when present.
- Successful Yahoo Company News normalization into compact metadata.
- Missing required provider fields.
- Stale market data.
- Malformed numeric and timestamp values.
- Mismatched or unsupported Stock responses.
- Transport failures.

## Follow-Up Work

Create a separate follow-up issue for ingestion persistence and jobs. That future work should connect provider outputs to storage repositories, persist Market Snapshots and Company News records, and schedule or trigger refreshes. It should not be part of issue #5.

## Self-Review

- Placeholder scan: no placeholders remain.
- Internal consistency: provider adapters return normalized observed data only; persistence and jobs are explicitly deferred.
- Scope check: focused on issue #5 provider seams and Yahoo normalization.
- Ambiguity check: supported Stock enforcement belongs to callers, while adapters reject mismatched provider responses.
