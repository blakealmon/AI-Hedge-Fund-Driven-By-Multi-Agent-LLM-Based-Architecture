# Agent System Documentation

## Overview

The TradingAgents agent system implements a sophisticated multi-agent architecture for financial analysis and trading decision-making. The system is organized into specialized teams of AI agents, each with specific expertise and responsibilities in the trading analysis pipeline.

## Agent Architecture

### Core Principles

1. **Specialization**: Each agent focuses on a specific domain of expertise
2. **Collaboration**: Agents work together through structured interactions
3. **Debate-Driven**: Decision-making through structured argumentation
4. **Memory-Enhanced**: Learning from past decisions and outcomes
5. **Tool-Enabled**: Access to comprehensive data and analysis tools

### Agent Hierarchy

```
TradingAgents Framework
├── Analyst Team
│   ├── Market Analyst (Technical Analysis)
│   ├── Social Media Analyst (Sentiment Analysis)
│   ├── News Analyst (News Sentiment)
│   └── Fundamentals Analyst (Financial Metrics)
├── Research Team
│   ├── Bull Researcher (Bullish Arguments)
│   ├── Bear Researcher (Bearish Arguments)
│   └── Research Manager (Decision Making)
├── Trading Team
│   └── Trader (Execution Planning)
├── Risk Management Team
│   ├── Aggressive Debator (High-Risk Strategies)
│   ├── Conservative Debator (Low-Risk Strategies)
│   ├── Neutral Debator (Balanced Approach)
│   └── Portfolio Manager (Final Decision)
```

## Analyst Team

### Market Analyst (`analysts/market_analyst.py`)

**Primary Role**: Technical analysis specialist focused on price action and market indicators.

#### Core Responsibilities
- **Technical Indicator Analysis**: Selects and analyzes optimal technical indicators
- **Trend Identification**: Identifies short, medium, and long-term trends
- **Pattern Recognition**: Detects chart patterns and technical setups
- **Volatility Analysis**: Assesses market volatility and risk levels

#### Technical Indicator Selection Strategy

**Moving Averages**:
- `close_50_sma`: Medium-term trend analysis
- `close_200_sma`: Long-term trend confirmation, golden/death cross detection
- `close_10_ema`: Short-term momentum and entry point identification

**MACD Analysis**:
- `macd`: Primary momentum indicator for trend changes
- `macds`: Signal line for crossover confirmation
- `macdh`: Histogram for momentum strength visualization

**Momentum Indicators**:
- `rsi`: Overbought/oversold conditions with 70/30 thresholds

**Volatility Indicators**:
- `boll`, `boll_ub`, `boll_lb`: Bollinger Bands for volatility and breakout analysis
- `atr`: Average True Range for stop-loss and position sizing

**Volume Indicators**:
- `vwma`: Volume-weighted moving average for trend confirmation

#### Analysis Workflow
1. **Data Retrieval**: Calls `get_YFin_data` for historical price data
2. **Indicator Selection**: Chooses up to 8 complementary indicators
3. **Calculation**: Uses `get_stockstats_indicators_report` for technical calculations
4. **Pattern Analysis**: Identifies trends, support/resistance levels
5. **Report Generation**: Creates detailed markdown reports with data tables

#### Output Format
- **Trend Analysis**: Detailed trend identification across timeframes
- **Signal Analysis**: Buy/sell signals from technical indicators
- **Support/Resistance**: Key price levels identification
- **Volatility Assessment**: Current market volatility analysis
- **Summary Table**: Organized markdown table with key findings

### Social Media Analyst (`analysts/social_media_analyst.py`)

**Primary Role**: Social sentiment analysis from retail investor discussions.

#### Core Responsibilities
- **Sentiment Analysis**: Analyze sentiment from social media platforms
- **Volume Tracking**: Monitor discussion volume and engagement
- **Trend Detection**: Identify emerging social sentiment trends
- **Community Analysis**: Assess different community perspectives

#### Data Sources
- **Reddit**: r/stocks, r/investing, r/SecurityAnalysis, r/wallstreetbets
- **Twitter**: Financial Twitter discussions and hashtags
- **Discord**: Trading community discussions
- **Financial Forums**: Specialized investment forums

#### Analysis Methods
- **Natural Language Processing**: Sentiment scoring algorithms
- **Engagement Metrics**: Upvotes, comments, shares analysis
- **Trend Analysis**: Sentiment momentum and direction
- **Volume Correlation**: Social volume vs price movement correlation

### News Analyst (`analysts/news_analyst.py`)

**Primary Role**: Financial news analysis and event impact assessment.

#### Core Responsibilities
- **News Sentiment**: Analyze sentiment of financial news articles
- **Event Detection**: Identify significant corporate and economic events
- **Impact Assessment**: Evaluate potential market impact of news
- **Source Credibility**: Weight news based on source reliability

#### Data Processing
- **Article Collection**: Gather relevant news from multiple sources
- **Content Analysis**: Extract key information and sentiment
- **Event Categorization**: Classify news by type and potential impact
- **Timeline Analysis**: Track news flow and sentiment changes

### Fundamentals Analyst (`analysts/fundamentals_analyst.py`)

**Primary Role**: Fundamental analysis of financial metrics and company health.

#### Core Responsibilities
- **Financial Ratio Analysis**: P/E, P/B, ROE, debt ratios
- **Growth Analysis**: Revenue, earnings, cash flow growth
- **Valuation Models**: DCF, comparable company analysis
- **Financial Health**: Balance sheet strength, liquidity analysis

#### Key Metrics
- **Profitability Ratios**: ROE, ROA, profit margins
- **Valuation Ratios**: P/E, P/B, EV/EBITDA
- **Growth Metrics**: Revenue CAGR, earnings growth
- **Financial Strength**: Debt-to-equity, current ratio, interest coverage

## Research Team

### Bull Researcher (`researchers/bull_researcher.py`)

**Primary Role**: Develop comprehensive bullish investment arguments.

#### Core Responsibilities
- **Positive Case Development**: Build strongest possible bullish arguments
- **Opportunity Identification**: Highlight growth opportunities and catalysts
- **Risk Mitigation**: Address bearish concerns with counter-arguments
- **Evidence Compilation**: Gather supporting data and analysis

#### Argumentation Strategy
- **Catalyst Focus**: Identify potential positive catalysts
- **Growth Story**: Articulate compelling growth narrative
- **Competitive Advantages**: Highlight competitive moats and strengths
- **Market Opportunity**: Assess total addressable market and expansion

### Bear Researcher (`researchers/bear_researcher.py`)

**Primary Role**: Develop comprehensive bearish investment arguments.

#### Core Responsibilities
- **Risk Identification**: Identify potential downside risks and threats
- **Weakness Analysis**: Highlight company and market weaknesses
- **Scenario Planning**: Develop bearish scenarios and outcomes
- **Counter-Argument**: Challenge bullish assumptions

#### Argumentation Strategy
- **Risk Assessment**: Comprehensive risk factor analysis
- **Competitive Threats**: Identify competitive disadvantages
- **Market Challenges**: Assess market headwinds and obstacles
- **Valuation Concerns**: Challenge optimistic valuation assumptions

### Research Manager (`managers/research_manager.py`)

**Primary Role**: Facilitate research debate and make investment decisions.

#### Core Responsibilities
- **Debate Facilitation**: Manage bull vs bear research discussions
- **Argument Evaluation**: Assess strength of bullish and bearish cases
- **Decision Making**: Make final investment recommendations
- **Strategy Development**: Create detailed investment plans

#### Decision Process

```python
def research_manager_node(state) -> dict:
    # Gather all analyst reports
    market_report = state["market_report"]
    sentiment_report = state["sentiment_report"] 
    news_report = state["news_report"]
    fundamentals_report = state["fundamentals_report"]
    
    # Review debate history
    debate_history = state["investment_debate_state"]["history"]
    
    # Incorporate past experiences
    past_memories = memory.get_memories(current_situation, n_matches=2)
    
    # Make decision and create investment plan
```

#### Output Components
- **Investment Recommendation**: Clear Buy/Sell/Hold decision
- **Rationale**: Detailed reasoning for decision
- **Strategic Actions**: Specific implementation steps
- **Risk Considerations**: Identified risks and mitigation strategies
- **Learning Integration**: How past experiences influenced decision

#### Memory Integration
- **Similar Situations**: Retrieve relevant past scenarios
- **Mistake Learning**: Incorporate lessons from past errors
- **Pattern Recognition**: Identify recurring patterns and outcomes
- **Decision Improvement**: Continuously refine decision-making process

## Trading Team

### Trader (`trader/trader.py`)

**Primary Role**: Develop specific trading execution strategies.

#### Core Responsibilities
- **Execution Planning**: Develop detailed trade execution plans
- **Order Strategy**: Determine optimal order types and timing
- **Position Sizing**: Calculate appropriate position sizes
- **Risk Management**: Implement stop-losses and profit targets

#### Execution Considerations
- **Market Liquidity**: Assess liquidity for execution
- **Market Impact**: Minimize market impact of trades
- **Timing Optimization**: Identify optimal execution windows
- **Cost Management**: Minimize transaction costs

#### Output Format
- **Trade Plan**: Detailed execution strategy
- **Order Specifications**: Specific order types and parameters
- **Risk Parameters**: Stop-loss and profit target levels
- **Timing Strategy**: Optimal execution timing

## Risk Management Team

### Risk Debator System

The risk management team uses a structured debate system with three perspectives:

#### Aggressive Debator (`risk_mgmt/aggressive_debator.py`)
- **Philosophy**: Advocates for higher-risk, higher-reward strategies
- **Focus**: Maximizing potential returns
- **Arguments**: Growth opportunities, momentum strategies
- **Risk Tolerance**: High risk tolerance for high returns

#### Conservative Debator (`risk_mgmt/conservative_debator.py`)
- **Philosophy**: Emphasizes capital preservation and risk minimization
- **Focus**: Protecting downside risk
- **Arguments**: Value strategies, defensive positioning
- **Risk Tolerance**: Low risk tolerance, safety-first approach

#### Neutral Debator (`risk_mgmt/neutral_debator.py`)
- **Philosophy**: Balanced approach between risk and reward
- **Focus**: Risk-adjusted returns optimization
- **Arguments**: Moderate risk strategies, diversification
- **Risk Tolerance**: Balanced risk-reward optimization

### Portfolio Manager

**Primary Role**: Make final risk-adjusted investment decisions.

#### Integration Process
- **Risk Perspective Synthesis**: Combine insights from all risk debators
- **Portfolio Context**: Consider overall portfolio implications
- **Risk Budget**: Ensure position fits within risk budget
- **Final Decision**: Make ultimate investment decision

## Agent Utilities

### State Management (`utils/agent_states.py`)

#### Core State Classes

##### `AgentState`
- **Purpose**: Base state for all agent interactions
- **Components**: Messages, tool calls, current analysis state

##### `InvestDebateState`  
- **Purpose**: Manages bull vs bear research debates
- **Components**: 
  - `bull_history`: Bull researcher arguments
  - `bear_history`: Bear researcher arguments
  - `judge_decision`: Research manager decision
  - `count`: Debate round counter

##### `RiskDebateState`
- **Purpose**: Manages risk management debates
- **Components**:
  - `risky_history`: Aggressive debator arguments
  - `safe_history`: Conservative debator arguments
  - `neutral_history`: Neutral debator arguments
  - `judge_decision`: Portfolio manager decision

### Memory System (`utils/memory.py`)

#### `FinancialSituationMemory`

**Purpose**: Implement learning and memory for financial decision-making.

**Key Features**:
- **Similarity Matching**: Find similar past market situations
- **Learning Integration**: Incorporate lessons from past decisions
- **Context Retrieval**: Provide relevant historical context
- **Performance Tracking**: Track decision outcomes over time

**Memory Components**:
- **Situation Encoding**: Convert market conditions to searchable format
- **Decision Storage**: Store decisions and outcomes
- **Retrieval System**: Efficient similarity-based retrieval
- **Learning Metrics**: Track learning progress and improvement

### Agent Utilities (`utils/agent_utils.py`)

**Purpose**: Common utilities shared across all agents.

**Key Functions**:
- **Data Processing**: Common data manipulation functions
- **Formatting**: Standardized output formatting
- **Validation**: Input and output validation
- **Communication**: Inter-agent communication protocols

## Tool Integration

### Tool System Architecture

Each agent has access to a comprehensive toolkit for data analysis:

```python
# Market Analyst Tools
tools = [
    toolkit.get_YFin_data_online,
    toolkit.get_stockstats_indicators_report_online,
]

# Social Analyst Tools  
tools = [
    toolkit.get_reddit_sentiment_analysis,
    toolkit.get_social_media_sentiment,
]

# News Analyst Tools
tools = [
    toolkit.get_finnhub_news,
    toolkit.get_googlenews_data,
]
```

### Tool Categories

1. **Market Data Tools**: Yahoo Finance, Alpha Vantage
2. **Technical Analysis Tools**: StockStats, TA-Lib
3. **News Tools**: Finnhub, Google News, Bloomberg
4. **Social Media Tools**: Reddit, Twitter, Discord
5. **Fundamental Tools**: SEC EDGAR, Financial statements

## Communication Protocols

### Inter-Agent Communication

#### Message Passing
- **Structured Messages**: Standardized message formats
- **State Updates**: Coordinated state management
- **Tool Results**: Shared tool output and analysis

#### Debate Protocols
- **Round Management**: Structured debate rounds
- **Argument Formatting**: Standardized argument structure
- **Evidence Requirements**: Supporting evidence for claims
- **Decision Criteria**: Clear decision-making criteria

### Graph Integration

#### Node Definition
Each agent is implemented as a graph node with:
- **Input Processing**: Handle incoming state and data
- **Analysis Logic**: Core agent analysis functionality
- **Output Generation**: Structured output for next agents
- **State Updates**: Update global analysis state

#### Edge Conditions
- **Conditional Logic**: Determine next agent based on state
- **Parallel Processing**: Multiple agents processing simultaneously
- **Sequential Dependencies**: Required order for some agent interactions

## Learning and Adaptation

### Memory-Based Learning

#### Experience Storage
- **Situation Encoding**: Convert market scenarios to vectors
- **Decision Recording**: Store decisions and reasoning
- **Outcome Tracking**: Track actual outcomes vs predictions
- **Feedback Integration**: Incorporate outcome feedback

#### Similarity Matching
- **Semantic Similarity**: Content-based situation matching
- **Temporal Similarity**: Time-based pattern matching
- **Outcome Similarity**: Decision outcome pattern matching
- **Context Similarity**: Market context pattern matching

### Continuous Improvement

#### Performance Metrics
- **Accuracy Tracking**: Track prediction accuracy over time
- **Return Attribution**: Attribute returns to specific decisions
- **Risk Assessment**: Evaluate risk prediction accuracy
- **Learning Rate**: Measure improvement over time

#### Adaptation Mechanisms
- **Weight Adjustment**: Adjust decision weights based on performance
- **Strategy Evolution**: Evolve strategies based on outcomes
- **Bias Correction**: Identify and correct systematic biases
- **Confidence Calibration**: Improve confidence estimates

This comprehensive agent system provides a robust framework for collaborative financial analysis, combining specialized expertise with structured decision-making processes and continuous learning capabilities.
