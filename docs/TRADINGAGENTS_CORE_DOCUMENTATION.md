# TradingAgents Core Module Documentation

## Overview

The TradingAgents core module is a sophisticated multi-agent framework for financial trading analysis. It orchestrates various specialized AI agents to perform comprehensive market analysis, research, trading strategy development, and risk management.

## Architecture Overview

The framework is organized into several key subsystems:

### 1. Core Configuration (`tradingagents/default_config.py`)

**Purpose**: Central configuration management for the entire framework.

```python
DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": "/Users/yluo/Documents/Code/ScAI/FR1-data",
    "data_cache_dir": os.path.join(..., "dataflows/data_cache"),
    
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "o4-mini",
    "quick_think_llm": "gpt-4o-mini", 
    "backend_url": "https://api.openai.com/v1",
    
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    
    # Tool settings
    "online_tools": True,
}
```

**Key Configuration Areas**:
- **Directory Management**: Project, results, and data directories
- **LLM Configuration**: Provider, model selection, and endpoints
- **Debate Parameters**: Rounds and recursion limits
- **Tool Settings**: Online vs offline data sources

## 2. Graph System (`tradingagents/graph/`)

### Core Graph Components

#### `trading_graph.py` - Main Orchestrator

**Purpose**: Central orchestration class that manages the entire trading analysis workflow.

**Key Features**:
- **Multi-LLM Support**: OpenAI, Anthropic, Google, OpenRouter, Ollama
- **Memory Management**: Specialized memory systems for different agent types
- **Tool Integration**: Comprehensive toolkit for data analysis
- **Component Coordination**: Manages all subsystem interactions

**Core Class: `TradingAgentsGraph`**

```python
class TradingAgentsGraph:
    def __init__(self, selected_analysts=["market", "social", "news", "fundamentals"], 
                 debug=False, config: Dict[str, Any] = None):
```

**Initialization Process**:
1. **LLM Setup**: Configure deep and quick thinking LLMs based on provider
2. **Memory Creation**: Initialize specialized memory systems for each agent type
3. **Tool Node Creation**: Set up data processing and analysis tools
4. **Component Assembly**: Initialize all graph components

**Supported LLM Providers**:
- **OpenAI**: GPT models, o-series reasoning models
- **Anthropic**: Claude family (Haiku, Sonnet, Opus)
- **Google**: Gemini models
- **OpenRouter**: Various open-source models
- **Ollama**: Local model support

#### Component Architecture

##### `conditional_logic.py` - Decision Making
- **Purpose**: Implements conditional logic for agent workflows
- **Features**: Dynamic routing based on analysis results

##### `setup.py` - Graph Construction  
- **Purpose**: Builds the computational graph structure
- **Features**: Node definition, edge creation, workflow assembly

##### `propagation.py` - State Management
- **Purpose**: Manages state propagation through the agent network
- **Features**: State transitions, data flow control

##### `reflection.py` - Learning System
- **Purpose**: Implements reflection and learning mechanisms
- **Features**: Memory updates, decision improvement

##### `signal_processing.py` - Output Processing
- **Purpose**: Processes and formats final trading signals
- **Features**: Signal extraction, formatting, validation

## 3. Agent System (`tradingagents/agents/`)

### Agent Categories

#### Analysts (`agents/analysts/`)

##### `market_analyst.py` - Technical Analysis Specialist

**Purpose**: Performs comprehensive technical analysis using market indicators.

**Key Features**:
- **Indicator Selection**: Chooses optimal technical indicators for analysis
- **Multi-Category Coverage**: Moving averages, MACD, momentum, volatility, volume
- **Smart Selection Logic**: Avoids redundancy, selects complementary indicators

**Supported Indicators**:

**Moving Averages**:
- `close_50_sma`: Medium-term trend identification
- `close_200_sma`: Long-term trend confirmation  
- `close_10_ema`: Short-term momentum capture

**MACD Family**:
- `macd`: Core momentum indicator
- `macds`: Signal line for crossovers
- `macdh`: Histogram for momentum strength

**Momentum Indicators**:
- `rsi`: Relative Strength Index for overbought/oversold conditions

**Volatility Indicators**:
- `boll`, `boll_ub`, `boll_lb`: Bollinger Bands for volatility analysis
- `atr`: Average True Range for risk management

**Volume Indicators**:
- `vwma`: Volume-weighted moving average

**Analysis Workflow**:
1. **Data Retrieval**: Calls `get_YFin_data` for price data
2. **Indicator Calculation**: Uses `get_stockstats_indicators_report`
3. **Pattern Recognition**: Identifies trends and signals
4. **Report Generation**: Creates detailed markdown reports with tables

##### Additional Analysts

**Social Media Analyst** (`social_media_analyst.py`):
- **Purpose**: Analyzes social sentiment and discussion trends
- **Data Sources**: Reddit, Twitter, financial forums
- **Features**: Sentiment scoring, volume analysis, trend detection

**News Analyst** (`news_analyst.py`):
- **Purpose**: Processes and analyzes financial news
- **Data Sources**: Financial news APIs, press releases
- **Features**: Sentiment analysis, event detection, impact assessment

**Fundamentals Analyst** (`fundamentals_analyst.py`):
- **Purpose**: Fundamental analysis of financial metrics
- **Data Sources**: Financial statements, SEC filings
- **Features**: Ratio analysis, growth metrics, valuation models

#### Managers (`agents/managers/`)

##### `research_manager.py` - Research Coordination

**Purpose**: Coordinates research activities and makes final investment decisions.

**Key Features**:
- **Debate Facilitation**: Manages bull vs bear discussions
- **Memory Integration**: Uses past experiences to improve decisions
- **Decision Making**: Makes definitive Buy/Sell/Hold recommendations

**Core Function: `research_manager_node(state)`**

**Input Processing**:
- Market research reports from all analysts
- Bull and bear researcher arguments
- Historical memory of similar situations

**Decision Process**:
1. **Argument Evaluation**: Analyzes bull vs bear positions
2. **Historical Context**: Reviews past similar decisions
3. **Strategic Planning**: Develops detailed investment plans
4. **Final Recommendation**: Makes clear trading decision

**Output Format**:
- **Recommendation**: Clear Buy/Sell/Hold decision
- **Rationale**: Detailed explanation of decision logic  
- **Strategic Actions**: Specific implementation steps
- **Risk Considerations**: Identified risks and mitigation

##### `risk_manager.py` - Risk Assessment
- **Purpose**: Evaluates and manages trading risks
- **Features**: Portfolio risk analysis, position sizing, stop-loss recommendations

#### Researchers (`agents/researchers/`)

##### Bull and Bear Researchers
- **Bull Researcher** (`bull_researcher.py`): Argues for bullish positions
- **Bear Researcher** (`bear_researcher.py`): Argues for bearish positions

**Debate System**:
- **Structured Arguments**: Evidence-based position development
- **Counter-Arguments**: Response to opposing viewpoints
- **Research Depth**: Configurable debate rounds for thoroughness

#### Risk Management (`agents/risk_mgmt/`)

##### Risk Debators
- **Aggressive Debator** (`aggressive_debator.py`): Advocates for higher-risk strategies
- **Conservative Debator** (`conservative_debator.py`): Promotes risk-averse approaches  
- **Neutral Debator** (`neutral_debator.py`): Provides balanced risk perspective

#### Trader (`agents/trader/`)

##### `trader.py` - Execution Planning
- **Purpose**: Develops specific trading execution strategies
- **Features**: Order planning, timing optimization, execution logistics

### Agent Utilities (`agents/utils/`)

#### `agent_states.py` - State Management
- **Purpose**: Defines state structures for different agent types
- **Classes**: `AgentState`, `InvestDebateState`, `RiskDebateState`

#### `agent_utils.py` - Common Utilities
- **Purpose**: Shared utilities across all agents
- **Features**: Common functions, data processing, formatting

#### `memory.py` - Memory Systems
- **Purpose**: Implements memory and learning for agents
- **Class**: `FinancialSituationMemory`

**Memory Features**:
- **Situation Matching**: Finds similar past scenarios
- **Learning Integration**: Incorporates past mistakes
- **Context Retrieval**: Relevant historical context

## 4. Data Flow System (`tradingagents/dataflows/`)

### Core Interface (`interface.py`)

**Purpose**: Central data access layer providing unified interface to all data sources.

**Key Features**:
- **Multi-Source Integration**: News, market data, social sentiment, insider information
- **Caching System**: Efficient data storage and retrieval
- **Configuration Management**: Flexible data source configuration

**Major Functions**:

#### News Data
```python
def get_finnhub_news(ticker, curr_date, look_back_days):
    """Retrieve news about a company within a time frame"""
```

#### Insider Sentiment
```python
def get_finnhub_company_insider_sentiment(ticker, curr_date, look_back_days):
    """Retrieve insider sentiment from SEC filings"""
```

#### Social Media Data
```python
def get_reddit_sentiment_analysis(ticker, curr_date, look_back_days):
    """Analyze Reddit sentiment for ticker"""
```

#### Technical Data
```python
def get_YFin_data_online(ticker, start_date, end_date):
    """Retrieve Yahoo Finance market data"""
```

### Data Source Utilities

#### `yfin_utils.py` - Yahoo Finance Integration

**Purpose**: Provides comprehensive Yahoo Finance data access.

**Key Features**:
- **Decorator Pattern**: `@init_ticker` for automatic ticker initialization
- **Multiple Data Types**: Price data, company info, financial statements
- **Flexible Date Ranges**: Configurable time periods

**Core Class: `YFinanceUtils`**

**Methods**:
- `get_stock_data(symbol, start_date, end_date)`: Historical price data
- `get_stock_info(symbol)`: Company information and metrics

#### Additional Data Sources

**`stockstats_utils.py`**: Technical indicator calculations
**`googlenews_utils.py`**: Google News API integration  
**`reddit_utils.py`**: Reddit API for social sentiment
**`finnhub_utils.py`**: Finnhub API for news and insider data

### Configuration System (`config.py`)

**Purpose**: Manages data source configuration and API keys.

**Features**:
- **Environment Variables**: Secure API key management
- **Source Selection**: Choose between online and cached data
- **Cache Management**: Configurable caching strategies

## Workflow Architecture

### Analysis Pipeline

1. **Initialization Phase**:
   - User selects analysts and configuration
   - Graph initializes with specified components
   - Memory systems prepare for analysis

2. **Analyst Phase**:
   - Market Analyst: Technical analysis with indicators
   - Social Analyst: Sentiment analysis from social media
   - News Analyst: News sentiment and event analysis
   - Fundamentals Analyst: Financial metrics analysis

3. **Research Phase**:
   - Bull Researcher: Develops bullish arguments
   - Bear Researcher: Develops bearish counter-arguments
   - Research Manager: Evaluates debates and decides

4. **Trading Phase**:
   - Trader: Develops execution strategy based on research

5. **Risk Management Phase**:
   - Risk Debators: Evaluate from different risk perspectives
   - Portfolio Manager: Makes final risk-adjusted decision

### State Management

**State Flow**:
```
Initial State → Analyst Reports → Research Debate → Trading Plan → Risk Assessment → Final Decision
```

**State Components**:
- **Ticker Information**: Symbol, company name, analysis date
- **Analyst Reports**: Individual analyst findings
- **Debate States**: Bull/bear arguments and decisions
- **Trading Plans**: Execution strategies
- **Risk Assessments**: Risk evaluations and mitigation

### Memory and Learning

**Memory Types**:
- **Bull Memory**: Bullish scenario experiences
- **Bear Memory**: Bearish scenario experiences  
- **Trader Memory**: Execution experiences
- **Judge Memory**: Decision-making experiences
- **Risk Manager Memory**: Risk management experiences

**Learning Process**:
1. **Situation Encoding**: Convert current situation to searchable format
2. **Memory Retrieval**: Find similar past scenarios
3. **Experience Integration**: Incorporate lessons learned
4. **Decision Enhancement**: Improve current decision with past insights

## Integration Points

### CLI Integration
- **Configuration Flow**: CLI selections update core config
- **Status Reporting**: Real-time agent status updates
- **Report Generation**: Structured output for CLI display

### External APIs
- **Yahoo Finance**: Market data and company information
- **Finnhub**: News, insider sentiment, financial data
- **Google News**: News article retrieval and analysis
- **Reddit**: Social sentiment analysis

### LLM Integration
- **Multi-Provider Support**: Flexible LLM backend selection
- **Model Specialization**: Different models for different thinking types
- **Cost Optimization**: Efficient model usage patterns

## Configuration and Customization

### Debate Configuration
- **Round Limits**: Control analysis depth
- **Timeout Settings**: Prevent infinite loops
- **Quality Thresholds**: Ensure meaningful debates

### Data Source Configuration
- **Online vs Offline**: Toggle between live and cached data
- **API Credentials**: Secure credential management
- **Cache Settings**: Control data freshness

### Agent Configuration
- **Analyst Selection**: Choose which analysts to include
- **Memory Settings**: Control learning behavior
- **Tool Selection**: Enable/disable specific data tools

This comprehensive architecture enables sophisticated multi-agent financial analysis with robust data integration, flexible configuration, and advanced learning capabilities.
