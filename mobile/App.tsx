import { StatusBar } from "expo-status-bar";
import { SafeAreaView, StyleSheet, Text, View } from "react-native";

export default function App() {
  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="auto" />
      <View style={styles.card}>
        <Text style={styles.kicker}>Trendwise</Text>
        <Text style={styles.title}>Stock Forecasting Prototype</Text>
        <Text style={styles.body}>
          Select a supported stock to view forecasts, predictions, summaries,
          and market context. Forecasts are informational estimates only.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#0f172a",
    justifyContent: "center",
    padding: 24,
  },
  card: {
    backgroundColor: "#f8fafc",
    borderRadius: 24,
    padding: 24,
  },
  kicker: {
    color: "#2563eb",
    fontSize: 14,
    fontWeight: "700",
    letterSpacing: 1.5,
    marginBottom: 12,
    textTransform: "uppercase",
  },
  title: {
    color: "#0f172a",
    fontSize: 28,
    fontWeight: "800",
    marginBottom: 12,
  },
  body: {
    color: "#334155",
    fontSize: 16,
    lineHeight: 24,
  },
});
