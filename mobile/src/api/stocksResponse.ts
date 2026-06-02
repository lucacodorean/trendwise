import type { StockSearchResponse, StockSearchResult } from "./generated";

export function normalizeStockSearchResults(
  response: StockSearchResponse | StockSearchResult[],
): StockSearchResult[] {
  return Array.isArray(response) ? response : response.results;
}
