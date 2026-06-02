/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ForecastHorizon } from '../models/ForecastHorizon';
import type { StockDetailResponse } from '../models/StockDetailResponse';
import type { StockSearchResponse } from '../models/StockSearchResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class StocksService {
    /**
     * Search Stocks
     * @returns StockSearchResponse Successful Response
     * @throws ApiError
     */
    public static searchStocks({
        q = '',
    }: {
        q?: string,
    }): CancelablePromise<StockSearchResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/stocks/search',
            query: {
                'q': q,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Stock Detail
     * @returns StockDetailResponse Successful Response
     * @throws ApiError
     */
    public static getStockDetail({
        ticker,
        horizon = '1d',
    }: {
        ticker: string,
        horizon?: ForecastHorizon,
    }): CancelablePromise<StockDetailResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/stocks/{ticker}/detail',
            path: {
                'ticker': ticker,
            },
            query: {
                'horizon': horizon,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
