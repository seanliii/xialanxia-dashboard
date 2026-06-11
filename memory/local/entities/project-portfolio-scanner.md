# project-portfolio-scanner

**Type:** project
**Updated:** 2026-03-20T11:11:55.241Z

## Facts

- Uses real-time price data for trading decisions
- Source of real-time price data was changed from Stooq to Yahoo Finance
- Contains trade trigger logic with safeguards for price deviation
- Automatically fetches real-time stock prices from Yahoo Finance as primary source
- Includes risk management checks for price deviations above 30% triggers
- Automates dashboard updates with latest market data
- Favors Yahoo Finance API over Stooq for fetching real-time small-cap stock prices
- Automated tool the user runs daily to update stock portfolio prices, returns, and holding days.

## Connected to

- [[tool-yahoo-finance]] — uses as price data source
- [[tool-stooq]] — previously used price data source
- [[entity-ocul]] — monitors for trading triggers
- [[entity-upxi]] — monitors stock price of
- [[tool-yahoo-finance]] — uses for stock price data
- [[tool-stooq]] — uses as alternative for stock price data
- [[tool-yahoo-finance]] — uses
- [[tool-stooq]] — uses
- [[tool-yahoo-finance]] — favors over tool-stooq for real-time small-cap stock prices
- [[project-xialanxia-dashboard]] — loads dynamic portfolio data from (reverse)
- [[project-xialanxia-dashboard]] — uses dynamic data updates from (reverse)
- [[project-xialanxia-dashboard]] — visualizes data refreshed by (reverse)

## Activity

- 2026-03-20: Mentioned in conversation
- 2026-03-20: Mentioned in conversation
- 2026-03-20: Mentioned in conversation
- 2026-03-20: Mentioned in conversation
