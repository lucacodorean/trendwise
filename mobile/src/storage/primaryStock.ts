import AsyncStorage from "@react-native-async-storage/async-storage";

import type { PrimaryStock } from "../api/stocks";

const PRIMARY_STOCK_KEY = "trendwise.primaryStock";

export async function loadPrimaryStock(): Promise<PrimaryStock | null> {
  const rawValue = await AsyncStorage.getItem(PRIMARY_STOCK_KEY);
  if (!rawValue) {
    return null;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(rawValue);
  } catch {
    return null;
  }

  if (parsed === null || typeof parsed !== "object") {
    return null;
  }

  const stock = parsed as Partial<PrimaryStock>;
  if (
    typeof stock.ticker !== "string" ||
    typeof stock.companyName !== "string" ||
    typeof stock.exchange !== "string"
  ) {
    return null;
  }

  return {
    ticker: stock.ticker,
    companyName: stock.companyName,
    exchange: stock.exchange,
  };
}

export async function savePrimaryStock(stock: PrimaryStock): Promise<void> {
  await AsyncStorage.setItem(PRIMARY_STOCK_KEY, JSON.stringify(stock));
}

export async function clearPrimaryStock(): Promise<void> {
  await AsyncStorage.removeItem(PRIMARY_STOCK_KEY);
}
