# TradingAgents Framework - Complete Documentation

## Table of Contents

1. [Framework Overview](#framework-overview)
2. [Architecture Summary](#architecture-summary)
3. [Module Documentation](#module-documentation)
4. [Quick Start Guide](#quick-start-guide)
5. [Configuration Guide](#configuration-guide)
6. [Development Guide](#development-guide)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

## Framework Overview

TradingAgents is a sophisticated multi-agent LLM framework for financial trading analysis. It combines the power of large language models with specialized financial data sources to provide comprehensive investment analysis through collaborative AI agents.

### Key Features

- **Multi-Agent Architecture**: Specialized AI agents for different aspects of financial analysis
- **Comprehensive Data Integration**: Multiple financial data sources and APIs
- **Interactive CLI Interface**: Rich terminal interface with real-time progress tracking
- **Debate-Driven Decision Making**: Structured argumentation between agents
- **Memory-Enhanced Learning**: Agents learn from past decisions and outcomes
- **Multi-LLM Support**: Support for multiple LLM providers (OpenAI, Anthropic, Google, etc.)
- **Configurable Analysis Depth**: Adjustable thoroughness of analysis
- **Risk Management Integration**: Comprehensive risk assessment and management

### Core Workflow

```
User Input → Analyst Team → Research Team → Trading Team → Risk Management → Final Decision
```

1. **User Configuration**: Select ticker, date, analysts, and analysis parameters
2. **Analyst Team**: Technical, social, news, and fundamental analysis
3. **Research Team**: Bull vs bear debate and investment recommendation
4. **Trading Team**: Execution strategy development
5. **Risk Management**: Multi-perspective risk analysis and final decision
6. **Results**: Comprehensive reports and trading recommendations

## Architecture Summary

### System Components

```
TradingAgents Framework
├── CLI Module (cli/)
│   ├── Interactive Interface
│   ├── Real-time Progress Tracking
│   ├── Rich Terminal Display
│   └── User Input Management
├── Core Framework (tradingagents/)
│   ├── Agent System
│   │   ├── Analyst Team
│   │   ├── Research Team  
│   │   ├── Trading Team
│   │   └── Risk Management Team
│   ├── Graph System
│   │   ├── Workflow Orchestration
│   │   ├── State Management
│   │   ├── Conditional Logic
│   │   └── Learning Integration
│   ├── Data Flow System
│   │   ├── Multi-Source Integration
│   │   ├── Caching Layer
│   │   ├── Data Processing
│   │   └── API Management
│   └── Configuration System
│       ├── LLM Configuration
│       ├── Data Source Settings
│       └── Analysis Parameters
```

### Agent Teams

#### Analyst Team
- **Market Analyst**: Technical analysis with indicators and patterns
- **Social Media Analyst**: Sentiment analysis from social platforms
- **News Analyst**: Financial news analysis and event detection
- **Fundamentals Analyst**: Financial metrics and company health

#### Research Team
- **Bull Researcher**: Develops bullish investment arguments
- **Bear Researcher**: Develops bearish investment arguments  
- **Research Manager**: Facilitates debate and makes investment decisions

#### Trading Team
- **Trader**: Develops specific execution strategies and trade plans

#### Risk Management Team
- **Aggressive Debator**: Advocates for higher-risk strategies
- **Conservative Debator**: Promotes risk-averse approaches
- **Neutral Debator**: Provides balanced risk perspective
- **Portfolio Manager**: Makes final risk-adjusted decisions

### Data Sources

- **Market Data**: Yahoo Finance, Alpha Vantage
- **Technical Indicators**: StockStats, TA-Lib
- **News Data**: Finnhub, Google News
- **Social Sentiment**: Reddit, Twitter
- **Fundamental Data**: SEC EDGAR, financial statements
- **Insider Data**: SEC insider trading filings

## Module Documentation

### 1. CLI Module (`cli/`)

**Comprehensive Documentation**: [CLI Module Documentation](./CLI_MODULE_DOCUMENTATION.md)

**Key Components**:
- `main.py`: Main CLI application with rich interface
- `models.py`: Data models and enums
- `utils.py`: Interactive input utilities and validation

**Features**:
- Interactive configuration wizard
- Real-time analysis progress tracking
- Rich terminal interface with color-coded panels
- Comprehensive report generation and display

### 2. Core Framework (`tradingagents/`)

**Comprehensive Documentation**: [TradingAgents Core Documentation](./TRADINGAGENTS_CORE_DOCUMENTATION.md)

**Key Components**:
- `default_config.py`: Central configuration management
- Agent system with specialized AI agents
- Graph system for workflow orchestration
- Data flow system for multi-source integration

### 3. Agent System (`tradingagents/agents/`)

**Comprehensive Documentation**: [Agent System Documentation](./AGENT_SYSTEM_DOCUMENTATION.md)

**Key Features**:
- Specialized agents for different analysis domains
- Structured debate and argumentation systems
- Memory-enhanced learning and decision improvement
- Tool integration for data access and analysis

### 4. Graph System (`tradingagents/graph/`)

**Comprehensive Documentation**: [Graph System Documentation](./GRAPH_SYSTEM_DOCUMENTATION.md)

**Key Features**:
- LangGraph-based workflow orchestration
- Dynamic conditional routing
- State management and validation
- Error handling and recovery mechanisms

### 5. Data Flow System (`tradingagents/dataflows/`)

**Comprehensive Documentation**: [Data Flow System Documentation](./DATAFLOW_SYSTEM_DOCUMENTATION.md)

**Key Features**:
- Multi-source data integration
- Intelligent caching and performance optimization
- Standardized data processing and formatting
- API management and rate limiting

## Quick Start Guide

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/TauricResearch/TradingAgents.git
   cd TradingAgents
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export FINNHUB_API_KEY="your-finnhub-api-key"
   export REDDIT_CLIENT_ID="your-reddit-client-id"
   export REDDIT_CLIENT_SECRET="your-reddit-client-secret"
   ```

### Basic Usage

1. **Run Analysis**:
   ```bash
   python -m cli.main analyze
   ```

2. **Follow Interactive Prompts**:
   - Enter ticker symbol (e.g., AAPL, SPY)
   - Select analysis date
   - Choose analyst team members
   - Configure research depth
   - Select LLM provider and models

3. **Monitor Progress**: Watch real-time analysis progress in the terminal

4. **Review Results**: Comprehensive analysis reports and trading recommendations

### Example Configuration

```
Ticker: AAPL
Date: 2024-01-15
Analysts: Market, Social, News, Fundamentals
Research Depth: Deep (5 rounds)
LLM Provider: OpenAI
Quick Thinking Model: gpt-4o-mini
Deep Thinking Model: o4-mini
```

## Configuration Guide

### Core Configuration (`tradingagents/default_config.py`)

```python
DEFAULT_CONFIG = {
    # Directories
    "project_dir": "./",
    "results_dir": "./results",
    "data_cache_dir": "./dataflows/data_cache",
    
    # LLM Settings
    "llm_provider": "openai",
    "deep_think_llm": "o4-mini",
    "quick_think_llm": "gpt-4o-mini",
    "backend_url": "https://api.openai.com/v1",
    
    # Analysis Settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    
    # Data Settings
    "online_tools": True,
}
```

### LLM Provider Configuration

#### OpenAI
```python
{
    "llm_provider": "openai",
    "backend_url": "https://api.openai.com/v1",
    "deep_think_llm": "o4-mini",
    "quick_think_llm": "gpt-4o-mini",
}
```

#### Anthropic
```python
{
    "llm_provider": "anthropic", 
    "backend_url": "https://api.anthropic.com/",
    "deep_think_llm": "claude-3-5-sonnet-latest",
    "quick_think_llm": "claude-3-5-haiku-latest",
}
```

#### Google
```python
{
    "llm_provider": "google",
    "deep_think_llm": "gemini-2.5-pro-preview-06-05",
    "quick_think_llm": "gemini-2.0-flash",
}
```

### Analysis Depth Configuration

- **Shallow (1 round)**: Quick analysis with minimal debate
- **Medium (3 rounds)**: Moderate analysis with balanced debate
- **Deep (5 rounds)**: Comprehensive analysis with extensive debate

### Data Source Configuration

```python
# Online mode (live data)
"online_tools": True

# Offline mode (cached data)
"online_tools": False
```

## Development Guide

### Adding New Agents

1. **Create Agent File**: `tradingagents/agents/{category}/{agent_name}.py`

2. **Implement Agent Function**:
   ```python
   def create_new_agent(llm, toolkit, memory=None):
       def agent_node(state):
           # Agent logic here
           return updated_state
       return agent_node
   ```

3. **Register in Graph Setup**: Add to `graph/setup.py`

4. **Update Conditional Logic**: Add routing logic in `graph/conditional_logic.py`

### Adding New Data Sources

1. **Create Utility Module**: `tradingagents/dataflows/{source}_utils.py`

2. **Implement Data Functions**:
   ```python
   def get_data_from_source(ticker, start_date, end_date):
       # Data retrieval logic
       return processed_data
   ```

3. **Register in Interface**: Add to `dataflows/interface.py`

4. **Update Toolkit**: Add tools to agent toolkit

### Adding New LLM Providers

1. **Update Graph Setup**: Add provider case in `graph/trading_graph.py`

2. **Update CLI Utils**: Add provider options in `cli/utils.py`

3. **Test Integration**: Ensure compatibility with existing agents

### Memory System Extension

1. **Extend Memory Classes**: Add new memory types in `agents/utils/memory.py`

2. **Update State Management**: Modify state structures if needed

3. **Integrate Learning**: Connect memory to decision-making processes

## API Reference

### Core Classes

#### `TradingAgentsGraph`
```python
class TradingAgentsGraph:
    def __init__(self, selected_analysts, debug=False, config=None)
    def stream(self, initial_state, **args)
    def process_signal(self, final_decision)
```

#### `MessageBuffer`
```python
class MessageBuffer:
    def add_message(self, message_type, content)
    def add_tool_call(self, tool_name, args)
    def update_agent_status(self, agent, status)
    def update_report_section(self, section_name, content)
```

#### `FinancialSituationMemory`
```python
class FinancialSituationMemory:
    def get_memories(self, situation, n_matches=2)
    def add_memory(self, situation, decision, context)
    def update_memory(self, memory_id, outcome)
```

### Key Functions

#### Data Access
```python
# Market data
get_YFin_data_online(ticker, start_date, end_date)
get_stockstats_indicators_report_online(ticker, start_date, end_date, indicators)

# News data
get_finnhub_news(ticker, curr_date, look_back_days)
get_googlenews_data(ticker, curr_date, look_back_days)

# Social sentiment
get_reddit_sentiment_analysis(ticker, curr_date, look_back_days)
```

#### Agent Creation
```python
# Analyst agents
create_market_analyst(llm, toolkit)
create_social_analyst(llm, toolkit)
create_news_analyst(llm, toolkit)
create_fundamentals_analyst(llm, toolkit)

# Research agents  
create_bull_researcher(llm, memory)
create_bear_researcher(llm, memory)
create_research_manager(llm, memory)
```

## Troubleshooting

### Common Issues

#### 1. API Key Issues
**Problem**: Missing or invalid API keys
**Solution**: 
- Verify environment variables are set correctly
- Check API key validity with provider
- Ensure proper permissions for API keys

#### 2. LLM Provider Issues
**Problem**: LLM provider unavailable or rate limited
**Solution**:
- Switch to alternative provider
- Implement retry logic with backoff
- Check API quotas and limits

#### 3. Data Source Issues
**Problem**: Data source unavailable or returning errors
**Solution**:
- Enable cached mode: `"online_tools": False`
- Check API status of data providers
- Verify ticker symbols are valid

#### 4. Memory Issues
**Problem**: Out of memory during analysis
**Solution**:
- Reduce analysis depth
- Clear data cache
- Monitor memory usage

#### 5. Performance Issues
**Problem**: Slow analysis performance
**Solution**:
- Use faster LLM models for quick thinking
- Enable caching for repeated analyses
- Reduce number of selected analysts

### Debug Mode

Enable debug mode for detailed logging:
```python
graph = TradingAgentsGraph(selected_analysts, debug=True, config=config)
```

### Log Analysis

Check logs in results directory:
```
results/{ticker}/{date}/
├── reports/
│   └── *.md
└── message_tool.log
```

### Configuration Validation

Validate configuration before analysis:
```python
def validate_config(config):
    required_keys = ["llm_provider", "deep_think_llm", "quick_think_llm"]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ConfigurationError(f"Missing config keys: {missing_keys}")
```

## Performance Optimization

### Best Practices

1. **Model Selection**:
   - Use lightweight models for quick thinking tasks
   - Reserve powerful models for complex reasoning
   - Balance cost and performance

2. **Caching Strategy**:
   - Enable data caching for repeated analyses
   - Use offline mode when possible
   - Regular cache cleanup

3. **Analysis Configuration**:
   - Adjust research depth based on needs
   - Select relevant analysts only
   - Configure appropriate debate rounds

4. **Resource Management**:
   - Monitor API usage and costs
   - Implement rate limiting
   - Use concurrent processing where possible

### Monitoring

Track key metrics:
- **Analysis Time**: Total time for complete analysis
- **API Calls**: Number and cost of LLM API calls
- **Data Usage**: Amount of data retrieved and cached
- **Memory Usage**: Peak memory consumption
- **Error Rates**: Frequency of errors and recovery

This comprehensive documentation provides everything needed to understand, configure, and extend the TradingAgents framework for sophisticated financial analysis and trading decision-making.
