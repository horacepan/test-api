#!/usr/bin/env python3
"""
Command-line interface for Kamino liquidity analysis tool.
"""

import argparse
import sys
import logging
from typing import Optional, List

from analyzer import generate_liquidity_report, export_report, summarize_report
from constants import MAIN_MARKET_PUBKEY, SWAP_SIZE_BANDS_USD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_swap_sizes(swap_sizes_str: str) -> List[float]:
    """
    Parse comma-separated swap sizes.

    Args:
        swap_sizes_str: Comma-separated string of swap sizes

    Returns:
        List of float swap sizes
    """
    try:
        sizes = [float(s.strip()) for s in swap_sizes_str.split(",")]
        return sizes
    except ValueError as e:
        raise ValueError(f"Invalid swap sizes format: {e}")


def parse_assets(assets_str: str) -> List[str]:
    """
    Parse comma-separated asset symbols.

    Args:
        assets_str: Comma-separated string of asset symbols

    Returns:
        List of uppercase asset symbols
    """
    return [s.strip().upper() for s in assets_str.split(",")]


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Kamino Liquidity Analysis Tool - Assess liquidation risk via swap price impact",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage - analyze all volatile assets
  python main.py

  # Save output to CSV
  python main.py --output liquidity_analysis.csv

  # Analyze specific assets only
  python main.py --assets SOL,MSOL,JITOSOL

  # Use custom swap sizes ($5M, $10M, $25M)
  python main.py --swap-sizes 5000000,10000000,25000000

  # Use paid Jupiter tier with API key
  python main.py --jupiter-api-key YOUR_KEY

  # Show summary pivot table
  python main.py --summary

  # Quiet mode (errors only)
  python main.py --quiet
        """,
    )

    parser.add_argument(
        "--market",
        type=str,
        default=MAIN_MARKET_PUBKEY,
        help=f"Kamino market pubkey (default: {MAIN_MARKET_PUBKEY[:8]}...)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output CSV file path",
    )

    parser.add_argument(
        "--assets",
        type=str,
        help="Comma-separated list of specific assets to analyze (e.g., SOL,MSOL,WBTC)",
    )

    parser.add_argument(
        "--swap-sizes",
        type=str,
        help="Comma-separated list of swap sizes in USD (e.g., 5000000,10000000)",
    )

    parser.add_argument(
        "--jupiter-api-key",
        type=str,
        help="Jupiter API key for paid tier (optional)",
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display summary pivot table",
    )

    parser.add_argument(
        "--include-failed",
        action="store_true",
        default=True,
        help="Include failed quotes in output (default: True)",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode - only show errors",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose mode - show debug output",
    )

    args = parser.parse_args()

    # Configure logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse optional arguments
    asset_filter = None
    if args.assets:
        try:
            asset_filter = parse_assets(args.assets)
            logger.info(f"Filtering to assets: {asset_filter}")
        except ValueError as e:
            logger.error(f"Error parsing assets: {e}")
            return 1

    swap_sizes_usd = None
    if args.swap_sizes:
        try:
            swap_sizes_usd = parse_swap_sizes(args.swap_sizes)
            logger.info(f"Using custom swap sizes: {swap_sizes_usd}")
        except ValueError as e:
            logger.error(f"Error parsing swap sizes: {e}")
            return 1

    # Run analysis
    try:
        logger.info("Starting analysis...")
        df = generate_liquidity_report(
            market_pubkey=args.market,
            jupiter_api_key=args.jupiter_api_key,
            swap_sizes_usd=swap_sizes_usd,
            asset_filter=asset_filter,
        )

        if df.empty:
            logger.error("No data generated - check logs for errors")
            return 1

        # Display summary if requested
        if args.summary:
            print("\n" + "=" * 80)
            print("PRICE IMPACT SUMMARY (% by Asset and Swap Size)")
            print("=" * 80)
            summary = summarize_report(df)
            if not summary.empty:
                print(summary.to_string())
            else:
                print("No successful quotes to summarize")
            print()

        # Export to CSV if requested
        if args.output:
            export_report(
                df,
                args.output,
                include_failed=args.include_failed,
            )
            logger.info(f"Results saved to: {args.output}")
        else:
            # Display first few rows
            print("\n" + "=" * 80)
            print("SAMPLE RESULTS (first 10 rows)")
            print("=" * 80)
            display_cols = [
                "asset_symbol",
                "swap_size_usd",
                "price_impact_pct",
                "output_usd",
                "router",
                "quote_success",
            ]
            print(df[display_cols].head(10).to_string(index=False))
            print(f"\nTotal rows: {len(df)}")
            print("Use --output to save full results to CSV")
            print()

        # Show risk flags if any
        high_risk_df = df[df["risk_flags"].apply(lambda x: len(x) > 0)]
        if len(high_risk_df) > 0:
            print("\n" + "=" * 80)
            print(f"HIGH-RISK SCENARIOS DETECTED: {len(high_risk_df)}")
            print("=" * 80)
            for _, row in high_risk_df.head(10).iterrows():
                print(
                    f"{row['asset_symbol']:10} | "
                    f"${row['swap_size_usd']/1e6:.0f}M | "
                    f"Impact: {row['price_impact_pct']:.2f}% | "
                    f"Flags: {', '.join(row['risk_flags'])}"
                )
            if len(high_risk_df) > 10:
                print(f"... and {len(high_risk_df) - 10} more")
            print()

        logger.info("Analysis complete!")
        return 0

    except KeyboardInterrupt:
        logger.warning("\nAnalysis interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
