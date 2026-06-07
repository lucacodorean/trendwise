/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ForecastHorizon } from './ForecastHorizon';
import type { StockDetailPricePointBasis } from './StockDetailPricePointBasis';
export type StockDetailHorizonMetadata = {
    calendarBasis: 'regular_market_trading_time' | 'calendar_period';
    expectedForecastPointCount: number;
    externalFactorWeightScale: number;
    label: string;
    newsWindowDays: number;
    pricePointBasis: StockDetailPricePointBasis;
    timeBasis: 'regular_market' | 'calendar_period';
    value: ForecastHorizon;
};

