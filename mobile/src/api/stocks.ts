import {
  OpenAPI,
  StocksService,
  type StockSearchResult,
} from "./generated";

declare const process: {
  env: {
    EXPO_PUBLIC_API_BASE_URL?: string;
  };
};

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

OpenAPI.BASE = API_BASE_URL;

export type PrimaryStock = StockSearchResult;

export async function searchStocks(query: string): Promise<StockSearchResult[]> {
  const response = await StocksService.searchStocks({ q: query });
  return response.results;
}
