import AsyncStorage from "@react-native-async-storage/async-storage";

import type { ForecastHorizon } from "../api/stocks";

const FORECAST_HORIZON_KEY = "trendwise.forecastHorizon";

export const DEFAULT_FORECAST_HORIZON: ForecastHorizon = "1d";
export const FORECAST_HORIZONS: ForecastHorizon[] = ["30m", "1d", "5d", "7d", "1mo", "6mo", "1y"];
export const FORECAST_HORIZON_LABELS: Record<ForecastHorizon, string> = {
  "30m": "30 min",
  "1d": "1 day",
  "5d": "5 days",
  "7d": "7 days",
  "1mo": "1 month",
  "6mo": "6 months",
  "1y": "1 year",
};

export function isForecastHorizon(value: unknown): value is ForecastHorizon {
  return typeof value === "string" && FORECAST_HORIZONS.includes(value as ForecastHorizon);
}

export async function loadForecastHorizon(): Promise<ForecastHorizon> {
  const rawValue = await AsyncStorage.getItem(FORECAST_HORIZON_KEY);
  if (!rawValue) {
    return DEFAULT_FORECAST_HORIZON;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(rawValue);
  } catch {
    return DEFAULT_FORECAST_HORIZON;
  }

  return isForecastHorizon(parsed) ? parsed : DEFAULT_FORECAST_HORIZON;
}

export async function saveForecastHorizon(horizon: ForecastHorizon): Promise<void> {
  await AsyncStorage.setItem(FORECAST_HORIZON_KEY, JSON.stringify(horizon));
}
