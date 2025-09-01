from typing import Dict, Any
import os
import sys


def create_test_runner(toolkit):
    def test_runner_node(state) -> Dict[str, Any]:
        """
        Optional testing harness node.

        - Runs portfolio execution smoke tests when enabled.
        - Runs date-range evaluation via testingLoop when enabled.
        - Returns a compact summary of which tests ran and any errors.
        """

        config = getattr(toolkit, "config", {})
        results: Dict[str, Any] = {"ran": [], "errors": {}}

        # Ensure project root is on sys.path for imports of top-level test scripts
        try:
            project_dir = config.get("project_dir") or os.getcwd()
            project_root = os.path.abspath(os.path.join(project_dir, os.pardir))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
        except Exception:
            pass

        # 1) Portfolio execution tests (buy/sell/hold implementations)
        if config.get("run_portfolio_exec_tests", False):
            try:
                from test_execution import test_portfolio_execution

                test_portfolio_execution()
                results["ran"].append("portfolio_exec_tests")
            except Exception as e:
                results["errors"]["portfolio_exec_tests"] = str(e)

        # 2) testingLoop range run (per-day propagation over a range)
        if config.get("run_testing_loop", False):
            try:
                from testingLoop import run_range

                ticker = state.get("company_of_interest")
                # Use state trade_date if specific dates are not provided
                start_date = config.get("testing_start_date", state.get("trade_date"))
                end_date = config.get("testing_end_date", state.get("trade_date"))
                outdir = config.get("testing_outdir", "evalRes")
                debug = bool(config.get("debug", False))

                if ticker and start_date and end_date:
                    run_range(
                        ticker=ticker,
                        start_date=str(start_date),
                        end_date=str(end_date),
                        outdir=str(outdir),
                        debug=debug,
                        deep_copy_config=True,
                        fail_fast=False,
                        show_trace=False,
                    )
                    results["ran"].append(
                        f"testing_loop:{ticker}:{start_date}->{end_date}"
                    )
                else:
                    results["errors"]["testing_loop"] = (
                        "Missing ticker or date(s) for testing loop"
                    )
            except Exception as e:
                results["errors"]["testing_loop"] = str(e)

        return {"testing_results": results}

    return test_runner_node


