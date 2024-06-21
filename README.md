### Pairs Trading in Cryptocurrency Markets

#### Introduction

Pairs trading is a strategy that seeks to identify short-term pricing anomalies between assets and capitalize on the convergence of their prices back to their long-term historical levels. This strategy involves taking a long position in the asset that is undervalued relative to another asset while simultaneously taking a short position in the latter. The strategy hinges on two key assumptions: first, that the assets in the pair are cointegrated and their spread exhibits mean-reversion characteristics; and second, that this relationship will continue to hold throughout the trading period.

In classical pairs trading, the search space for pairs is typically restricted to equities, often chosen from the same sector to ensure similar economic fundamentals. However, as this strategy becomes more widely implemented in equities, it might be more susceptible to alpha decay, reducing potential profits. This project aims to leverage the pairs trading strategy to identify and exploit pricing inefficiencies in cryptocurrency markets.

#### Objectives

1. **Identify Cointegrated Pairs**: Conduct thorough analysis to identify pairs of cryptocurrencies that exhibit strong cointegration, ensuring they have a stable long-term relationship despite short-term deviations.
2. **Implement and Compare Trading Strategies**: Evaluate the effectiveness of different trading strategies with distinct stop-loss mechanisms to determine the most robust and profitable approach.

#### Data Processing

- **Data Acquisition**: Historical price data from Binance API, covering daily closing prices from January 2020 to January 2023.
- **Data Cleaning**: Involves timestamp conversion, setting index, handling missing values, and filtering relevant columns.
- **Data Processing**: Includes normalization, visual inspection, cointegration testing, and stationarity check.

#### Split Data

The dataset is divided into three subsets:

1. **January 2020 to December 2021**
2. **January 2021 to December 2022**
3. **January 2022 to December 2023**

The most recent data from January 2023 onward is used as the test dataset, ensuring robust backtesting and validation across various time periods.

#### Trading Strategy

- **Whole Period Cointegration Analysis**: Analyze cointegration over a comprehensive period (2020-2023) and test two stop-loss strategies: continuous return drop stop-loss and Bollinger Band stop-loss.
- **Yearly Cointegration Analysis**: Perform cointegration analysis on a yearly basis and test the same two stop-loss strategies.

#### Strategy Implementation

1. **Identify Best Pairs**: Based on cointegration tests, identify pairs like XRPUSDT and BCHUSDT with stable long-term relationships.
2. **Rolling Regression**: Use a rolling window of 8760 hours to compute rolling intercept, beta, and spread.
3. **Spread Calculation**: Calculate the spread using the rolling intercept and beta.
4. **Entry and Exit Conditions**: Set entry at 1.96, exit at 0.25, and a minimum threshold at 0.005 based on the normalized spread.
5. **Position Calculation**: Use forward fill for XRPUSDT positions and rolling beta for BCHUSDT positions.
6. **PNL Calculation**: Compute hourly PNL and cumulative PNL based on log returns.

#### Backtesting and Results

Backtest the strategy on three training datasets (2021, 2022, 2023) and one test dataset (2024), observing metrics like cumulative return, Sharpe ratio, and drawdown.

#### Risk Control

1. **Execution Risk**: Address risks associated with using limit orders vs. market orders in live trading scenarios.
2. **Model Risk**: Ensure cointegration stability with a two-year rolling window and use rolling beta for accurate spread calculation.
3. **Market Risk**: Implement a stop-loss strategy to mitigate losses when the spread deviates significantly from the mean.

### Conclusion

The project validates the effectiveness of pairs trading strategies in the cryptocurrency market and explores the impact of different stop-loss mechanisms on trading performance. By comparing these strategies, we aim to provide insights into the optimal design of market-neutral trading strategies.
