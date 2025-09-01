import os
from datetime import datetime
from typing import Dict, Any
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.blackboard.utils import create_agent_blackboard


def create_quant_options_manager(llm, memory, toolkit):
    def quant_options_manager_node(state: AgentState) -> Dict[str, Any]:
        """
        Enterprise-grade quantitative options strategy manager.

        - Scans for quantitative opportunities across options, momentum, mean reversion, and risk parity.
        - If a high-confidence quantitative strategy is found, forwards a structured directive
          (quant_strategies) to the portfolio optimizer node via state.
        - Logs artifacts under results_dir/<ticker>/<date>/reports.
        """

        ticker = state["company_of_interest"]
        trade_date = state.get("trade_date", datetime.now().strftime("%Y-%m-%d"))

        # Blackboard integration
        blackboard_agent = create_agent_blackboard("QOM_001", "QuantOptionsManager")
        
        # Read recent analyst reports and investment decisions for context
        recent_analyses = blackboard_agent.get_analysis_reports(ticker=ticker)
        recent_decisions = blackboard_agent.get_investment_decisions(ticker=ticker)
        
        blackboard_context = ""
        if recent_analyses:
            blackboard_context += "\n\nRecent Analyst Reports on Blackboard:\n"
            for analysis in recent_analyses[-3:]:  # Last 3 analyses
                content = analysis.get('content', {})
                analysis_data = content.get('analysis', {})
                if isinstance(analysis_data, dict):
                    blackboard_context += f"- {analysis['sender'].get('role', 'Unknown')}: {analysis_data.get('recommendation', 'N/A')} (Confidence: {analysis_data.get('confidence', 'N/A')})\n"
        
        if recent_decisions:
            blackboard_context += "\n\nRecent Investment Decisions on Blackboard:\n"
            for decision in recent_decisions[-2:]:  # Last 2 decisions
                content = decision.get('content', {})
                blackboard_context += f"- Decision: {content.get('decision', 'N/A')} (Confidence: {content.get('confidence', 'N/A')})\n"

        # Prepare enterprise results directory
        results_root = toolkit.config.get("results_dir", "./results")
        reports_dir = os.path.join(results_root, ticker, trade_date, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        # Use Toolkit quantitative tools for signals (exclude Kelly entirely)
        momentum = toolkit.get_portfolio_momentum.invoke({})
        mean_rev = toolkit.get_portfolio_mean_reversion.invoke({})
        risk_parity = toolkit.get_portfolio_risk_parity.invoke({})

        # Score and select strategies
        quant_findings: Dict[str, Any] = {
            "momentum": momentum,
            "mean_reversion": mean_rev,
            "risk_parity": risk_parity,
        }

        # Simple enterprise selection heuristic
        selected_strategies = {}
        try:
            # Prefer momentum BUY opportunities
            buy_momentum = {
                t: d for t, d in (momentum.get("signals") or {}).items() if d.get("signal") == "BUY"
            }
            if buy_momentum:
                selected_strategies["momentum"] = {
                    "action": "OVERWEIGHT",
                    "targets": buy_momentum,
                    "rationale": "Positive momentum with non-overbought RSI",
                }
        except Exception:
            pass

        try:
            # Mean reversion BUY opportunities
            buy_mean = {
                t: d for t, d in (mean_rev.get("signals") or {}).items() if d.get("signal") == "BUY"
            }
            if buy_mean:
                selected_strategies["mean_reversion"] = {
                    "action": "ACCUMULATE",
                    "targets": buy_mean,
                    "rationale": "Undervalued vs rolling mean; expect reversion",
                }
        except Exception:
            pass

        # Explicitly exclude Kelly sizing logic per requirements

        # Risk parity baseline weights
        if isinstance(risk_parity, dict) and risk_parity.get("weights"):
            selected_strategies["risk_parity"] = {
                "action": "BASELINE_WEIGHTS",
                "weights": risk_parity.get("weights"),
                "rationale": "Inverse volatility weighting to equalize risk contributions",
            }

        # Persist a concise JSON artifact for audit
        try:
            artifact_path = os.path.join(
                reports_dir, f"quant_findings_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            import json

            with open(artifact_path, "w", encoding="utf-8") as f:
                json.dump({"inputs": {"ticker": ticker, "date": trade_date}, "findings": quant_findings, "selected": selected_strategies}, f, indent=2)
        except Exception:
            pass

        # Write a human-readable Markdown report with findings
        md_path = None
        try:
            md_path = os.path.join(reports_dir, "quantoptionsstrat.md")
            lines = []
            lines.append(f"# Quant Options Strategy Report: {ticker} ({trade_date})\n")
            lines.append("## Executive Summary\n")
            if selected_strategies:
                lines.append("High-confidence quantitative opportunities detected and forwarded to portfolio optimization.\n")
            else:
                lines.append("No high-confidence quantitative strategies identified. Baseline risk frameworks retained.\n")
            lines.append("\n## Selected Strategies\n")
            if selected_strategies:
                for name, payload in selected_strategies.items():
                    lines.append(f"### {name.replace('_', ' ').title()}\n")
                    if isinstance(payload, dict):
                        for k, v in payload.items():
                            if k in ("targets", "weights") and isinstance(v, dict):
                                lines.append(f"- **{k}**:\n")
                                for kt, kv in v.items():
                                    lines.append(f"  - {kt}: {kv}")
                            else:
                                lines.append(f"- **{k}**: {v}")
                    else:
                        lines.append(f"- {payload}")
                    lines.append("")
            else:
                lines.append("- None\n")
            lines.append("\n## Raw Findings (for audit)\n")
            lines.append("```json")
            import json as _json
            lines.append(_json.dumps({
                "inputs": {"ticker": ticker, "date": trade_date},
                "findings": quant_findings,
                "selected": selected_strategies,
            }, indent=2))
            lines.append("```\n")
            with open(md_path, "w", encoding="utf-8") as f_md:
                f_md.write("\n".join(lines))
        except Exception:
            md_path = None

        # Blackboard logging for enterprise visibility
        try:
            blackboard_agent.post_investment_decision(
                ticker=ticker,
                decision="Quant Strategy Scan",
                reasoning=str(selected_strategies),
                confidence="N/A",
            )
        except Exception:
            pass

        # Save to memory snapshot
        try:
            memory.add_situations([
                (
                    f"Quant scan for {ticker} on {trade_date}",
                    f"Selected strategies: {str(selected_strategies)[:500]}...",
                )
            ])
        except Exception:
            pass

        # Return state enrichment for downstream portfolio optimizer
        return {
            "quant_strategies": selected_strategies,
            "quant_options_report_file": md_path,
        }

    return quant_options_manager_node