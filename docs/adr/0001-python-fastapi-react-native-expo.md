# ADR 0001: Python FastAPI Backend And React Native Expo Frontend

## Status

Accepted

## Context

The application needs a Python backend for market data ingestion, ML forecasting, background jobs, and API delivery. It also needs a native mobile frontend to display Stock Forecasts, Stock Predictions, comparison graphs, Company News, and Stock Summaries.

The first milestone is an off-production prototype.

## Decision

Use FastAPI for the Python backend API and Expo React Native with TypeScript for the mobile app.

FastAPI owns the OpenAPI schema. The mobile app consumes generated TypeScript API types/client code from the backend OpenAPI contract.

## Consequences

FastAPI supports typed request/response models, OpenAPI generation, async provider calls, and straightforward Python ML integration.

Expo accelerates mobile prototype development and avoids unnecessary native configuration early.

The mobile production artifact is a native iOS/Android build, not a long-running Docker container. Docker may standardize local frontend tooling later, but Expo development runs separately from the backend Compose stack for the prototype.
