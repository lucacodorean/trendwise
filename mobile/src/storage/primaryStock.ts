import AsyncStorage from "@react-native-async-storage/async-storage";

import type { PrimaryStock } from "../api/stocks";

const PRIMARY_STOCK_KEY = "trendwise.primaryStock";

export async function loadPrimaryStock(): Promise<PrimaryStock | null> {
  const rawValue = await AsyncStorage.getItem(PRIMARY_STOCK_KEY);
  if (!rawValue) {
    return null;
  }

  const parsed = JSON.parse(rawValue) as Partial<PrimaryStock>;
  if (
    typeof parsed.ticker !== "string" ||
    typeof parsed.companyName !== "string" ||
    typeof parsed.exchange !== "string"
  ) {
    return null;
  }

  return {
    ticker: parsed.ticker,
    companyName: parsed.companyName,
    exchange: parsed.exchange,
  };
}

export async function savePrimaryStock(stock: PrimaryStock): Promise<void> {
  await AsyncStorage.setItem(PRIMARY_STOCK_KEY, JSON.stringify(stock));
}

export async function clearPrimaryStock(): Promise<void> {
  await AsyncStorage.removeItem(PRIMARY_STOCK_KEY);
}
