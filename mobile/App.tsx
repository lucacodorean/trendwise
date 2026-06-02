import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Pressable, SafeAreaView, StyleSheet, Text } from "react-native";
import { StatusBar } from "expo-status-bar";

import { getStockDetail, type PrimaryStock, type StockDetail } from "./src/api/stocks";
import { StockDetailScreen } from "./src/screens/StockDetailScreen";
import { StockSearchScreen } from "./src/screens/StockSearchScreen";
import {
  clearPrimaryStock,
  loadPrimaryStock,
  savePrimaryStock,
} from "./src/storage/primaryStock";

type AppState =
  | { status: "loading" }
  | { status: "search" }
  | { status: "detail-loading"; stock: PrimaryStock }
  | { status: "detail-error"; stock: PrimaryStock }
  | { status: "detail"; stock: PrimaryStock; detail: StockDetail };

export default function App() {
  const [appState, setAppState] = useState<AppState>({ status: "loading" });
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const detailRequestId = useRef(0);

  useEffect(() => {
    let isActive = true;

    async function hydratePrimaryStock() {
      try {
        const cachedStock = await loadPrimaryStock();
        if (isActive) {
          if (cachedStock) {
            loadDetailForStock(cachedStock);
          } else {
            setAppState({ status: "search" });
          }
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

  async function loadDetailForStock(stock: PrimaryStock) {
    const requestId = detailRequestId.current + 1;
    detailRequestId.current = requestId;

    setAppState({ status: "detail-loading", stock });

    try {
      const detail = await getStockDetail(stock.ticker, "1d");
      if (detailRequestId.current === requestId) {
        setDetailError(null);
        setAppState({ status: "detail", stock, detail });
      }
    } catch {
      if (detailRequestId.current === requestId) {
        setDetailError("Could not load Stock details. Try again.");
        setAppState({ status: "detail-error", stock });
      }
    }
  }

  async function handleSelectStock(stock: PrimaryStock) {
    try {
      await savePrimaryStock(stock);
      setSelectionError(null);
      setDetailError(null);
      loadDetailForStock(stock);
    } catch {
      setSelectionError("Could not save your selected Stock. Try again.");
      setAppState({ status: "search" });
    }
  }

  async function handleChangeStock() {
    try {
      detailRequestId.current += 1;
      await clearPrimaryStock();
      setDetailError(null);
      setSelectionError(null);
      setAppState({ status: "search" });
    } catch {
      setDetailError("Could not clear your selected Stock. Try again.");
    }
  }

  return (
    <>
      <StatusBar style="light" />
      {appState.status === "loading" ? (
        <SafeAreaView style={styles.loadingScreen}>
          <ActivityIndicator color="#60a5fa" />
        </SafeAreaView>
      ) : null}
      {appState.status === "search" ? (
        <StockSearchScreen onSelect={handleSelectStock} selectionError={selectionError} />
      ) : null}
      {appState.status === "detail-loading" ? (
        <SafeAreaView style={styles.loadingScreen}>
          <ActivityIndicator color="#60a5fa" />
          <Text style={styles.loadingText}>Loading {appState.stock.ticker} details...</Text>
        </SafeAreaView>
      ) : null}
      {appState.status === "detail-error" ? (
        <SafeAreaView style={styles.errorScreen}>
          <Text style={styles.errorTitle}>{appState.stock.ticker} details unavailable</Text>
          <Text style={styles.errorText}>{detailError}</Text>
          <Pressable
            accessibilityLabel="Change selected Stock"
            accessibilityRole="button"
            onPress={handleChangeStock}
            style={styles.changeButton}
          >
            <Text style={styles.changeButtonText}>Change Stock</Text>
          </Pressable>
        </SafeAreaView>
      ) : null}
      {appState.status === "detail" ? (
        <StockDetailScreen
          detail={appState.detail}
          detailError={detailError}
          onChangeStock={handleChangeStock}
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
  loadingText: {
    color: "#cbd5e1",
    marginTop: 16,
  },
  errorScreen: {
    backgroundColor: "#0f172a",
    flex: 1,
    justifyContent: "center",
    padding: 24,
  },
  errorTitle: {
    color: "#f8fafc",
    fontSize: 28,
    fontWeight: "900",
    marginBottom: 12,
  },
  errorText: {
    color: "#fecaca",
    lineHeight: 22,
  },
  changeButton: {
    alignItems: "center",
    backgroundColor: "#2563eb",
    borderRadius: 16,
    marginTop: 24,
    padding: 16,
  },
  changeButtonText: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "800",
  },
});
