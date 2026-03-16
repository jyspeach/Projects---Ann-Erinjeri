# Time Series Analysis of Crime Rates

## Overview
This project performs time series analysis on historical crime rate data over a period of 118 years.

The goal is to analyze trends, assess stationarity, and identify an appropriate ARIMA model for forecasting.

## Key Findings

The data shows:

- An overall upward trend
- Non-constant variance
- Non-stationary behavior

Log transformation and differencing were applied to stabilize variance and achieve stationarity. :contentReference[oaicite:4]{index=4}

## Model Selection

Two candidate models were evaluated:

ARIMA(0,1,3)  
ARIMA(1,1,0)

The final selected model was:

**ARIMA(1,1,0)**

based on lower AIC and BIC values.

## Evaluation Metrics
- AIC
- BIC
- Residual analysis
- ACF and PACF plots

## Tools Used
- R Programming
- Time Series Analysis
- ARIMA Modelling

## Author
Ann Erinjeri
