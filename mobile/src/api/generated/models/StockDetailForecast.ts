/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { StockDetailForecastCandlestick } from './StockDetailForecastCandlestick';
import type { StockDetailForecastHistoricalPoint } from './StockDetailForecastHistoricalPoint';
import type { StockDetailForecastLinePoint } from './StockDetailForecastLinePoint';
export type StockDetailForecast = {
    candlesticks?: Array<StockDetailForecastCandlestick>;
    freshnessLabel: string;
    generatedAt: (string | null);
    historicalPoints?: Array<StockDetailForecastHistoricalPoint>;
    linePoints?: Array<StockDetailForecastLinePoint>;
    status: string;
};

