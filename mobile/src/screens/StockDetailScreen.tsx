import { Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";

import type { ForecastHorizon, StockDetail } from "../api/stocks";

type HorizonOption = {
  value: ForecastHorizon;
  label: string;
};

type StockDetailScreenProps = {
  detail: StockDetail;
  detailError: string | null;
  horizonOptions: HorizonOption[];
  onChangeHorizon: (horizon: ForecastHorizon) => void;
  onChangeStock: () => void;
  selectedHorizon: ForecastHorizon;
};

export function StockDetailScreen({
  detail,
  detailError,
  horizonOptions,
  onChangeHorizon,
  onChangeStock,
  selectedHorizon,
}: StockDetailScreenProps) {
  const { forecast, market, prediction, stock } = detail;

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.heroCard}>
          <View style={styles.heroHeader}>
            <View>
              <Text style={styles.exchange}>{stock.exchange}</Text>
              <Text style={styles.ticker}>{stock.ticker}</Text>
            </View>

            <Pressable
              accessibilityLabel="Change selected Stock"
              accessibilityRole="button"
              onPress={onChangeStock}
              style={styles.changeButton}
            >
              <Text style={styles.changeButtonText}>Change</Text>
            </Pressable>
          </View>

          <Text style={styles.company}>{stock.companyName}</Text>
          <Text style={styles.price}>{formatPrice(market.latestPrice)}</Text>
          <Text style={styles.dailyChange}>
            {formatDailyChange(market.dailyChange, market.dailyChangePercent)}
          </Text>
          <Text style={styles.freshness}>{market.freshnessLabel}</Text>
        </View>

        {detailError ? <Text style={styles.error}>{detailError}</Text> : null}

        <View style={styles.metricRow}>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Prediction direction</Text>
            <Text style={styles.metricValue}>{formatTitleCase(prediction.direction)}</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Risk Level</Text>
            <Text style={styles.metricValue}>{formatTitleCase(prediction.riskLevel)}</Text>
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardKicker}>Forecast horizon</Text>
          <View style={styles.horizonChips}>
            {horizonOptions.map((option) => {
              const isSelected = option.value === selectedHorizon;

              return (
                <Pressable
                  accessibilityLabel={`Select ${option.label} Forecast Horizon`}
                  accessibilityRole="button"
                  accessibilityState={{ selected: isSelected }}
                  key={option.value}
                  onPress={() => onChangeHorizon(option.value)}
                  style={[styles.horizonChip, isSelected ? styles.horizonChipSelected : null]}
                >
                  <Text style={[styles.horizonChipText, isSelected ? styles.horizonChipTextSelected : null]}>
                    {option.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>
          <View style={styles.predictionFacts}>
            <Text style={styles.fact}>{formatConfidence(prediction.confidence)}</Text>
            <Text style={styles.fact}>{formatExpectedChange(prediction.expectedChangePercent)}</Text>
          </View>
          <Text style={styles.cardFreshness}>{prediction.freshnessLabel}</Text>
        </View>

        <Text style={styles.disclaimer}>{detail.disclaimer}</Text>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Forecast graph unavailable</Text>
          <Text style={styles.cardBody}>
            Forecast graph rendering comes later. Backend graph data is loaded for the {detail.horizonMetadata.label} horizon with {detail.horizonMetadata.expectedForecastPointCount} forecast points.
          </Text>
          <Text style={styles.cardFreshness}>{forecast.freshnessLabel}</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function formatPrice(value: number | null): string {
  return typeof value === "number" ? `$${value.toFixed(2)}` : "Unavailable";
}

function formatDailyChange(change: number | null, percent: number | null): string {
  return typeof change === "number" && typeof percent === "number"
    ? `${formatSignedCurrency(change)} (${formatSignedPercent(percent)}) today`
    : "Change unavailable";
}

function formatConfidence(value: number | null): string {
  return typeof value === "number"
    ? `${Math.round(value * 100)}% confidence`
    : "Confidence unavailable";
}

function formatExpectedChange(value: number | null): string {
  return typeof value === "number"
    ? `${formatSignedPercent(value)} expected change`
    : "Expected change unavailable";
}

function formatSignedPercent(value: number): string {
  const prefix = value >= 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
}

function formatSignedCurrency(value: number): string {
  const prefix = value >= 0 ? "+" : "-";
  return `${prefix}$${Math.abs(value).toFixed(2)}`;
}

function formatTitleCase(value: string | null): string {
  return value ? value.charAt(0).toUpperCase() + value.slice(1) : "Unavailable";
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: "#f8fafc",
    flex: 1,
  },
  content: {
    gap: 16,
    padding: 24,
    paddingBottom: 32,
  },
  heroCard: {
    backgroundColor: "#0f172a",
    borderRadius: 28,
    padding: 24,
  },
  heroHeader: {
    alignItems: "flex-start",
    flexDirection: "row",
    justifyContent: "space-between",
  },
  exchange: {
    color: "#93c5fd",
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 1.2,
    marginBottom: 8,
    textTransform: "uppercase",
  },
  ticker: {
    color: "#f8fafc",
    fontSize: 46,
    fontWeight: "900",
  },
  changeButton: {
    backgroundColor: "#dbeafe",
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  changeButtonText: {
    color: "#1d4ed8",
    fontSize: 14,
    fontWeight: "800",
  },
  company: {
    color: "#cbd5e1",
    fontSize: 18,
    fontWeight: "700",
    marginTop: 8,
  },
  price: {
    color: "#ffffff",
    fontSize: 40,
    fontWeight: "900",
    marginTop: 28,
  },
  dailyChange: {
    color: "#bfdbfe",
    fontSize: 18,
    fontWeight: "800",
    marginTop: 8,
  },
  freshness: {
    color: "#94a3b8",
    fontSize: 13,
    marginTop: 14,
  },
  error: {
    color: "#b91c1c",
  },
  metricRow: {
    flexDirection: "row",
    gap: 12,
  },
  metricCard: {
    backgroundColor: "#ffffff",
    borderRadius: 20,
    flex: 1,
    padding: 16,
  },
  metricLabel: {
    color: "#64748b",
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0.7,
    textTransform: "uppercase",
  },
  metricValue: {
    color: "#0f172a",
    fontSize: 21,
    fontWeight: "900",
    marginTop: 10,
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 24,
    padding: 20,
  },
  cardKicker: {
    color: "#2563eb",
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1,
    marginBottom: 8,
    textTransform: "uppercase",
  },
  cardTitle: {
    color: "#0f172a",
    fontSize: 24,
    fontWeight: "900",
  },
  horizonChips: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 12,
  },
  horizonChip: {
    alignItems: "center",
    backgroundColor: "#e2e8f0",
    borderRadius: 999,
    justifyContent: "center",
    minHeight: 44,
    minWidth: 44,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  horizonChipSelected: {
    backgroundColor: "#2563eb",
  },
  horizonChipText: {
    color: "#334155",
    fontSize: 13,
    fontWeight: "800",
  },
  horizonChipTextSelected: {
    color: "#ffffff",
  },
  predictionFacts: {
    gap: 8,
    marginTop: 16,
  },
  fact: {
    color: "#334155",
    fontSize: 16,
    fontWeight: "700",
  },
  cardBody: {
    color: "#475569",
    fontSize: 15,
    lineHeight: 22,
    marginTop: 12,
  },
  cardFreshness: {
    color: "#64748b",
    fontSize: 13,
    marginTop: 16,
  },
  disclaimer: {
    color: "#64748b",
    fontSize: 12,
    lineHeight: 18,
  },
});
