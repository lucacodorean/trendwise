/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type StockDetailPrediction = {
    confidence: (number | null);
    direction: ('bullish' | 'bearish' | 'neutral' | null);
    expectedChangePercent: (number | null);
    freshnessLabel: string;
    generatedAt: (string | null);
    riskLevel: ('low' | 'medium' | 'high' | null);
    status: string;
};

