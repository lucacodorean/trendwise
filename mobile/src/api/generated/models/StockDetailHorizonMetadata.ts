/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ForecastHorizon } from './ForecastHorizon';
export type StockDetailHorizonMetadata = {
    calendarBasis: 'regular_market_trading_time' | 'calendar_period';
    expectedForecastPointCount: number;
    externalFactorWeightScale: number;
    label: string;
    newsWindowDays: number;
    pricePointBasis: 'trading_session';
    timeBasis: 'regular_market' | 'calendar_period';
    value: ForecastHorizon;
};
