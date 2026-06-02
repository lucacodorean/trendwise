import {
  OpenAPI,
  StocksService,
  type StockSearchResult,
} from "./generated";
import { NativeModules } from "react-native";

import { normalizeStockSearchResults } from "./stocksResponse";

declare const process: {
  env: {
    EXPO_PUBLIC_API_BASE_URL?: string;
  };
};

function getExpoDevServerApiBaseUrl(): string | undefined {
  const scriptURL = NativeModules.SourceCode.scriptURL;
  if (typeof scriptURL !== "string") {
    return undefined;
  }

  const host = scriptURL.match(/^https?:\/\/([^/:]+)/)?.[1];
  return host ? `http://${host}:8000` : undefined;
}

const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ||
  getExpoDevServerApiBaseUrl() ||
  "http://localhost:8000";

OpenAPI.BASE = API_BASE_URL;

export type PrimaryStock = StockSearchResult;

export async function searchStocks(query: string): Promise<StockSearchResult[]> {
  const response = await StocksService.searchStocks({ q: query });
  return normalizeStockSearchResults(response);
}
