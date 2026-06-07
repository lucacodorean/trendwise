const assert = require("node:assert/strict");
const test = require("node:test");

import type { StockDetail } from "./api/stocks";
import { getDetailLoadingState } from "./appState";

const stock = {
  ticker: "AAPL",
  companyName: "Apple Inc.",
  exchange: "NASDAQ",
};

const detail: StockDetail = {
  disclaimer: "Not investment advice.",
  forecast: {
    freshnessLabel: "fresh",
    generatedAt: null,
    status: "available",
  },
  horizon: "1d",
  horizonMetadata: {
    calendarBasis: "regular_market_trading_time",
    externalFactorWeightScale: 1,
    label: "1 day",
    newsWindowDays: 1,
    pricePointBasis: "trading_session",
    timeBasis: "regular_market",
    value: "1d",
    expectedForecastPointCount: 24,
  },
  market: {
    dailyChange: null,
    dailyChangePercent: null,
    freshnessLabel: "fresh",
    latestPrice: null,
    observedAt: null,
    status: "available",
  },
  prediction: {
    confidence: null,
    direction: null,
    expectedChangePercent: null,
    freshnessLabel: "fresh",
    generatedAt: null,
    riskLevel: null,
    status: "available",
  },
  stock,
};

test("keeps the current detail visible while a replacement detail is loading", () => {
  assert.deepEqual(getDetailLoadingState(stock, detail), {
    status: "detail",
    stock,
    detail,
  });
});

test("shows the loading screen when there is no current detail to keep visible", () => {
  assert.deepEqual(getDetailLoadingState(stock), {
    status: "detail-loading",
    stock,
  });
});
