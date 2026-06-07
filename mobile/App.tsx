import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, Pressable, SafeAreaView, StyleSheet, Text } from "react-native";
import { StatusBar } from "expo-status-bar";

import { getStockDetail, type ForecastHorizon, type PrimaryStock, type StockDetail } from "./src/api/stocks";
import { StockDetailScreen } from "./src/screens/StockDetailScreen";
import { StockSearchScreen } from "./src/screens/StockSearchScreen";
import {
  DEFAULT_FORECAST_HORIZON,
  FORECAST_HORIZON_LABELS,
  FORECAST_HORIZONS,
  loadForecastHorizon,
  saveForecastHorizon,
} from "./src/storage/forecastHorizon";
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
  const [selectedHorizon, setSelectedHorizon] = useState<ForecastHorizon>(DEFAULT_FORECAST_HORIZON);
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const selectionRequestId = useRef(0);
  const detailRequestId = useRef(0);
  const savePrimaryStockQueue = useRef<Promise<void>>(Promise.resolve());
  const saveForecastHorizonQueue = useRef<Promise<void>>(Promise.resolve());

  useEffect(() => {
    let isActive = true;

    async function hydratePrimaryStock() {
      try {
        const [cachedStock, cachedHorizon] = await Promise.all([
          loadPrimaryStock(),
          loadForecastHorizon(),
        ]);
        if (isActive) {
          setSelectedHorizon(cachedHorizon);
          if (cachedStock) {
            loadDetailForStock(cachedStock, cachedHorizon);
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

  async function loadDetailForStock(stock: PrimaryStock, horizon: ForecastHorizon = selectedHorizon) {
    const requestId = detailRequestId.current + 1;
    detailRequestId.current = requestId;

    setAppState({ status: "detail-loading", stock });

    try {
      const detail = await getStockDetail(stock.ticker, horizon);
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
    const requestId = selectionRequestId.current + 1;
    selectionRequestId.current = requestId;
    detailRequestId.current += 1;

    try {
      const savePromise = savePrimaryStockQueue.current.then(() => savePrimaryStock(stock));
      savePrimaryStockQueue.current = savePromise.catch(() => undefined);
      await savePromise;

      if (selectionRequestId.current !== requestId) {
        return;
      }

      setSelectionError(null);
      setDetailError(null);
      loadDetailForStock(stock, selectedHorizon);
    } catch {
      if (selectionRequestId.current !== requestId) {
        return;
      }

      setSelectionError("Could not save your selected Stock. Try again.");
      setAppState({ status: "search" });
    }
  }

  async function handleChangeHorizon(horizon: ForecastHorizon) {
    if (horizon === selectedHorizon) {
      return;
    }

    setSelectedHorizon(horizon);

    try {
      const savePromise = saveForecastHorizonQueue.current.then(() => saveForecastHorizon(horizon));
      saveForecastHorizonQueue.current = savePromise.catch(() => undefined);
      await savePromise;
    } catch {
      setDetailError("Could not save your selected Forecast Horizon. Try again.");
    }

    if (appState.status === "detail" || appState.status === "detail-error" || appState.status === "detail-loading") {
      loadDetailForStock(appState.stock, horizon);
    }
  }

  async function handleChangeStock() {
    try {
      selectionRequestId.current += 1;
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
            accessibilityLabel={`Retry loading ${appState.stock.ticker} details`}
            accessibilityRole="button"
            onPress={() => loadDetailForStock(appState.stock, selectedHorizon)}
            style={styles.retryButton}
          >
            <Text style={styles.retryButtonText}>Try Again</Text>
          </Pressable>
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
          horizonOptions={FORECAST_HORIZONS.map((value) => ({
            value,
            label: FORECAST_HORIZON_LABELS[value],
          }))}
          onChangeHorizon={handleChangeHorizon}
          onChangeStock={handleChangeStock}
          selectedHorizon={selectedHorizon}
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
  retryButton: {
    alignItems: "center",
    backgroundColor: "#dbeafe",
    borderRadius: 16,
    marginTop: 24,
    padding: 16,
  },
  retryButtonText: {
    color: "#1d4ed8",
    fontSize: 16,
    fontWeight: "800",
  },
  changeButton: {
    alignItems: "center",
    backgroundColor: "#2563eb",
    borderRadius: 16,
    marginTop: 12,
    padding: 16,
  },
  changeButtonText: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "800",
  },
});
