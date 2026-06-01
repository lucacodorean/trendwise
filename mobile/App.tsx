import { useEffect, useState } from "react";
import { ActivityIndicator, SafeAreaView, StyleSheet } from "react-native";
import { StatusBar } from "expo-status-bar";

import type { PrimaryStock } from "./src/api/stocks";
import { StockDetailPlaceholderScreen } from "./src/screens/StockDetailPlaceholderScreen";
import { StockSearchScreen } from "./src/screens/StockSearchScreen";
import {
  clearPrimaryStock,
  loadPrimaryStock,
  savePrimaryStock,
} from "./src/storage/primaryStock";

type AppState =
  | { status: "loading" }
  | { status: "search" }
  | { status: "detail"; stock: PrimaryStock };

export default function App() {
  const [appState, setAppState] = useState<AppState>({ status: "loading" });

  useEffect(() => {
    let isActive = true;

    async function hydratePrimaryStock() {
      try {
        const cachedStock = await loadPrimaryStock();
        if (isActive) {
          setAppState(cachedStock ? { status: "detail", stock: cachedStock } : { status: "search" });
        }
      } catch {
        if (isActive) {
          setAppState({ status: "search" });
        }
      }
    }

    hydratePrimaryStock();

    return () => {
      isActive = false;
    };
  }, []);

  async function handleSelectStock(stock: PrimaryStock) {
    await savePrimaryStock(stock);
    setAppState({ status: "detail", stock });
  }

  async function handleChangeStock() {
    await clearPrimaryStock();
    setAppState({ status: "search" });
  }

  return (
    <>
      <StatusBar style="light" />
      {appState.status === "loading" ? (
        <SafeAreaView style={styles.loadingScreen}>
          <ActivityIndicator color="#60a5fa" />
        </SafeAreaView>
      ) : null}
      {appState.status === "search" ? <StockSearchScreen onSelect={handleSelectStock} /> : null}
      {appState.status === "detail" ? (
        <StockDetailPlaceholderScreen
          onChangeStock={handleChangeStock}
          stock={appState.stock}
        />
      ) : null}
    </>
  );
}

const styles = StyleSheet.create({
  loadingScreen: {
    alignItems: "center",
    backgroundColor: "#0f172a",
    flex: 1,
    justifyContent: "center",
  },
});
