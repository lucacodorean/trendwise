import { Pressable, SafeAreaView, StyleSheet, Text, View } from "react-native";

import type { PrimaryStock } from "../api/stocks";

type StockDetailPlaceholderScreenProps = {
  stock: PrimaryStock;
  onChangeStock: () => void;
};

export function StockDetailPlaceholderScreen({
  stock,
  onChangeStock,
}: StockDetailPlaceholderScreenProps) {
  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.card}>
        <Text style={styles.kicker}>Primary Stock</Text>
        <Text style={styles.ticker}>{stock.ticker}</Text>
        <Text style={styles.company}>{stock.companyName}</Text>
        <Text style={styles.exchange}>{stock.exchange}</Text>

        <View style={styles.notice}>
          <Text style={styles.noticeTitle}>Forecasts and predictions are not available yet.</Text>
          <Text style={styles.noticeBody}>
            Trendwise is informational only and does not provide trading recommendations.
          </Text>
        </View>

        <Pressable accessibilityRole="button" onPress={onChangeStock} style={styles.button}>
          <Text style={styles.buttonText}>Change Stock</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: "#0f172a",
    flex: 1,
    justifyContent: "center",
    padding: 24,
  },
  card: {
    backgroundColor: "#f8fafc",
    borderRadius: 28,
    padding: 24,
  },
  kicker: {
    color: "#2563eb",
    fontSize: 13,
    fontWeight: "800",
    letterSpacing: 1.2,
    marginBottom: 12,
    textTransform: "uppercase",
  },
  ticker: {
    color: "#0f172a",
    fontSize: 44,
    fontWeight: "900",
  },
  company: {
    color: "#334155",
    fontSize: 20,
    fontWeight: "700",
    marginTop: 6,
  },
  exchange: {
    color: "#64748b",
    fontSize: 15,
    marginTop: 4,
  },
  notice: {
    backgroundColor: "#e0f2fe",
    borderRadius: 18,
    marginTop: 24,
    padding: 16,
  },
  noticeTitle: {
    color: "#0f172a",
    fontSize: 16,
    fontWeight: "800",
    marginBottom: 8,
  },
  noticeBody: {
    color: "#334155",
    lineHeight: 22,
  },
  button: {
    alignItems: "center",
    backgroundColor: "#2563eb",
    borderRadius: 16,
    marginTop: 22,
    padding: 16,
  },
  buttonText: {
    color: "#ffffff",
    fontSize: 16,
    fontWeight: "800",
  },
});
