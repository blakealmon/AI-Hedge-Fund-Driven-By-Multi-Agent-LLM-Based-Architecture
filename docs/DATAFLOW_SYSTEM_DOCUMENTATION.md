# Data Flow System Documentation

## Overview

The TradingAgents data flow system provides a comprehensive data integration layer that connects multiple financial data sources to the agent framework. It handles data retrieval, caching, processing, and standardization across various APIs and data providers.

## Architecture

### Core Components

#### 1. Interface Layer (`interface.py`)
- **Purpose**: Central unified API for all data access
- **Features**: Multi-source aggregation, caching, standardization
- **Dependencies**: All utility modules, configuration system

#### 2. Data Source Utilities
- `yfin_utils.py` - Yahoo Finance integration
- `stockstats_utils.py` - Technical indicator calculations  
- `googlenews_utils.py` - Google News API
- `reddit_utils.py` - Reddit social sentiment
- `finnhub_utils.py` - Finnhub financial data

#### 3. Configuration System (`config.py`)
- **Purpose**: Manages API keys, endpoints, and data source settings
- **Features**: Environment variable support, secure credential management

#### 4. Utility Functions (`utils.py`)
- **Purpose**: Common data processing and helper functions
- **Features**: Data formatting, validation, transformation

## Data Sources

### 1. Yahoo Finance (`yfin_utils.py`)

**Core Class: `YFinanceUtils`**

Uses decorator pattern for automatic ticker initialization:
```python
@decorate_all_methods(init_ticker)
class YFinanceUtils:
```

**Key Methods**:

##### `get_stock_data(symbol, start_date, end_date, save_path=None)`
- **Purpose**: Retrieve historical stock price data
- **Parameters**:
  - `symbol`: Ticker symbol (e.g., "AAPL")
  - `start_date`: Start date in YYYY-MM-DD format
  - `end_date`: End date in YYYY-MM-DD format (inclusive)
  - `save_path`: Optional path for data caching
- **Returns**: Pandas DataFrame with OHLCV data
- **Features**: 
  - Automatic date adjustment for inclusivity
  - Built-in caching support
  - Error handling for invalid symbols

##### `get_stock_info(symbol)`
- **Purpose**: Fetch comprehensive company information
- **Parameters**: `symbol`: Ticker symbol
- **Returns**: Dictionary with company metadata
- **Data Includes**:
  - Market cap, P/E ratio, dividend yield
  - Sector, industry classification
  - Financial metrics and ratios
  - Executive information

**Implementation Features**:
- **Decorator Pattern**: `@init_ticker` automatically creates `yf.Ticker` objects
- **Error Handling**: Graceful handling of invalid tickers or network issues
- **Data Validation**: Ensures data quality and completeness

### 2. Technical Indicators (`stockstats_utils.py`)

**Purpose**: Calculate technical analysis indicators from price data.

**Supported Indicator Categories**:

#### Moving Averages
- **SMA (Simple Moving Average)**: `close_50_sma`, `close_200_sma`
- **EMA (Exponential Moving Average)**: `close_10_ema`
- **VWMA (Volume Weighted Moving Average)**: `vwma`

#### Momentum Indicators  
- **RSI (Relative Strength Index)**: `rsi`
- **MACD Family**: `macd`, `macds`, `macdh`

#### Volatility Indicators
- **Bollinger Bands**: `boll`, `boll_ub`, `boll_lb`
- **ATR (Average True Range)**: `atr`

**Core Function**:
```python
def get_stockstats_indicators_report_online(
    ticker, start_date, end_date, indicators
):
    """Calculate specified technical indicators for a stock"""
```

**Features**:
- **Flexible Indicator Selection**: Choose any combination of indicators
- **Data Integration**: Automatically fetches price data if needed
- **Quality Validation**: Ensures sufficient data for accurate calculations
- **Performance Optimization**: Efficient calculation algorithms

### 3. News Data (`googlenews_utils.py`, `finnhub_utils.py`)

#### Google News Integration
**Purpose**: Retrieve and analyze news articles from Google News.

**Key Functions**:
```python
def get_googlenews_data(ticker, curr_date, look_back_days):
    """Fetch news articles for a specific ticker"""
```

**Features**:
- **Date Range Support**: Configurable lookback periods
- **Relevance Filtering**: Focus on ticker-specific news
- **Content Extraction**: Full article text when available
- **Sentiment Preparation**: Structured for sentiment analysis

#### Finnhub Integration  
**Purpose**: Professional-grade financial news and insider data.

**Core Functions**:

##### News Data
```python
def get_finnhub_news(ticker, curr_date, look_back_days):
    """Retrieve professional financial news"""
```

**Features**:
- **Professional Sources**: High-quality financial news
- **Structured Format**: Consistent headline and summary format
- **Time-based Organization**: Chronological news organization
- **Relevance Scoring**: Ticker-specific relevance

##### Insider Sentiment
```python  
def get_finnhub_company_insider_sentiment(ticker, curr_date, look_back_days):
    """Retrieve insider trading sentiment from SEC filings"""
```

**Data Includes**:
- **Net Buying/Selling**: Aggregate insider transaction direction
- **Monthly Share Purchase Ratio (MSPR)**: Standardized insider activity metric
- **Time Series Data**: Historical insider sentiment trends
- **Transaction Details**: Individual insider transaction summaries

### 4. Social Media Data (`reddit_utils.py`)

**Purpose**: Analyze social sentiment from Reddit financial communities.

**Core Functions**:

##### `fetch_top_from_category(category, limit=100)`
- **Purpose**: Retrieve top posts from financial subreddits
- **Categories**: "hot", "new", "top", "rising"
- **Features**: 
  - Content filtering for financial relevance
  - Score and engagement metrics
  - Comment analysis capability

##### `get_reddit_sentiment_analysis(ticker, curr_date, look_back_days)`
- **Purpose**: Comprehensive Reddit sentiment analysis
- **Features**:
  - **Multi-subreddit Coverage**: r/stocks, r/investing, r/SecurityAnalysis, etc.
  - **Sentiment Scoring**: Positive/negative/neutral classification
  - **Volume Analysis**: Discussion volume trends
  - **Engagement Metrics**: Upvotes, comments, awards

## Interface Layer Functions

### Core Data Access Functions

#### `get_YFin_data_online(ticker, start_date, end_date)`
**Purpose**: Online Yahoo Finance data retrieval with caching.
**Features**:
- **Real-time Data**: Latest market information
- **Automatic Caching**: Reduces API calls and improves performance
- **Data Validation**: Ensures data quality and completeness

#### `get_comprehensive_sentiment_analysis(ticker, curr_date, look_back_days)`
**Purpose**: Multi-source sentiment aggregation.
**Sources Combined**:
- Reddit discussions and sentiment
- News article sentiment
- Insider trading patterns
- Social media buzz

**Output Format**:
- **Aggregated Score**: Combined sentiment metric
- **Source Breakdown**: Individual source contributions
- **Trend Analysis**: Sentiment changes over time
- **Confidence Metrics**: Reliability indicators

#### `get_market_context_analysis(ticker, curr_date)`
**Purpose**: Broad market context for individual stock analysis.
**Features**:
- **Sector Performance**: Relative sector strength
- **Market Indices**: SPY, QQQ, DIA performance
- **Economic Indicators**: Relevant economic data
- **Peer Comparison**: Similar stock performance

### Caching System

#### Cache Architecture
- **Hierarchical Structure**: Organized by ticker, date, and data type
- **Automatic Expiration**: Time-based cache invalidation
- **Selective Refresh**: Update only stale data
- **Storage Optimization**: Efficient disk usage

#### Cache Location
```
dataflows/data_cache/
├── {ticker}/
│   ├── {date}/
│   │   ├── news_data.json
│   │   ├── market_data.csv
│   │   ├── sentiment_data.json
│   │   └── insider_data.json
│   └── metadata.json
```

#### Cache Management
```python
def get_data_in_range(ticker, start_date, end_date, data_type, data_dir):
    """Retrieve cached data with automatic cache management"""
```

**Features**:
- **Range Queries**: Efficient date range retrieval
- **Partial Updates**: Update only missing date ranges
- **Data Validation**: Ensure cache integrity
- **Automatic Cleanup**: Remove expired cache entries

## Configuration Management

### Configuration Structure (`config.py`)

```python
# API Configuration
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
GOOGLE_NEWS_API_KEY = os.getenv("GOOGLE_NEWS_API_KEY")

# Data Source Settings
DATA_DIR = get_config().get("data_cache_dir", "./dataflows/data_cache")
ONLINE_MODE = get_config().get("online_tools", True)

# Cache Settings  
CACHE_EXPIRY_HOURS = 24
MAX_CACHE_SIZE_GB = 10
```

### Environment Variables

Required environment variables for full functionality:
- `FINNHUB_API_KEY`: Professional financial data access
- `REDDIT_CLIENT_ID`: Reddit API authentication
- `REDDIT_CLIENT_SECRET`: Reddit API authentication  
- `GOOGLE_NEWS_API_KEY`: Google News API access
- `TRADINGAGENTS_RESULTS_DIR`: Custom results directory

### Configuration Functions

#### `get_config()` and `set_config()`
- **Purpose**: Dynamic configuration management
- **Features**: Runtime configuration updates, validation

#### Data Source Selection
```python
if config["online_tools"]:
    # Use live APIs
    tools = [get_YFin_data_online, get_stockstats_indicators_report_online]
else:
    # Use cached data
    tools = [get_YFin_data, get_stockstats_indicators_report]
```

## Data Processing Pipeline

### 1. Data Retrieval
- **API Calls**: Make requests to external data sources
- **Rate Limiting**: Respect API rate limits
- **Error Handling**: Graceful handling of API failures

### 2. Data Validation
- **Schema Validation**: Ensure data structure consistency
- **Quality Checks**: Identify and handle data anomalies
- **Completeness Verification**: Ensure all required fields present

### 3. Data Standardization
- **Format Conversion**: Convert to standard formats (DataFrame, JSON)
- **Date Standardization**: Consistent date/time formats
- **Numerical Formatting**: Standardized number formats and units

### 4. Data Enrichment
- **Derived Metrics**: Calculate additional useful metrics
- **Cross-Reference**: Link data across sources
- **Context Addition**: Add relevant market context

### 5. Caching and Storage
- **Efficient Storage**: Optimized file formats
- **Metadata Management**: Track data lineage and freshness
- **Retrieval Optimization**: Fast data access patterns

## Performance Optimization

### Concurrent Processing
```python
from concurrent.futures import ThreadPoolExecutor

def parallel_data_fetch(tickers, date_range):
    """Fetch data for multiple tickers concurrently"""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_ticker_data, ticker) for ticker in tickers]
        results = [future.result() for future in futures]
```

### Memory Management
- **Streaming Processing**: Handle large datasets efficiently
- **Memory Monitoring**: Track memory usage
- **Garbage Collection**: Proactive memory cleanup

### Network Optimization
- **Connection Pooling**: Reuse HTTP connections
- **Compression**: Use data compression when available
- **Retry Logic**: Intelligent retry mechanisms

## Error Handling and Reliability

### Error Categories
1. **Network Errors**: API timeouts, connection failures
2. **Data Errors**: Invalid data, missing fields
3. **Rate Limiting**: API quota exceeded
4. **Authentication Errors**: Invalid API keys

### Error Recovery Strategies
```python
def robust_api_call(api_function, *args, **kwargs):
    """Make API calls with automatic retry and fallback"""
    for attempt in range(3):
        try:
            return api_function(*args, **kwargs)
        except RateLimitError:
            time.sleep(exponential_backoff(attempt))
        except NetworkError:
            if attempt == 2:
                return fallback_data(*args, **kwargs)
```

### Monitoring and Logging
- **API Call Logging**: Track all external API interactions
- **Performance Metrics**: Monitor response times and success rates
- **Error Reporting**: Detailed error logs for debugging

## Integration with Agent System

### Data Flow to Agents
1. **Agent Requests**: Agents specify data requirements
2. **Interface Layer**: Routes requests to appropriate data sources
3. **Data Processing**: Processes and formats data for agent consumption
4. **Response Delivery**: Returns structured data to requesting agents

### Tool Integration
```python
# Agent tools automatically use the data flow system
tools = [
    toolkit.get_YFin_data_online,
    toolkit.get_stockstats_indicators_report_online,
    toolkit.get_comprehensive_sentiment_analysis,
]
```

This comprehensive data flow system ensures that TradingAgents have access to high-quality, real-time financial data from multiple sources while maintaining performance, reliability, and cost efficiency.
