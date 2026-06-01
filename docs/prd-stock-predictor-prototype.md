# PRD: Trendwise Off-Production Prototype

## Problem Statement

People who want to understand selected US-listed common stocks need a mobile-native way to see future-looking analytical estimates without receiving trading recommendations. They need one place to view a Stock Forecast graph, a Stock Prediction, Company News, a Stock Summary, and Key Factors, while understanding freshness, uncertainty, and risk. The prototype must also support comparing up to three Stocks without implying which one should be bought, sold, or held.

The product also needs enough backend structure to make forecasts auditable, reproducible, and replaceable as data providers and ML models evolve. Forecasts must be grounded in observed Market Snapshots and External Factors, not prior Stock Predictions.

## Solution

Build an off-production prototype consisting of a Python FastAPI backend and an Expo React Native mobile app. The backend stores Market Snapshots, generates ML-based Stock Forecasts and Stock Predictions, refreshes tracked/requested Stocks through background jobs, and uses OpenAI only for grounded Stock Summaries and Key Factors. The mobile app lets users select a primary Stock, view its detail screen, switch Forecast Horizons, toggle Line Forecast or Candlestick Forecast graphs, and compare with up to two additional Stocks.

The prototype is free, local-first, Dockerized for backend infrastructure, and intentionally excludes accounts, watchlists, monetization, push notifications, and trading recommendations.

## User Stories

1. As a mobile user, I want the app to open to my last selected primary Stock, so that I can quickly resume checking the Stock I care about.
2. As a first-time mobile user, I want the app to open to Stock Search when no primary Stock is cached, so that I can select a Stock to analyze.
3. As a mobile user, I want to search by ticker or company name, so that I can find a supported Stock quickly.
4. As a mobile user, I want search results to include only supported US-listed common Stocks, so that I do not select an unsupported instrument.
5. As a mobile user, I want unsupported instruments to be excluded or clearly rejected, so that I understand why ETFs, OTC symbols, funds, warrants, preferred shares, delisted symbols, and non-US exchanges are unavailable.
6. As a mobile user, I want to select exactly one primary Stock first, so that the default experience stays focused.
7. As a mobile user, I want to see the selected Stock's ticker, company name, and exchange when available, so that I know I selected the correct Stock.
8. As a mobile user, I want to see the current or latest market price and daily change, so that I understand the Stock's current context.
9. As a mobile user, I want to see market data freshness labels, so that I know whether the Stock Forecast is based on recent Market Snapshots.
10. As a mobile user, I want to see a compact disclaimer that forecasts and predictions are informational estimates only, so that the product framing is clear.
11. As a mobile user, I want the default Forecast Horizon to be `1d`, so that the first view is useful without requiring intraday assumptions.
12. As a mobile user, I want to select `30m`, `1d`, `5d`, `7d`, `1mo`, `6mo`, or `1y`, so that I can analyze different Forecast Horizons.
13. As a mobile user, I want `30m` to mean the next 30 minutes of regular market trading time, so that closed-market hours do not produce misleading wall-clock forecasts.
14. As a mobile user, I want `1d` to mean the next trading day, so that daily forecasts align with market sessions.
15. As a mobile user, I want `5d` to mean the next five trading days, so that the horizon matches a trading week.
16. As a mobile user, I want `7d`, `1mo`, `6mo`, and `1y` to use calendar periods represented through trading-session price points, so that longer horizons match common expectations.
17. As a mobile user, I want the selected Forecast Horizon to update the Forecast Graph, Stock Prediction, Stock Summary, news window, and External Factor weighting together, so that the screen stays coherent.
18. As a mobile user, I want to see a Stock Prediction card above the Forecast Graph, so that I can quickly understand the analytical signal before studying the graph.
19. As a mobile user, I want the Stock Prediction to include direction, confidence, expected change, and Risk Level, so that I understand both the estimate and uncertainty.
20. As a mobile user, I want direction to be `bullish`, `bearish`, or `neutral`, so that the app avoids buy, sell, or hold language.
21. As a mobile user, I want confidence to account for model probability, forecast uncertainty, calibration, data quality, and signal agreement, so that the confidence score does not overstate weak forecasts.
22. As a mobile user, I want Risk Level to mean uncertainty and volatility rather than investment advice, so that I do not confuse analytical risk with personal financial suitability.
23. As a mobile user, I want to see 3-5 Key Factors inside the Stock Prediction card, so that I understand what signals influenced the prediction.
24. As a mobile user, I want Key Factors to be grounded in Market Snapshots, Company News, External Factors, and Stock Forecast data, so that explanations are traceable.
25. As a mobile user, I want the Forecast Graph to show historical price context and a clearly separated forecast segment, so that I do not confuse projected values with observed values.
26. As a mobile user, I want Line Forecast to be the default graph type on first use, so that the graph is easy to understand.
27. As a mobile user, I want to switch to Candlestick Forecast, so that I can inspect estimated OHLC behavior.
28. As a mobile user, I want the app to remember my graph type preference locally, so that future screens use my preferred graph style.
29. As a mobile user, I want every forecast point to include an expected value and uncertainty range, so that uncertainty is visible across the whole Forecast Horizon.
30. As a mobile user, I want a single-stock detail graph to use actual prices, so that I can interpret the Stock directly.
31. As a mobile user, I want extended-hours movement to be shown only when visually distinct and labeled, so that it is not confused with regular-session prices.
32. As a mobile user, I want to tap `Compare with` from the Stock Detail screen, so that I can add comparison Stocks after starting from one primary Stock.
33. As a mobile user, I want the `Compare with` action available in the header and near graph controls, so that comparison is discoverable.
34. As a mobile user, I want `Compare with` to open a bottom sheet, so that I remain anchored in the current primary Stock context.
35. As a mobile user, I want to add up to two comparison Stocks at once, so that I can compare a maximum of three Stocks efficiently.
36. As a mobile user, I want comparison Stocks to follow the same supported-stock restrictions as the primary Stock, so that comparison data is consistent.
37. As a mobile user, I want the primary Stock to be impossible to select again as a comparison Stock, so that duplicate graph series are prevented.
38. As a mobile user, I want all Stocks in a Stock Comparison to share one Forecast Horizon, so that the comparison is meaningful.
39. As a mobile user, I want each selected Stock to have its own Stock Prediction, so that comparison does not collapse into a recommendation.
40. As a mobile user, I do not want the app to rank selected Stocks or produce a winner, so that the app avoids trading recommendations.
41. As a mobile user, I want compact prediction cards for all selected Stocks above the comparison graph, so that I can compare analytical signals quickly.
42. As a mobile user, I want comparison graphs to use normalized percentage movement, so that Stocks with different prices are visually comparable.
43. As a mobile user, I want the comparison view to use one shared graph type for all selected Stocks, so that the graph remains readable.
44. As a mobile user, I want candlestick comparison to use normalized percentage movement, so that multi-stock candlestick views remain comparable.
45. As a mobile user, I want to hide or show graph series independently during a comparison, so that I can reduce visual clutter.
46. As a mobile user, I want graph visibility state to be temporary frontend state, so that hidden series do not persist unexpectedly across app restarts.
47. As a mobile user, I want prediction summaries to remain visible when a graph series is hidden, so that the Stock remains part of the comparison.
48. As a mobile user, I want to remove comparison Stocks, so that I can return to a simpler view.
49. As a mobile user, I want removing all comparison Stocks to return to single-stock detail mode, so that the UI state is clear.
50. As a mobile user, I want to change the primary Stock from the detail screen, so that I do not need awkward navigation back to search.
51. As a mobile user, I want changing the primary Stock to clear comparison Stocks, so that the new analysis starts cleanly.
52. As a mobile user, I want the app to cache the last selected primary Stock, so that relaunch opens the Stock I last cared about.
53. As a mobile user, I want the app to cache the last selected Forecast Horizon, so that relaunch preserves my analysis context.
54. As a mobile user, I do not want comparison Stocks restored on relaunch, so that the app does not reopen into a cluttered state.
55. As a mobile user, I want the Stock Summary before Company News, so that I get a concise synthesis before source detail.
56. As a mobile user, I want Company News listed separately from the Stock Summary, so that I can trace the summary back to source articles.
57. As a mobile user, I want Company News cards to show title, source, date/time, snippet, and source-opening action, so that I can decide whether to read more.
58. As a mobile user, I want five Company News items by default with `Show more`, so that the screen stays concise.
59. As a mobile user, I want Company News freshness to update when I access a Stock, so that news context is current.
60. As a mobile user, I want Stock Summaries to incorporate recent performance, Company News, External Factors, and Stock Forecast or Stock Prediction interpretation, so that I understand the current context.
61. As a mobile user, I want Stock Summaries and Key Factors generated by an LLM only from structured inputs, so that they are useful without inventing facts.
62. As a mobile user, I want deterministic fallback summaries when the LLM API is unavailable, so that the screen still works.
63. As a mobile user, I want news windows to depend on Forecast Horizon, so that short-term forecasts emphasize recent news and long-term forecasts include longer context.
64. As a mobile user, I want social media sentiment excluded, so that the prototype avoids noisy and moderation-heavy signals.
65. As a mobile user, I want news sentiment allowed when derived from reputable Company News, so that the app can summarize article tone.
66. As a mobile user, I want earnings events treated as important External Factors when available, so that forecasts reflect major stock-specific catalysts.
67. As a mobile user, I want analyst ratings used when available but not required, so that missing ratings do not block forecasts.
68. As a mobile user, I want stale forecasts clearly labeled, so that I can judge whether to trust the information.
69. As a mobile user, I want forecasts unavailable when Market Snapshots are too old, so that the app avoids generating misleading output.
70. As a mobile user, I want generated/update timestamps for forecasts, Market Snapshots, and news, so that freshness is transparent.
71. As a mobile user, I want to manually refresh news and summaries, so that current information can update without implying forecasts constantly change.
72. As a mobile user, I do not want manual forecast refresh spam, so that scheduled forecast freshness remains understandable.
73. As a mobile user, I want limited offline display of cached last primary Stock detail, so that I can see the last loaded analysis without connectivity.
74. As a mobile user, I want offline data clearly labeled as cached, so that I do not mistake it for fresh data.
75. As a mobile user, I want search, compare add, refresh, and backend-dependent actions disabled offline, so that unavailable operations are clear.
76. As a mobile user, I want no forecasts generated locally offline, so that mobile behavior remains consistent with backend-generated forecasts.
77. As a mobile user, I want partial-data screens when forecast data is unavailable but news exists, so that available context remains useful.
78. As a mobile user, I want forecast/prediction data shown when news is unavailable, so that a news provider failure does not hide model output.
79. As a mobile user, I want the app to support system dark mode, so that it matches my device appearance.
80. As a mobile user, I want graphs readable in light and dark themes, so that forecast interpretation works in either mode.
81. As a mobile user, I want a minimal settings/about screen, so that I can access legal/privacy links and app information.
82. As a mobile user, I want to clear local cache, so that remembered primary Stock, Forecast Horizon, graph type, and cached detail are removed.
83. As a mobile user, I want the app to be English-only in the prototype, so that terminology remains consistent.
84. As a mobile user, I want no accounts in the prototype, so that I can use the app without login.
85. As a mobile user, I want no watchlists in the prototype, so that the app stays focused on selected Stock analysis.
86. As a mobile user, I want no push or local notifications, so that the app does not behave like a trading alert product.
87. As a mobile user, I want no payments, subscriptions, ads, or premium limits, so that the prototype is completely free.
88. As a mobile user, I want no buy, sell, or hold recommendations anywhere, so that the app remains analytical.
89. As a backend operator, I want Market Snapshots stored separately from Stock Forecasts, so that observed data is not confused with computed output.
90. As a backend operator, I want Stock Forecasts grounded in Market Snapshots, historical prices, External Factors, Company News, and model logic, so that forecasts remain auditable.
91. As a backend operator, I want Stock Forecasts to ignore prior Stock Predictions as evidence, so that feedback loops are avoided.
92. As a backend operator, I want all generated Forecast Runs and Prediction Runs stored historically, so that model quality can be evaluated later.
93. As a backend operator, I want Market Snapshots and Forecast Runs retained for at least five years where licensing permits, so that long-horizon evaluation is possible.
94. As a backend operator, I want raw news handling to respect provider licensing, so that the prototype does not store content improperly.
95. As a backend operator, I want daily market-close snapshots for tracked/requested Stocks, so that users get fresh daily analytical results.
96. As a backend operator, I want intraday snapshots for `30m` when requested or actively tracked, so that intraday forecasts have recent context.
97. As a backend operator, I want Stocks requested in the last 30 days treated as tracked, so that refresh jobs stay bounded.
98. As a backend operator, I want all canonical Forecast Horizons generated during closed-market refresh for tracked/requested Stocks, so that the UI can switch horizons quickly.
99. As a backend operator, I want Yahoo Finance behind provider adapters in the prototype, so that market and news providers can be replaced later.
100. As a backend operator, I want OpenAI behind a summary adapter, so that LLM provider choice can be changed later.
101. As a backend operator, I want OpenAI used only for Stock Summaries and Key Factors, so that numeric forecasts remain reproducible and measurable.
102. As a backend operator, I want ML used from day one for numeric Stock Forecasts and Stock Predictions, so that the prototype validates the intended modeling path.
103. As a backend operator, I want a shared model architecture with a global base model, so that patterns can be learned across supported Stocks.
104. As a backend operator, I want horizon-specific model heads or outputs, so that `30m` and `1y` can specialize on different signals.
105. As a backend operator, I want optional stock-specific fine-tuning or calibration when enough data exists, so that individual Stocks can be adapted later.
106. As a backend operator, I want full forecast steps generated by the model rather than frontend interpolation, so that graph paths reflect model output.
107. As a backend operator, I want Candlestick Forecast data derived from predicted path and volatility in the prototype, so that OHLC visualization is possible without a separate direct-OHLC model.
108. As a backend operator, I want weekly scheduled retraining, so that models can improve as data accumulates.
109. As a backend operator, I want validation-gated model promotion, so that failed or worse candidate models do not replace the current promoted model.
110. As a backend operator, I want failed retraining to keep the current promoted model, so that user-facing forecasts remain available when possible.
111. As a backend operator, I want no user-facing historical accuracy reporting in the prototype, so that immature metrics do not mislead users.
112. As a backend operator, I want CLI-only admin tooling, so that model/job status and recovery actions are available without a web dashboard.
113. As a backend operator, I want CLI commands to inspect status, current model, last retraining, refresh health, and data freshness, so that operations can be diagnosed locally.
114. As a backend operator, I want CLI commands to trigger retraining, trigger forecast refresh for a Stock, and promote validated models, so that recovery actions are explicit.
115. As a backend operator, I want PostgreSQL as the durable database, so that Stock data, Market Snapshots, Forecast Runs, Prediction Runs, provider records, model versions, jobs, and analytics are queryable.
116. As a backend operator, I want plain PostgreSQL first rather than TimescaleDB, so that local prototype operations remain simpler.
117. As a backend operator, I want Redis used for Celery broker/result backend only, so that durable data remains in PostgreSQL.
118. As a backend operator, I want local filesystem model artifacts with PostgreSQL metadata, so that model storage remains simple in Docker.
119. As a backend operator, I want Docker Compose to start backend infrastructure, so that local setup is reproducible.
120. As a backend operator, I want the Expo app run separately from Docker Compose in the prototype, so that mobile development remains ergonomic on macOS.
121. As a backend operator, I want `.env` files for local secrets and `.env.example` committed, so that required configuration is clear without committing secrets.
122. As a backend operator, I want OpenTelemetry on backend API, jobs, provider calls, and model operations, so that technical telemetry is available.
123. As a backend operator, I want production observability export configurable but not vendor-locked, so that the prototype remains portable.
124. As a product owner, I want minimal anonymous analytics stored internally, so that product behavior can be improved without adding a third-party analytics vendor.
125. As a product owner, I want raw anonymous analytics retained for 90 days, so that privacy and storage risk stay bounded.
126. As a product owner, I want legal/privacy documents available in-app and hostable publicly later, so that app store and user trust needs are covered.
127. As a developer, I want FastAPI to own OpenAPI, so that the backend contract is explicit.
128. As a developer, I want generated TypeScript API types in the mobile app, so that backend/frontend contract drift is reduced.
129. As a developer, I want one combined stock-detail endpoint, so that the mobile detail screen can render from one coherent payload.
130. As a developer, I want comparison data returned by the same stock-detail endpoint through optional comparison parameters, so that comparison remains an extension of detail view.
131. As a developer, I want backend-provided normalized comparison graph data, so that normalization is treated as business logic rather than ad hoc frontend rendering.
132. As a developer, I want structured backend values and frontend display formatting, so that API contracts remain testable and formatting stays presentation-specific.
133. As a developer, I want frontend formatting for prices, percentages, confidence, and large values, so that UI presentation can evolve without changing backend data.
134. As a developer, I want GitHub Actions CI, so that backend tests, mobile checks, Docker checks, and OpenAPI generation checks run consistently.
135. As a developer, I want basic rate limits and provider-cost protections, so that a free prototype does not accidentally overload providers or local jobs.

## Implementation Decisions

- The project is a monorepo containing the Python backend, Expo mobile app, infrastructure configuration, documentation, ADRs, legal drafts, and generated API client artifacts.
- The backend is a modular monolith rather than multiple deployable services.
- The backend API uses FastAPI.
- The mobile app uses Expo React Native with TypeScript.
- FastAPI owns the OpenAPI schema.
- The mobile app consumes generated TypeScript API types/client code from the backend OpenAPI contract.
- Generated TypeScript client code lives inside the mobile app for the prototype because there is only one TypeScript consumer.
- PostgreSQL is the primary durable database.
- Plain PostgreSQL is used first; TimescaleDB is deferred until measured snapshot volume or query performance requires it.
- Redis is used as Celery broker/result backend, not as durable forecast or snapshot storage.
- Celery handles background jobs and scheduling for ingestion, refresh, and model-related work.
- Model training runs on a separate queue or CLI path so heavy training does not starve normal refresh jobs.
- Model artifacts are stored in a local filesystem volume for the prototype, with model metadata stored in PostgreSQL.
- Docker Compose starts the backend, worker, scheduler, PostgreSQL, Redis, OpenTelemetry Collector, and optional trace viewer locally.
- Expo development is run separately from Docker Compose for the prototype.
- Local secrets use `.env` files that are not committed; `.env.example` documents required variables.
- The prototype is off-production and local-first.
- Yahoo Finance is the initial market data and Company News source through provider adapters.
- OpenAI API is used for Stock Summaries and Key Factors through a summary adapter.
- Deterministic template summaries are used when OpenAI configuration is missing or calls fail.
- Provider adapters are mandatory seams so Yahoo Finance and OpenAI can be replaced later.
- The supported Stock universe is constrained to selected US-listed common Stocks, initially S&P 500 and optionally high-volume NASDAQ/NYSE common Stocks.
- Unsupported instruments include ETFs, OTC securities, warrants, preferred shares, funds, delisted symbols, and non-US exchanges.
- Users select Stocks from supported search results only.
- The app has no accounts, watchlists, monetization, ads, premium limits, notifications, or trading recommendations in the prototype.
- Forecast Horizons are exactly `30m`, `1d`, `5d`, `7d`, `1mo`, `6mo`, and `1y`.
- Default Forecast Horizon is `1d`.
- `30m` means the next 30 minutes of regular market trading time and targets next market open when selected during closed-market hours.
- Short horizons are market-session aware; longer horizons are calendar periods represented through trading-session price points.
- Stock Forecasts are grounded in Market Snapshots, historical prices, External Factors, Company News, and model logic.
- Stock Forecasts must not use prior Stock Predictions as evidence.
- Market Snapshots are stored separately from computed Stock Forecasts.
- Stock Predictions may summarize a Stock Forecast and other structured signals, but predictions do not feed future forecasts.
- Forecast and prediction runs are stored historically for evaluation and audit.
- Forecast Runs and Market Snapshots are retained at least five years where licensing permits.
- Raw analytics events are retained for 90 days.
- News storage respects provider licensing; metadata/features may be retained longer than raw article content.
- A Stock becomes tracked when requested as primary or comparison in the last 30 days.
- Daily market-close refresh prepares all canonical Forecast Horizons for tracked/requested Stocks.
- Intraday snapshots are captured for `30m` when requested or actively tracked.
- Fresh Company News is fetched on Stock access.
- Stale forecast data may be displayed with clear labels if not beyond cutoff.
- Forecast generation is blocked when underlying Market Snapshots are too old.
- ML is used from day one for numeric Stock Forecasts and Stock Predictions.
- The ML strategy is a shared model architecture with a global base model and horizon-specific heads or outputs.
- Optional stock-specific fine-tuning or calibration may be added when enough data exists.
- The model outputs explicit forecast steps for graphs rather than only endpoint forecasts.
- Forecast points include expected value, lower bound, upper bound, and timestamp or interval.
- Candlestick Forecasts are derived from forecast path and volatility/range estimates for the prototype.
- Stock Prediction confidence combines model probability, forecast uncertainty, calibration, data quality, and signal agreement.
- Risk Level represents uncertainty and volatility, not personal investment advice.
- Weekly scheduled retraining creates candidate models.
- Candidate models are promoted only after validation passes.
- Failed retraining or validation keeps the current promoted model.
- No user-facing historical accuracy reporting is included in the prototype.
- The backend exposes a combined stock-detail response optimized for the mobile Stock Detail screen.
- The stock-detail response includes stock identity, selected Forecast Horizon, Forecast Graph data, Stock Prediction, Key Factors, Stock Summary, Company News, freshness timestamps, and optional comparison data.
- Comparison data is fetched through the same stock-detail endpoint with optional comparison Stock parameters.
- The backend returns raw actual-price graph data for single-stock detail and normalized percentage graph series for comparison.
- Frontend graph visibility is local UI state only.
- Frontend persists last selected primary Stock, last selected Forecast Horizon, graph type preference, and cached last loaded stock detail.
- Frontend does not persist comparison Stocks or hidden graph series state across app restarts.
- Clearing local cache removes primary Stock, Forecast Horizon, graph type preference, and cached stock detail.
- The app follows system dark mode and does not include an in-app theme override in the prototype.
- The app includes a minimal settings/about screen with legal/privacy links, app version, disclaimer, and clear-cache action.
- Legal/privacy documents include Privacy Policy, Terms/Disclaimer, and financial information disclaimer.
- OpenTelemetry is used for backend observability first.
- Frontend gets basic error/performance logging, not full OpenTelemetry in the prototype unless it is straightforward.
- Minimal anonymous product analytics are stored internally.
- GitHub Actions is the intended CI platform.
- CI should run backend tests/lint/type checks, mobile TypeScript/lint/tests, Docker checks, and OpenAPI generation checks.

## Testing Decisions

- Tests should verify external behavior at the highest practical seam, not implementation details.
- The highest product seam is the mobile Stock Detail and Stock Comparison behavior backed by the combined stock-detail API contract.
- The highest backend seam is the combined stock-detail endpoint because it integrates stock identity, Forecast Horizon, graph data, Stock Prediction, Key Factors, Stock Summary, Company News, freshness, and comparison behavior.
- API contract tests should verify valid single-stock detail payloads and valid comparison payloads with up to three Stocks.
- API validation tests should reject unsupported Forecast Horizons, unsupported Stocks, duplicate comparison Stocks, more than two comparison Stocks, and duplicate primary-as-comparison selection.
- Domain tests should verify canonical Forecast Horizon parsing and rejection of ambiguous forms like `1M` and `30M`.
- Domain tests should verify Forecast Horizon market-time interpretation, especially `30m` during closed-market hours.
- Domain tests should verify that Stock Forecast generation never consumes prior Stock Predictions as input evidence.
- Repository tests should verify storing and retrieving Stocks, Market Snapshots, Forecast Runs, Prediction Runs, Company News records, External Factor records, Model Versions, job statuses, and analytics events.
- Provider adapter tests should use mocked Yahoo Finance responses to verify normalized market data, metadata, and news records.
- Provider adapter tests should verify fallback behavior when Yahoo Finance data is missing, stale, or malformed.
- Summary adapter tests should verify OpenAI receives only structured grounded inputs and does not own numeric forecast/prediction values.
- Summary fallback tests should verify deterministic Stock Summary and Key Factors are returned when OpenAI is unavailable.
- ML pipeline tests should verify every canonical Forecast Horizon returns forecast steps with expected value, lower bound, upper bound, and timestamp/interval.
- ML pipeline tests should verify Stock Prediction direction, confidence, expected change, Risk Level, and Key Factor inputs are produced without buy/sell/hold language.
- ML pipeline tests should verify Candlestick Forecast output is derived from forecast path and uncertainty/range estimates.
- Model validation tests should verify a failed candidate model does not replace the current promoted model.
- Job tests should verify market snapshot refresh, news refresh, forecast refresh, scheduled retraining, failure logging, and durable job status updates.
- CLI tests should verify read-only status commands and explicit operational actions such as retrain trigger, forecast refresh trigger, and validated model promotion.
- Rate-limit tests should verify repeated expensive requests receive clear throttling responses.
- Observability tests should verify instrumentation hooks exist for API requests, Celery jobs, provider calls, and model operations at integration boundaries.
- Analytics tests should verify anonymous event ingestion does not require accounts or direct user identity.
- Mobile screen tests should verify launch behavior chooses cached primary Stock and cached Forecast Horizon when available, otherwise Stock Search.
- Mobile screen tests should verify Stock Search returns/selects supported Stocks only.
- Mobile screen tests should verify Stock Detail renders header, freshness labels, disclaimer, Forecast Horizon selector, Stock Prediction card, Forecast Graph, Stock Summary, and Company News.
- Mobile screen tests should verify `Show more` behavior for Company News after five default items.
- Mobile screen tests should verify graph type preference persists locally.
- Mobile screen tests should verify comparison bottom sheet selection rules and max two comparison Stocks.
- Mobile screen tests should verify comparison cards, normalized graph display, active Stock switching, graph hide/show, and comparison removal behavior.
- Mobile storage tests should verify local cache clearing removes remembered primary Stock, Forecast Horizon, graph type preference, and cached stock detail.
- Mobile offline tests should verify cached detail is read-only, labeled offline/cached, and backend-dependent actions are disabled.
- Legal/settings tests should verify legal/privacy/disclaimer links are reachable and clear-cache action is available.
- There is no prior implementation test suite in the current repo; prior art is the existing documentation: `CONTEXT.md`, product decisions, implementation plan, and ADRs.

## Out of Scope

- Production deployment hardening.
- App store release setup.
- Expo EAS formal build pipeline.
- User accounts.
- Watchlists.
- Personalized preferences stored on the backend.
- Push notifications.
- Local notifications.
- Subscriptions.
- Ads.
- Premium limits.
- Buy, sell, or hold recommendations.
- Ranking comparison Stocks as a winner or best option.
- Full historical accuracy reporting to users.
- ETFs and index funds.
- OTC securities.
- Warrants.
- Preferred shares.
- Delisted symbols.
- Non-US exchanges.
- Multi-currency support.
- Social media sentiment.
- Full offline functionality.
- Locally generated mobile forecasts.
- Dedicated web admin dashboard.
- Full frontend OpenTelemetry instrumentation unless trivial.
- TimescaleDB or specialized time-series storage.
- Kubernetes or multi-service production orchestration.
- Third-party product analytics vendors.
- Multilingual UI or summaries.
- In-app theme toggle.

## Further Notes

The PRD reflects an off-production prototype. The most important product boundary is that the app is analytical and informational only. It must not offer trading recommendations or imply personalized financial advice.

The most important modeling boundary is that Stock Forecasts are grounded in observed Market Snapshots, historical prices, External Factors, Company News, and model logic. Prior Stock Predictions are stored for audit/evaluation but must not become evidence for future forecasts.

The most important architecture boundary is provider replaceability. Yahoo Finance and OpenAI are acceptable for the prototype, but both must sit behind adapters.

The issue tracker could not be updated from this environment because the workspace has no GitHub metadata and the `gh` command is unavailable. Apply the `ready-for-agent` label when publishing this PRD to the issue tracker.
