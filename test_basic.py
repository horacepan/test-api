#!/usr/bin/env python3
"""
Basic test script to verify the Kamino liquidity analysis tool works.
"""

import sys
from kamino_liquidity_analysis import (
    generate_liquidity_report,
    summarize_report,
)

def test_basic_functionality():
    """Test basic functionality with a small subset."""
    print("=" * 80)
    print("Testing Kamino Liquidity Analysis Tool")
    print("=" * 80)
    print()

    # Test with just SOL and smaller swap sizes for faster testing
    print("Running analysis on SOL with limited swap sizes...")
    print("(This may take a minute or two)")
    print()

    try:
        df = generate_liquidity_report(
            asset_filter=['SOL'],  # Just test SOL
            swap_sizes_usd=[1_000_000, 5_000_000],  # Just two sizes
        )

        if df.empty:
            print("ERROR: No data generated")
            return False

        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Total scenarios: {len(df)}")
        print(f"Successful quotes: {df['quote_success'].sum()}")
        print(f"Failed quotes: {(~df['quote_success']).sum()}")

        # Show results
        print("\nDetailed Results:")
        print(df[['asset_symbol', 'swap_size_usd', 'price_impact_pct', 'output_usd', 'router', 'quote_success']])

        # Show summary if we have successful quotes
        successful_df = df[df['quote_success']]
        if len(successful_df) > 0:
            print("\nSummary:")
            print(summarize_report(df))
            print("\n✓ Test PASSED - Tool is working correctly!")
            return True
        else:
            print("\nWARNING: No successful quotes - check API connectivity")
            return False

    except Exception as e:
        print(f"\nERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
