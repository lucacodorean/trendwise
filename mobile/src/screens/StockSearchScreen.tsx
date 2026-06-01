import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { searchStocks, type PrimaryStock } from "../api/stocks";

type StockSearchScreenProps = {
  onSelect: (stock: PrimaryStock) => void;
  selectionError: string | null;
};

export function StockSearchScreen({
  onSelect,
  selectionError,
}: StockSearchScreenProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PrimaryStock[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    async function loadResults() {
      setIsLoading(true);
      setError(null);

      try {
        const nextResults = await searchStocks(query);
        if (isActive) {
          setResults(nextResults);
        }
      } catch {
        if (isActive) {
          setError("Stock search is unavailable. Check the backend and try again.");
          setResults([]);
        }
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    }

    loadResults();

    return () => {
      isActive = false;
    };
  }, [query]);

  const isShowingExamples = query.trim() === "";

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.header}>
        <Text style={styles.kicker}>Trendwise</Text>
        <Text style={styles.title}>Start with a supported Stock</Text>
        <Text style={styles.body}>
          Search US-listed common Stocks by ticker or company name.
        </Text>
      </View>

      <TextInput
        accessibilityLabel="Search ticker or company"
        autoCapitalize="characters"
        onChangeText={setQuery}
        placeholder="Search ticker or company"
        placeholderTextColor="#94a3b8"
        style={styles.input}
        value={query}
      />

      {isShowingExamples ? <Text style={styles.sectionLabel}>Examples</Text> : null}

      {isLoading ? <ActivityIndicator color="#60a5fa" style={styles.loader} /> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {selectionError ? <Text style={styles.error}>{selectionError}</Text> : null}
      {!isLoading && !error && results.length === 0 ? (
        <Text style={styles.empty}>
          No supported US-listed common Stocks matched your search.
        </Text>
      ) : null}

      <ScrollView
        contentContainerStyle={isShowingExamples ? styles.exampleResults : styles.results}
        keyboardShouldPersistTaps="handled"
      >
        {results.map((stock) =>
          isShowingExamples ? (
            <Pressable
              accessibilityLabel={`Select ${stock.ticker}, ${stock.companyName}, ${stock.exchange}`}
              accessibilityRole="button"
              key={stock.ticker}
              onPress={() => onSelect(stock)}
              style={styles.exampleChip}
            >
              <Text style={styles.exampleTicker}>{stock.ticker}</Text>
              <Text style={styles.exampleCompany}>{stock.companyName}</Text>
            </Pressable>
          ) : (
            <Pressable
              accessibilityLabel={`Select ${stock.ticker}, ${stock.companyName}, ${stock.exchange}`}
              accessibilityRole="button"
              key={stock.ticker}
              onPress={() => onSelect(stock)}
              style={styles.resultRow}
            >
              <View>
                <Text style={styles.ticker}>{stock.ticker}</Text>
                <Text style={styles.company}>{stock.companyName}</Text>
              </View>
              <Text style={styles.exchange}>{stock.exchange}</Text>
            </Pressable>
          ),
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: {
    backgroundColor: "#0f172a",
    flex: 1,
    padding: 24,
  },
  header: {
    marginBottom: 24,
    marginTop: 32,
  },
  kicker: {
    color: "#60a5fa",
    fontSize: 14,
    fontWeight: "700",
    letterSpacing: 1.5,
    marginBottom: 12,
    textTransform: "uppercase",
  },
  title: {
    color: "#f8fafc",
    fontSize: 32,
    fontWeight: "800",
    marginBottom: 12,
  },
  body: {
    color: "#cbd5e1",
    fontSize: 16,
    lineHeight: 24,
  },
  input: {
    backgroundColor: "#f8fafc",
    borderRadius: 18,
    color: "#0f172a",
    fontSize: 18,
    paddingHorizontal: 18,
    paddingVertical: 16,
  },
  sectionLabel: {
    color: "#93c5fd",
    fontSize: 13,
    fontWeight: "700",
    letterSpacing: 1,
    marginTop: 20,
    textTransform: "uppercase",
  },
  loader: {
    marginTop: 24,
  },
  error: {
    color: "#fecaca",
    marginTop: 18,
  },
  empty: {
    color: "#cbd5e1",
    lineHeight: 22,
    marginTop: 18,
  },
  exampleResults: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 12,
    paddingBottom: 24,
  },
  exampleChip: {
    backgroundColor: "#dbeafe",
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  exampleTicker: {
    color: "#1d4ed8",
    fontSize: 15,
    fontWeight: "800",
  },
  exampleCompany: {
    color: "#334155",
    fontSize: 12,
    marginTop: 2,
  },
  results: {
    gap: 12,
    marginTop: 12,
    paddingBottom: 24,
  },
  resultRow: {
    alignItems: "center",
    backgroundColor: "#f8fafc",
    borderRadius: 18,
    flexDirection: "row",
    justifyContent: "space-between",
    padding: 18,
  },
  ticker: {
    color: "#0f172a",
    fontSize: 18,
    fontWeight: "800",
  },
  company: {
    color: "#475569",
    fontSize: 14,
    marginTop: 4,
  },
  exchange: {
    color: "#2563eb",
    fontSize: 13,
    fontWeight: "800",
  },
});
