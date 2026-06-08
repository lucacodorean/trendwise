import AsyncStorage from "@react-native-async-storage/async-storage";

const GRAPH_TYPE_KEY = "trendwise.graphType";

export type GraphType = "line" | "candlestick";

export const DEFAULT_GRAPH_TYPE: GraphType = "line";
export const GRAPH_TYPES: GraphType[] = ["line", "candlestick"];
export const GRAPH_TYPE_LABELS: Record<GraphType, string> = {
  line: "Line",
  candlestick: "Candlestick",
};

export function isGraphType(value: unknown): value is GraphType {
  return typeof value === "string" && GRAPH_TYPES.includes(value as GraphType);
}

export async function loadGraphType(): Promise<GraphType> {
  try {
    const rawValue = await AsyncStorage.getItem(GRAPH_TYPE_KEY);
    if (!rawValue) {
      return DEFAULT_GRAPH_TYPE;
    }

    const parsed: unknown = JSON.parse(rawValue);
    return isGraphType(parsed) ? parsed : DEFAULT_GRAPH_TYPE;
  } catch {
    return DEFAULT_GRAPH_TYPE;
  }
}

export async function saveGraphType(graphType: GraphType): Promise<void> {
  await AsyncStorage.setItem(GRAPH_TYPE_KEY, JSON.stringify(graphType));
}
