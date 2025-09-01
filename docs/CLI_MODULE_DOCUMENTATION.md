# CLI Module Documentation

## Overview

The CLI module provides a comprehensive command-line interface for the TradingAgents multi-agent LLM financial trading framework. It offers an interactive terminal interface with rich visualizations, real-time progress tracking, and comprehensive reporting capabilities.

## Architecture

The CLI module consists of four main components:

### 1. `cli/__init__.py`
- **Purpose**: Empty initialization file for the CLI package
- **Status**: Empty file - serves as package marker

### 2. `cli/main.py`
- **Purpose**: Main CLI application entry point with rich terminal interface
- **Dependencies**: 
  - `typer` - CLI framework
  - `rich` - Terminal formatting and visualization
  - `questionary` - Interactive prompts (imported via utils)
- **Key Components**:

#### Core Classes

##### `MessageBuffer`
A sophisticated message and state management system for real-time CLI updates.

**Attributes:**
- `messages`: Deque storing recent messages with timestamps
- `tool_calls`: Deque tracking tool invocations
- `agent_status`: Dictionary tracking status of all agents
- `report_sections`: Dictionary storing different report sections
- `current_report`: Currently displayed report section
- `final_report`: Complete consolidated report

**Methods:**
- `add_message(message_type, content)`: Adds timestamped messages
- `add_tool_call(tool_name, args)`: Tracks tool usage
- `update_agent_status(agent, status)`: Updates agent progress
- `update_report_section(section_name, content)`: Updates report sections

#### Core Functions

##### `create_layout()`
Creates a sophisticated Rich layout with multiple panels:
- **Header**: Welcome message and branding
- **Progress**: Real-time agent status tracking
- **Messages**: Live message and tool call feed
- **Analysis**: Current report display
- **Footer**: Statistics and metrics

##### `update_display(layout, spinner_text=None)`
Dynamically updates all layout panels with:
- **Progress Table**: Color-coded agent status with teams
- **Messages Table**: Recent messages with truncation
- **Analysis Panel**: Current markdown-formatted reports
- **Statistics**: Tool calls, LLM calls, and report counts

##### `get_user_selections()`
Interactive user input collection with:
- ASCII art welcome screen
- Step-by-step configuration panels
- Ticker symbol selection
- Analysis date validation
- Analyst team selection
- Research depth configuration
- LLM provider and model selection

##### `run_analysis()`
Main analysis orchestration function:
- Initializes TradingAgentsGraph with user selections
- Creates result directories and logging
- Streams analysis results with real-time updates
- Manages agent status transitions
- Generates comprehensive final reports

##### `display_complete_report(final_state)`
Formats and displays the final analysis report with:
- Team-based organization (Analyst, Research, Trading, Risk, Portfolio)
- Rich markdown formatting
- Color-coded panels by team
- Comprehensive results presentation

#### Agent Status Management

The CLI tracks five main teams with specific agents:

1. **Analyst Team**:
   - Market Analyst
   - Social Analyst  
   - News Analyst
   - Fundamentals Analyst

2. **Research Team**:
   - Bull Researcher
   - Bear Researcher
   - Research Manager

3. **Trading Team**:
   - Trader

4. **Risk Management Team**:
   - Risky Analyst
   - Neutral Analyst
   - Safe Analyst

5. **Portfolio Management**:
   - Portfolio Manager

#### Report Section Management

Seven main report sections are tracked:
- `market_report`: Market analysis results
- `sentiment_report`: Social sentiment analysis
- `news_report`: News analysis results
- `fundamentals_report`: Fundamental analysis
- `investment_plan`: Research team decisions
- `trader_investment_plan`: Trading strategy
- `final_trade_decision`: Portfolio management decision

### 3. `cli/models.py`
- **Purpose**: Data models and enums for CLI operations
- **Dependencies**: `pydantic`, `enum`

#### Models

##### `AnalystType(str, Enum)`
Enumeration of available analyst types:
- `MARKET = "market"`: Market analysis specialist
- `SOCIAL = "social"`: Social media sentiment analyst
- `NEWS = "news"`: News and media analyst  
- `FUNDAMENTALS = "fundamentals"`: Fundamental analysis specialist

### 4. `cli/utils.py`
- **Purpose**: Utility functions for interactive user input and validation
- **Dependencies**: `questionary`

#### Core Functions

##### `get_ticker() -> str`
- **Purpose**: Interactive ticker symbol input with validation
- **Features**: 
  - Green-styled prompt
  - Non-empty validation
  - Automatic uppercase conversion
  - Exit handling

##### `get_analysis_date() -> str`
- **Purpose**: Date input with YYYY-MM-DD format validation
- **Features**:
  - Regex pattern validation
  - DateTime parsing validation
  - Green-styled prompt
  - Error handling

##### `select_analysts() -> List[AnalystType]`
- **Purpose**: Multi-select checkbox for analyst team configuration
- **Features**:
  - Interactive checkbox interface
  - Keyboard shortcuts (Space, 'a', Enter)
  - Minimum selection validation
  - Color-coded selections

##### `select_research_depth() -> int`
- **Purpose**: Research depth level selection
- **Options**:
  - Shallow (1 round): Quick research with minimal debate
  - Medium (3 rounds): Moderate debate and strategy discussion
  - Deep (5 rounds): Comprehensive research with in-depth debate

##### `select_shallow_thinking_agent(provider) -> str`
- **Purpose**: Quick-thinking LLM model selection
- **Supported Providers**:
  - **OpenAI**: GPT-4o-mini, GPT-4.1-nano, GPT-4.1-mini, GPT-4o
  - **Anthropic**: Claude Haiku 3.5, Claude Sonnet 3.5, Claude Sonnet 3.7, Claude Sonnet 4
  - **Google**: Gemini 2.0 Flash-Lite, Gemini 2.0 Flash, Gemini 2.5 Flash
  - **OpenRouter**: Meta Llama 4 Scout, Llama 3.3 8B, Gemini 2.0 Flash
  - **Ollama**: llama3.1, llama3.2 (local models)

##### `select_deep_thinking_agent(provider) -> str`
- **Purpose**: Deep-thinking LLM model selection
- **Supported Providers**:
  - **OpenAI**: GPT-4.1-nano through o3, o1 (reasoning models)
  - **Anthropic**: Claude Haiku 3.5 through Claude Opus 4
  - **Google**: Gemini 2.0 Flash-Lite through Gemini 2.5 Pro
  - **OpenRouter**: DeepSeek V3, DeepSeek Chat V3
  - **Ollama**: llama3.1, qwen3 (local models)

##### `select_llm_provider() -> tuple[str, str]`
- **Purpose**: LLM provider and endpoint selection
- **Supported Providers**:
  - OpenAI (https://api.openai.com/v1)
  - Anthropic (https://api.anthropic.com/)
  - Google (https://generativelanguage.googleapis.com/v1)
  - OpenRouter (https://openrouter.ai/api/v1)
  - Ollama (http://localhost:11434/v1)

## Usage Workflow

### 1. Interactive Setup
Users go through a guided setup process:
```bash
python -m cli.main analyze
```

### 2. Configuration Steps
1. **Ticker Selection**: Enter stock symbol (e.g., SPY, AAPL)
2. **Date Selection**: Choose analysis date (YYYY-MM-DD format)
3. **Analyst Team**: Select which analysts to include
4. **Research Depth**: Choose analysis thoroughness
5. **LLM Provider**: Select AI service provider
6. **Model Selection**: Choose specific models for different thinking levels

### 3. Real-Time Analysis
- Live progress tracking of all agents
- Real-time message and tool call monitoring
- Dynamic report updates as analysis progresses
- Color-coded status indicators

### 4. Final Results
- Comprehensive multi-team report
- Markdown-formatted analysis
- Investment recommendations
- Risk assessments

## Features

### Rich Terminal Interface
- **Color-coded panels**: Different colors for different teams
- **Progress tracking**: Real-time agent status updates
- **Live messaging**: Stream of analysis progress
- **Dynamic layouts**: Responsive terminal interface

### Comprehensive Logging
- **Message logging**: All messages saved to files
- **Tool call tracking**: Complete audit trail
- **Report archiving**: Individual report sections saved
- **Structured output**: Organized by ticker and date

### Error Handling
- **Input validation**: Comprehensive user input checking
- **Graceful exits**: Proper cleanup on user cancellation
- **Error recovery**: Robust error handling throughout

### Extensibility
- **Modular design**: Easy to add new analysts or features
- **Configuration-driven**: Behavior controlled by config files
- **Plugin architecture**: Support for additional LLM providers

## Dependencies

### Core Dependencies
- `typer`: Modern CLI framework
- `rich`: Terminal rendering and formatting
- `questionary`: Interactive prompts and forms
- `pydantic`: Data validation and models

### Framework Dependencies
- `tradingagents`: Core trading agents framework
- `pathlib`: Path manipulation
- `datetime`: Date/time handling
- `functools`: Function decoration
- `collections`: Data structures (deque)

## Configuration Integration

The CLI module integrates with the main TradingAgents configuration system:
- Uses `DEFAULT_CONFIG` from `tradingagents.default_config`
- Overrides config based on user selections
- Passes configuration to `TradingAgentsGraph`
- Manages LLM provider configuration

## Output and Results

### Directory Structure
```
results/
├── {ticker}/
│   └── {date}/
│       ├── reports/
│       │   ├── market_report.md
│       │   ├── sentiment_report.md
│       │   ├── news_report.md
│       │   ├── fundamentals_report.md
│       │   ├── investment_plan.md
│       │   ├── trader_investment_plan.md
│       │   └── final_trade_decision.md
│       └── message_tool.log
```

### Report Content
Each report contains:
- **Markdown formatting**: Rich text with tables and sections
- **Analysis details**: Comprehensive findings and insights
- **Recommendations**: Specific trading advice
- **Supporting data**: Charts, tables, and metrics
- **Risk assessments**: Risk factors and mitigation strategies

This CLI module provides a professional, user-friendly interface for complex multi-agent financial analysis, combining ease of use with comprehensive functionality and real-time feedback.
