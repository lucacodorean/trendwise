const { describe, it } = require("node:test");
const assert = require("node:assert/strict");

const { normalizeStockSearchResults } = require("./stocksResponse.ts");

describe("normalizeStockSearchResults", () => {
  it("returns results from the generated stock search response", () => {
    assert.deepEqual(
      normalizeStockSearchResults({
        results: [{ ticker: "AAPL", companyName: "Apple Inc.", exchange: "NASDAQ" }],
      }),
      [{ ticker: "AAPL", companyName: "Apple Inc.", exchange: "NASDAQ" }],
    );
  });

  it("returns a bare result array when the API response is already unwrapped", () => {
    assert.deepEqual(
      normalizeStockSearchResults([
        { ticker: "MSFT", companyName: "Microsoft Corporation", exchange: "NASDAQ" },
      ]),
      [{ ticker: "MSFT", companyName: "Microsoft Corporation", exchange: "NASDAQ" }],
    );
  });
});
