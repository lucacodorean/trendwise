/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ForecastHorizon } from './ForecastHorizon';
import type { StockDetailForecast } from './StockDetailForecast';
import type { StockDetailMarket } from './StockDetailMarket';
import type { StockDetailPrediction } from './StockDetailPrediction';
import type { StockDetailStock } from './StockDetailStock';
export type StockDetailResponse = {
    disclaimer: string;
    forecast: StockDetailForecast;
    horizon: ForecastHorizon;
    market: StockDetailMarket;
    prediction: StockDetailPrediction;
    stock: StockDetailStock;
};

