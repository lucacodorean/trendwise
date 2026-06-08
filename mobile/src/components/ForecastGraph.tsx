import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import Svg, { Circle, Line, Path, Rect } from "react-native-svg";

import type {
  StockDetail,
  StockDetailForecastCandlestick,
  StockDetailForecastHistoricalPoint,
  StockDetailForecastLinePoint,
} from "../api/stocks";
import type { GraphType } from "../storage/graphType";

type GraphTypeOption = {
  value: GraphType;
  label: string;
};

type ChartPoint = {
  sequence: number;
  timestamp: string;
  value: number;
};

type ForecastGraphProps = {
  detail: StockDetail;
  graphTypeOptions: GraphTypeOption[];
  onChangeGraphType: (graphType: GraphType) => void;
  selectedGraphType: GraphType;
};

const CHART_WIDTH = 320;
const CHART_HEIGHT = 180;
const CHART_PADDING = 18;
const FORECAST_COLOR = "#60a5fa";
const HISTORICAL_COLOR = "#94a3b8";
const UNCERTAINTY_COLOR = "#93c5fd";
const DIVIDER_COLOR = "#facc15";

export function ForecastGraph({
  detail,
  graphTypeOptions,
  onChangeGraphType,
  selectedGraphType,
}: ForecastGraphProps) {
  const { forecast, horizonMetadata, stock } = detail;
  const historicalPoints = forecast.historicalPoints ?? [];
  const linePoints = forecast.linePoints ?? [];
  const candlesticks = forecast.candlesticks ?? [];
  const hasForecastData = selectedGraphType === "candlestick" ? candlesticks.length > 0 : linePoints.length > 0;

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <View>
          <Text style={styles.kicker}>Forecast Graph</Text>
          <Text style={styles.title}>
            {stock.ticker} {horizonMetadata.label} {selectedGraphType === "line" ? "Line" : "Candlestick"} Forecast
          </Text>
        </View>
        <View style={styles.segmentedControl}>
          {graphTypeOptions.map((option) => {
            const isSelected = option.value === selectedGraphType;

            return (
              <Pressable
                accessibilityLabel={getGraphTypeAccessibilityLabel(option.value)}
                accessibilityRole="button"
                accessibilityState={{ selected: isSelected }}
                key={option.value}
                onPress={() => onChangeGraphType(option.value)}
                style={[styles.segment, isSelected ? styles.segmentSelected : null]}
              >
                <Text style={[styles.segmentText, isSelected ? styles.segmentTextSelected : null]}>{option.label}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {!hasForecastData ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyTitle}>Forecast Graph data is unavailable</Text>
          <Text style={styles.emptyBody}>Graph data is unavailable for the selected horizon.</Text>
        </View>
      ) : (
        <View>
          <Svg height={CHART_HEIGHT} viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} width="100%">
            {selectedGraphType === "candlestick"
              ? renderCandlestickGraph(historicalPoints, candlesticks)
              : renderLineGraph(historicalPoints, linePoints)}
          </Svg>
          <View style={styles.legendRow}>
            <Text style={styles.legendHistorical}>
              {historicalPoints.length > 0 ? "Historical actual price" : "Historical context unavailable"}
            </Text>
            <Text style={styles.legendForecast}>Forecast</Text>
            <Text style={styles.legendUncertainty}>Uncertainty range</Text>
          </View>
          <Text style={styles.rangeCopy}>{getRangeCopy(selectedGraphType, historicalPoints, linePoints, candlesticks)}</Text>
        </View>
      )}
      <Text style={styles.freshness}>{forecast.freshnessLabel}</Text>
    </View>
  );
}

function renderLineGraph(
  historicalPoints: StockDetailForecastHistoricalPoint[],
  linePoints: StockDetailForecastLinePoint[],
) {
  const historicalChartPoints = historicalPoints.map((point) => ({
    sequence: point.sequence,
    timestamp: point.timestamp,
    value: point.value,
  }));
  const expectedPoints = linePoints.map((point) => ({
    sequence: point.sequence,
    timestamp: point.timestamp,
    value: point.expectedValue,
  }));
  const lowerPoints = linePoints.map((point) => ({
    sequence: point.sequence,
    timestamp: point.timestamp,
    value: point.lowerBound,
  }));
  const upperPoints = linePoints.map((point) => ({
    sequence: point.sequence,
    timestamp: point.timestamp,
    value: point.upperBound,
  }));
  const scale = createScale(
    [...historicalChartPoints, ...expectedPoints, ...lowerPoints, ...upperPoints],
    historicalChartPoints.length + linePoints.length,
  );
  const forecastStartX = scale.x(historicalChartPoints.length);

  return (
    <>
      <Line x1={forecastStartX} x2={forecastStartX} y1={8} y2={CHART_HEIGHT - 8} stroke={DIVIDER_COLOR} strokeWidth={2} />
      {historicalChartPoints.length > 1 ? (
        <Path d={toPath(historicalChartPoints, scale, 0)} fill="none" stroke={HISTORICAL_COLOR} strokeWidth={3} />
      ) : null}
      <Path d={toPath(expectedPoints, scale, historicalChartPoints.length)} fill="none" stroke={FORECAST_COLOR} strokeWidth={3} />
      {linePoints.length === 1 ? (
        renderSinglePointUncertainty(linePoints[0], scale, historicalChartPoints.length)
      ) : (
        <>
          <Path
            d={toPath(upperPoints, scale, historicalChartPoints.length)}
            fill="none"
            stroke={UNCERTAINTY_COLOR}
            strokeDasharray="6 6"
            strokeWidth={2}
          />
          <Path
            d={toPath(lowerPoints, scale, historicalChartPoints.length)}
            fill="none"
            stroke={UNCERTAINTY_COLOR}
            strokeDasharray="6 6"
            strokeWidth={2}
          />
        </>
      )}
      {expectedPoints.map((point, index) => (
        <Circle
          cx={scale.x(index + historicalChartPoints.length)}
          cy={scale.y(point.value)}
          fill={FORECAST_COLOR}
          key={`${point.timestamp}-${point.sequence}`}
          r={3}
        />
      ))}
    </>
  );
}

function renderSinglePointUncertainty(
  linePoint: StockDetailForecastLinePoint,
  scale: ReturnType<typeof createScale>,
  offset: number,
) {
  const x = scale.x(offset);

  return (
    <Line
      x1={x}
      x2={x}
      y1={scale.y(linePoint.upperBound)}
      y2={scale.y(linePoint.lowerBound)}
      stroke={UNCERTAINTY_COLOR}
      strokeDasharray="6 6"
      strokeWidth={2}
    />
  );
}

function renderCandlestickGraph(
  historicalPoints: StockDetailForecastHistoricalPoint[],
  candlesticks: StockDetailForecastCandlestick[],
) {
  const historicalChartPoints = historicalPoints.map((point) => ({
    sequence: point.sequence,
    timestamp: point.timestamp,
    value: point.value,
  }));
  const candleValues = candlesticks.flatMap((candlestick) => [
    { sequence: candlestick.sequence, timestamp: candlestick.timestamp, value: candlestick.open },
    { sequence: candlestick.sequence, timestamp: candlestick.timestamp, value: candlestick.high },
    { sequence: candlestick.sequence, timestamp: candlestick.timestamp, value: candlestick.low },
    { sequence: candlestick.sequence, timestamp: candlestick.timestamp, value: candlestick.close },
  ]);
  const scale = createScale(
    [...historicalChartPoints, ...candleValues],
    historicalChartPoints.length + candlesticks.length,
  );
  const forecastStartX = scale.x(historicalChartPoints.length);
  const candleWidth = Math.max(
    5,
    Math.min(14, CHART_WIDTH / Math.max(candlesticks.length + historicalChartPoints.length, 1) / 2),
  );

  return (
    <>
      <Line x1={forecastStartX} x2={forecastStartX} y1={8} y2={CHART_HEIGHT - 8} stroke={DIVIDER_COLOR} strokeWidth={2} />
      {historicalChartPoints.length > 1 ? (
        <Path d={toPath(historicalChartPoints, scale, 0)} fill="none" stroke={HISTORICAL_COLOR} strokeWidth={3} />
      ) : null}
      {candlesticks.map((candlestick, index) => {
        const x = scale.x(index + historicalChartPoints.length);
        const openY = scale.y(candlestick.open);
        const closeY = scale.y(candlestick.close);
        const highY = scale.y(candlestick.high);
        const lowY = scale.y(candlestick.low);
        const isBullish = candlestick.close >= candlestick.open;
        const color = isBullish ? "#86efac" : "#fca5a5";

        return (
          <React.Fragment key={`${candlestick.timestamp}-${candlestick.sequence}`}>
            <Line x1={x} x2={x} y1={highY} y2={lowY} stroke={color} strokeWidth={2} />
            <Rect
              fill={color}
              height={Math.max(Math.abs(closeY - openY), 3)}
              rx={2}
              width={candleWidth}
              x={x - candleWidth / 2}
              y={Math.min(openY, closeY)}
            />
          </React.Fragment>
        );
      })}
    </>
  );
}

function createScale(points: ChartPoint[], slotCount: number) {
  const values = points.map((point) => point.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const range = maxValue - minValue || 1;
  const domainPadding = range * 0.08;
  const paddedMin = minValue - domainPadding;
  const paddedMax = maxValue + domainPadding;
  const paddedRange = paddedMax - paddedMin || 1;
  const maxIndex = Math.max(slotCount - 1, 1);

  return {
    x: (index: number) => CHART_PADDING + (index / maxIndex) * (CHART_WIDTH - CHART_PADDING * 2),
    y: (value: number) =>
      CHART_HEIGHT - CHART_PADDING - ((value - paddedMin) / paddedRange) * (CHART_HEIGHT - CHART_PADDING * 2),
  };
}

function toPath(points: ChartPoint[], scale: ReturnType<typeof createScale>, offset: number): string {
  return points.map((point, index) => `${index === 0 ? "M" : "L"}${scale.x(index + offset)} ${scale.y(point.value)}`).join(" ");
}

function getRangeCopy(
  selectedGraphType: GraphType,
  historicalPoints: StockDetailForecastHistoricalPoint[],
  linePoints: StockDetailForecastLinePoint[],
  candlesticks: StockDetailForecastCandlestick[],
): string {
  const renderedForecastValues =
    selectedGraphType === "line"
      ? linePoints.flatMap((point) => [point.expectedValue, point.lowerBound, point.upperBound])
      : candlesticks.flatMap((candlestick) => [candlestick.open, candlestick.high, candlestick.low, candlestick.close]);
  const values = [
    ...historicalPoints.map((point) => point.value),
    ...renderedForecastValues,
  ];
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);

  return `Actual price scale ${formatPrice(minValue)} to ${formatPrice(maxValue)}`;
}

function formatPrice(value: number): string {
  return `$${value.toFixed(2)}`;
}

function getGraphTypeAccessibilityLabel(graphType: GraphType): string {
  return graphType === "line" ? "Select Line Forecast Graph" : "Select Candlestick Forecast Graph";
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#0f172a",
    borderRadius: 24,
    padding: 20,
  },
  header: {
    gap: 14,
  },
  kicker: {
    color: "#93c5fd",
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  title: {
    color: "#f8fafc",
    fontSize: 22,
    fontWeight: "900",
    marginTop: 6,
  },
  segmentedControl: {
    alignSelf: "flex-start",
    backgroundColor: "#1e293b",
    borderRadius: 999,
    flexDirection: "row",
    gap: 4,
    padding: 4,
  },
  segment: {
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  segmentSelected: {
    backgroundColor: "#60a5fa",
  },
  segmentText: {
    color: "#cbd5e1",
    fontSize: 12,
    fontWeight: "900",
  },
  segmentTextSelected: {
    color: "#082f49",
  },
  emptyState: {
    backgroundColor: "#1e293b",
    borderRadius: 18,
    marginTop: 16,
    padding: 18,
  },
  emptyTitle: {
    color: "#f8fafc",
    fontSize: 18,
    fontWeight: "900",
  },
  emptyBody: {
    color: "#cbd5e1",
    lineHeight: 20,
    marginTop: 8,
  },
  legendRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 8,
  },
  legendHistorical: {
    color: HISTORICAL_COLOR,
    fontSize: 12,
    fontWeight: "800",
  },
  legendForecast: {
    color: FORECAST_COLOR,
    fontSize: 12,
    fontWeight: "800",
  },
  legendUncertainty: {
    color: UNCERTAINTY_COLOR,
    fontSize: 12,
    fontWeight: "800",
  },
  rangeCopy: {
    color: "#cbd5e1",
    fontSize: 13,
    marginTop: 10,
  },
  freshness: {
    color: "#94a3b8",
    fontSize: 13,
    marginTop: 16,
  },
});
