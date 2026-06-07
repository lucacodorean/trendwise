import type { PrimaryStock, StockDetail } from "./api/stocks";

export type AppState =
  | { status: "loading" }
  | { status: "search" }
  | { status: "detail-loading"; stock: PrimaryStock }
  | { status: "detail-error"; stock: PrimaryStock }
  | { status: "detail"; stock: PrimaryStock; detail: StockDetail };

export function getDetailLoadingState(
  stock: PrimaryStock,
  fallbackDetail?: StockDetail,
): AppState {
  return fallbackDetail
    ? { status: "detail", stock, detail: fallbackDetail }
    : { status: "detail-loading", stock };
}
