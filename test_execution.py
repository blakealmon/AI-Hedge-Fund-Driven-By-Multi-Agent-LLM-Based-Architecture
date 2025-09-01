#!/usr/bin/env python3
"""
Test script to verify portfolio execution functions are working correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'tradingagents'))

def test_portfolio_execution():
    """Test the portfolio execution functions."""
    try:
        from tradingagents.agents.utils.agent_utils import Toolkit
        
        print("🧪 Testing Portfolio Execution Functions...")
        print("=" * 50)
        
        # Test buy function - call the implementation directly
        print("\n1. Testing BUY function...")
        result = Toolkit.buy_impl("AAPL", "2025-01-20", 10)
        print(f"Result: {result}")
        
        # Test portfolio reading
        print("\n2. Testing portfolio reading...")
        portfolio_path = os.path.join(os.path.dirname(__file__), "config/portfolio.json")
        if os.path.exists(portfolio_path):
            import json
            with open(portfolio_path, 'r') as f:
                portfolio = json.load(f)
            print(f"Portfolio: {json.dumps(portfolio, indent=2)}")
        else:
            print("❌ Portfolio file not found!")
            
        # Test sell function - call the implementation directly
        print("\n3. Testing SELL function...")
        result = Toolkit.sell_impl("AAPL", "2025-01-20", 5)
        print(f"Result: {result}")
        
        # Test hold function - call the implementation directly
        print("\n4. Testing HOLD function...")
        result = Toolkit.hold_impl("AAPL", "2025-01-20", "Testing hold function")
        print(f"Result: {result}")
        
        # Final portfolio state
        print("\n5. Final portfolio state...")
        if os.path.exists(portfolio_path):
            with open(portfolio_path, 'r') as f:
                portfolio = json.load(f)
            print(f"Final Portfolio: {json.dumps(portfolio, indent=2)}")
        
        print("\n✅ Portfolio execution test completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed and the path is correct.")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_portfolio_execution()
