/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
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
}
