import time
import json
import os
from datetime import datetime
from tradingagents.blackboard.utils import create_agent_blackboard
from .MVO_BLM import size_positions
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage  # Added for static system message
import yfinance as yf
from .metrics_manager import update_metrics_for_date


def create_portfolio_optimizer(llm, memory, toolkit):
    def portfolio_optimizer_node(state) -> dict:

        company_name = state["company_of_interest"]
        
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        sentiment_report = state["sentiment_report"]
        trader_plan = state["trader_investment_plan"]
        risk_decision = state["final_trade_decision"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"
        past_memories = memory.get_memories(curr_situation, n_matches=3)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"
            
        # Blackboard integration
        blackboard_agent = create_agent_blackboard("FA_001", "FundamentalAnalyst")
        # Read recent analysis reports for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=company_name)
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Analysis Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:
                content = analysis.get('content', {})
                blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {content.get('recommendation', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"
                
        tools = [toolkit.get_portfolio_kelly_criterion,
                 toolkit.get_portfolio_risk_parity,
                 toolkit.get_portfolio_black_litterman,
                 toolkit.get_portfolio_mean_reversion,
                 toolkit.get_portfolio_momentum,
                 toolkit.calculate_beta,
                ]

        quant_strategies = state.get("quant_strategies")

        prompt = f"""As the Senior Quantitative Portfolio Manager, create a comprehensive institutional-grade portfolio optimization strategy for {company_name}. Your analysis should exclude options-based strategies and focus on equity sizing via MVO/Black-Litterman, beta management, and non-options hedging where relevant.

**CRITICAL REQUIREMENTS:**
1. **Multi-Asset Hedging Strategy**: Design hedging using crypto (BTC, ETH), options (puts/calls), futures (ES, NQ), forex (USD pairs), and commodities (gold, oil, etc.)
2. **Advanced Quantitative Techniques**: Implement Kelly Criterion, Risk Parity, Black-Litterman, Mean Reversion, Momentum strategies
3. **Beta Management**: Calculate and hedge portfolio beta using index futures and ETFs
4. **Cross-Asset Correlation Analysis**: Analyze correlations between {company_name} and various asset classes
5. **Scenario Analysis**: Stress test portfolio against market crashes, inflation, currency devaluation

**Input Context:**
- **Trader's Investment Plan**: {trader_plan}
- **Risk Committee Decision**: {risk_decision}
- **Market Intelligence**: {market_research_report}
- **Sentiment Analysis**: {sentiment_report}
- **News Report**: {news_report}
- **Fundamentals Report**: {fundamentals_report}
- **Past Portfolio Lessons**: {past_memory_str}
- **Blackboard Context**: {blackboard_context}

**DELIVERABLE STRUCTURE:**
Create a detailed markdown report covering:

## Executive Summary
- Portfolio optimization recommendation for {company_name}
- Key hedging strategies across asset classes
- Expected risk/return profile

## Position Sizing & Allocation
- Primary position in {company_name} (size, rationale)
- Kelly Criterion application
- Risk parity considerations
- Volatility targeting methodology

## Multi-Asset Hedging Strategy

### Cryptocurrency Hedging
- Bitcoin (BTC) hedge ratios and correlation analysis
- Ethereum (ETH) as inflation/tech hedge
- Crypto derivatives and futures for tail risk protection

### Options Strategy
- Put protection levels and strike selection
- Call overwriting opportunities
- Volatility trading strategies
- Greeks management (delta, gamma, theta, vega)

### Futures Hedging
- Index futures (ES, NQ, RTY) for beta management
- Sector-specific futures exposure
- Currency futures for FX risk
- Commodity futures positioning

### Forex Hedging
- USD exposure management
- Cross-currency hedging strategies
- Emerging market currency risks
- Carry trade considerations

### Commodities Exposure
- Gold as portfolio insurance
- Oil and energy complex hedging
- Agricultural commodities for inflation protection
- Precious metals allocation

## Beta Management
- Current portfolio beta calculation
- Target beta based on market conditions
- Hedging instruments to achieve beta neutrality
- Dynamic beta adjustment strategies

## Risk Metrics & Analytics
- Value at Risk (VaR) calculations
- Expected Shortfall (CVaR)
- Maximum Drawdown estimates
- Sharpe ratio optimization
- Correlation matrix analysis

## Scenario Analysis
- Market crash scenarios (-20%, -40%)
- Inflation spike scenarios
- Currency crisis scenarios
- Sector rotation impacts
- Crypto market correlation breaks

## Implementation Roadmap
- Phase 1: Core position establishment
- Phase 2: Hedging implementation
- Phase 3: Dynamic rebalancing
- Execution timeline and cost analysis

## Monitoring & Rebalancing
- Daily risk monitoring protocols
- Rebalancing triggers and thresholds
- Performance attribution analysis
- Hedge effectiveness measurement

Provide specific trade recommendations, position sizes, and quantitative analysis. Make this institutional-quality with hedge fund level sophistication."""

        # Build a ChatPromptTemplate using a static SystemMessage to avoid template parsing of curly braces in dynamic content
        chat_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=prompt),  # static, no templating
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # Bind tools to the prompt/llm pipeline
        chain = chat_prompt | llm.bind_tools(tools)

        # Normalize incoming messages robustly
        raw_messages = state.get("messages", []) or []
        normalized_messages = []
        for m in raw_messages:
            if isinstance(m, dict):
                role = (m.get("role") or m.get("type") or "user").lower()
                content = m.get("content") or m.get("text") or ""
            else:
                role = (getattr(m, "role", None) or getattr(m, "type", None) or "user").lower()
                content = getattr(m, "content", None)
                if callable(content):
                    try:
                        content = content()
                    except Exception:
                        content = ""
                content = content or getattr(m, "text", None) or ""
            # Map generic roles to LangChain expected types
            if role == "user":
                role = "human"
            elif role in ("assistant", "ai", "model"):
                role = "ai"
            elif role not in ("system", "human", "ai"):
                role = "human"
            # Ensure content is a string
            if not isinstance(content, (str, list)):
                content = str(content)
            if isinstance(content, list):
                # Flatten list parts to string if list of dicts/str
                try:
                    parts = []
                    for p in content:
                        if isinstance(p, str):
                            parts.append(p)
                        else:
                            parts.append(json.dumps(p, ensure_ascii=False))
                    content = "\n".join(parts)
                except Exception:
                    content = str(content)
            normalized_messages.append({"role": role, "content": content})

        # Invoke the chain with normalized messages only
        result = chain.invoke({"messages": normalized_messages})

        # Safely extract the analysis text from the result
        if isinstance(result, dict):
            portfolio_analysis = result.get("content") or result.get("text") or ""
        else:
            extracted = getattr(result, "content", None)
            if callable(extracted):  # guard against bound method
                try:
                    extracted = extracted()
                except Exception:
                    extracted = None
            portfolio_analysis = extracted or getattr(result, "text", None) or str(result) or ""
        # Ensure portfolio_analysis is a string for downstream operations
        if not isinstance(portfolio_analysis, str):
            try:
                portfolio_analysis = json.dumps(portfolio_analysis, ensure_ascii=False)
            except Exception:
                portfolio_analysis = str(portfolio_analysis)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"portfolio_optimization_{company_name}_{timestamp}.md"
        
        # Create the markdown report content
        report_content = f"""# Portfolio Optimization Report: {company_name}
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Analyst**: Senior Quantitative Portfolio Manager
**Target Asset**: {company_name}

---

{portfolio_analysis}

---

## Disclaimer
This report is generated by AI-powered quantitative analysis and should be reviewed by qualified financial professionals before implementation. Past performance does not guarantee future results. All investments carry risk of loss.

## Report Metadata
- **Generation Time**: {datetime.now().isoformat()}
- **Asset Analyzed**: {company_name}
- **Portfolio Optimizer Version**: 1.0
- **Multi-Asset Coverage**: Crypto, Options, Futures, Forex, Commodities
"""

        # Enterprise-grade results directory: results_dir/<ticker>/<date>/reports
        try:
            results_root = toolkit.config.get("results_dir", "./results")
            trade_date = state.get("trade_date", datetime.now().strftime("%Y-%m-%d"))
            reports_dir = os.path.join(results_root, company_name, trade_date, "reports")
            os.makedirs(reports_dir, exist_ok=True)
            full_path = os.path.join(reports_dir, filename)
        except Exception:
            reports_dir = os.getcwd()
            full_path = os.path.join(reports_dir, filename)

        # Write the report to file
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ Portfolio optimization report saved: {full_path}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")

        # Execute trades here using daily MVO-BLM sizing
        execution_summary = {
            "executed": False,
            "action": None,
            "quantity": 0,
            "message": "",
            "target_weight": None,
        }
        action = None
        quantity = 0
        portfolio_value = 0.0
        liquid = 0.0

        try:
            # Skip trade execution during multithreaded testing; only report.
            if os.getenv("TA_TESTING_MULTI") == "1":
                execution_summary.update({
                    "executed": False,
                    "action": None,
                    "quantity": 0,
                    "message": "Skipped execution in multithreaded testing.",
                })
                portfolio_value = 0.0
                liquid = 0.0
            else:
                trade_date = state.get("trade_date", datetime.now().strftime("%Y-%m-%d"))
                decisions = {company_name: (state.get("final_trade_decision") or "HOLD")}
                portfolio_path = os.path.join(os.path.dirname(__file__), "../../../config/portfolio.json")
                data = {}
                try:
                    if os.path.exists(portfolio_path):
                        with open(portfolio_path, "r") as pf:
                            data = json.load(pf) or {}
                except Exception:
                    data = {"liquid": 1000000}
                portfolio_holdings = data.get("portfolio", {}) if isinstance(data.get("portfolio"), dict) else {}
                liquid = float(data.get("liquid", 0) or 0)
                def get_price_safe(tkr: str) -> float:
                    try:
                        st = yf.Ticker(tkr)
                        hist = st.history(period="1d")
                        return float(hist["Close"].iloc[-1]) if not hist.empty else 0.0
                    except Exception:
                        return 0.0
                tickers = list(portfolio_holdings.keys())
                prices = {t: get_price_safe(t) for t in set(tickers + [company_name])}
                existing = portfolio_holdings.get(company_name, {})
                current_shares = int(existing.get("totalAmount", 0) or 0)
                price = prices.get(company_name, 0.0)
                portfolio_value_positions = sum(
                    (float(info.get("totalAmount", 0) or 0) * prices.get(t, 0.0))
                    for t, info in portfolio_holdings.items()
                )
                portfolio_value = liquid + portfolio_value_positions
                trades = size_positions([company_name], trade_date, decisions, portfolio_path, prices)
                tr = trades.get(company_name)
                action = None
                quantity = 0
                if tr:
                    delta = int(tr.get("delta_shares", 0))
                    if delta > 0:
                        msg = toolkit.buy(company_name, trade_date, delta)
                        action, quantity = "BUY", delta
                    elif delta < 0:
                        msg = toolkit.sell(company_name, trade_date, abs(delta))
                        action, quantity = "SELL", abs(delta)
                    else:
                        msg = toolkit.hold_impl(company_name, trade_date, note="MVO-BLM no change")
                        action, quantity = "HOLD", 0
                    execution_summary.update({"message": msg})
                execution_summary.update({
                    "executed": True if action else False,
                    "action": action,
                    "quantity": quantity,
                })
        except Exception as e:
            execution_summary = {
                "executed": False,
                "action": None,
                "quantity": 0,
                "message": f"Execution skipped due to error: {str(e)}",
                "target_weight": execution_summary.get("target_weight"),
            }

        # Store analysis in memory for future reference
        memory_entry = f"Portfolio Optimization for {company_name}: {portfolio_analysis[:500]}..."
        try:
            # Use the correct method to save to memory
            memory.add_situations([(curr_situation, memory_entry)])
        except Exception as e:
            print(f"⚠️ Memory save warning: {e}")

        # Final execution summary
        print(f"\n🎯 PORTFOLIO OPTIMIZATION COMPLETED FOR {company_name}")
        print(f"📊 Action: {action}")
        print(f"📈 Quantity: {quantity}")
        print(f"💰 Portfolio Value: ${portfolio_value:,.2f}")
        print(f"💵 Liquid Cash: ${liquid:,.2f}")
        print(f"📋 Execution Summary: {execution_summary}")
        print("=" * 60)

        # After execution (or skip in test), update metrics for the trade date
        try:
            update_metrics_for_date(state.get("trade_date", datetime.now().strftime("%Y-%m-%d")))
        except Exception as _:
            pass

        return {
            "portfolio_optimization_state": {
                "analysis": portfolio_analysis,
                "company": company_name,
                "optimization_completed": True,
                "report_file": full_path,
                "timestamp": timestamp,
                "multi_asset_hedging": True,
                "asset_classes_covered": ["crypto", "options", "futures", "forex", "commodities"],
                "execution": execution_summary,
            }
        }

    return portfolio_optimizer_node