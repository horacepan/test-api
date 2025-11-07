"""
Main analysis logic for Kamino liquidity assessment.
"""

import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime
import logging

from constants import (
    MAIN_MARKET_PUBKEY,
    SWAP_SIZE_BANDS_USD,
    VOLATILE_ASSETS,
    HIGH_PRICE_IMPACT_THRESHOLD,
    ROUTE_CONCENTRATION_THRESHOLD,
    MIN_TVL_MULTIPLE,
)
from kamino_client import KaminoClient
from jupiter_client import JupiterClient
from utils import format_usd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LiquidityAnalyzer:
    """Main analyzer for Kamino liquidity risk assessment."""

    def __init__(
        self,
        market_pubkey: str = MAIN_MARKET_PUBKEY,
        jupiter_api_key: Optional[str] = None,
        swap_sizes_usd: Optional[List[float]] = None,
    ):
        """
        Initialize analyzer.

        Args:
            market_pubkey: Kamino market to analyze
            jupiter_api_key: Optional Jupiter API key
            swap_sizes_usd: Custom swap sizes to test
        """
        self.market_pubkey = market_pubkey
        self.kamino_client = KaminoClient()
        self.jupiter_client = JupiterClient(api_key=jupiter_api_key)
        self.swap_sizes_usd = swap_sizes_usd or SWAP_SIZE_BANDS_USD

    def generate_liquidity_report(
        self,
        asset_filter: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Main analysis function.

        Workflow:
        1. Fetch all reserves from Kamino
        2. Filter to volatile collateral (SOL/BTC/ETH based)
        3. For each asset:
           a. Query Jupiter across all swap size bands
           b. Collect price impact, output amounts
        4. Compile into DataFrame

        Args:
            asset_filter: Optional list of specific assets to analyze

        Returns:
            DataFrame with columns:
            - asset_symbol
            - mint_address
            - current_price_usd
            - current_tvl_usd
            - swap_size_usd
            - swap_size_tokens
            - price_impact_pct
            - output_usd
            - effective_price
            - slippage_bps
            - router
            - route_summary
            - route_concentration
            - quote_success
            - error_msg
            - timestamp
            - risk_flags
        """
        logger.info("=" * 80)
        logger.info("Starting Kamino Liquidity Analysis")
        logger.info("=" * 80)

        # Step 1: Fetch reserves
        logger.info(f"Fetching reserves from market: {self.market_pubkey}")
        all_reserves = self.kamino_client.fetch_market_reserves(self.market_pubkey)

        if not all_reserves:
            logger.error("No reserves fetched from Kamino")
            return pd.DataFrame()

        logger.info(f"Fetched {len(all_reserves)} total reserves")

        # Step 2: Filter to volatile collateral
        volatile_reserves = self.kamino_client.filter_volatile_collateral(
            all_reserves,
            asset_symbols=asset_filter or VOLATILE_ASSETS,
        )

        if not volatile_reserves:
            logger.warning("No volatile assets found matching criteria")
            return pd.DataFrame()

        logger.info(f"Analyzing {len(volatile_reserves)} volatile assets")

        # Step 3: Analyze each asset
        all_results = []
        timestamp = datetime.utcnow()

        for i, reserve in enumerate(volatile_reserves, 1):
            symbol = reserve["symbol"]
            logger.info(f"\n[{i}/{len(volatile_reserves)}] Analyzing {symbol}...")
            logger.info(f"  TVL: {format_usd(reserve['tvl_usd'])}")
            logger.info(f"  Price: ${reserve['usd_price']:.2f}")

            # Query Jupiter for liquidity depth
            liquidity_results = self.jupiter_client.analyze_liquidity_depth(
                input_mint=reserve["mint_address"],
                token_decimals=reserve["decimals"],
                token_price_usd=reserve["usd_price"],
                swap_sizes_usd=self.swap_sizes_usd,
            )

            # Combine reserve data with liquidity results
            for result in liquidity_results:
                risk_flags = self._identify_risk_flags(
                    reserve=reserve,
                    liquidity_result=result,
                )

                all_results.append({
                    "asset_symbol": symbol,
                    "mint_address": reserve["mint_address"],
                    "current_price_usd": reserve["usd_price"],
                    "current_tvl_usd": reserve["tvl_usd"],
                    "swap_size_usd": result["swap_size_usd"],
                    "swap_size_tokens": result["swap_size_tokens"],
                    "price_impact_pct": result["price_impact_pct"],
                    "output_usd": result["output_usd"],
                    "effective_price": result["effective_price"],
                    "slippage_bps": result.get("slippage_bps", 0),
                    "router": result["router"],
                    "route_summary": result.get("route_summary"),
                    "route_concentration": result.get("route_concentration"),
                    "quote_success": result["success"],
                    "error_msg": result.get("error"),
                    "timestamp": timestamp,
                    "risk_flags": risk_flags,
                })

                # Log result
                if result["success"]:
                    logger.info(
                        f"  {format_usd(result['swap_size_usd'])}: "
                        f"{result['price_impact_pct']:.2f}% impact, "
                        f"{format_usd(result['output_usd'])} output "
                        f"[{result['router']}]"
                    )
                else:
                    logger.warning(
                        f"  {format_usd(result['swap_size_usd'])}: "
                        f"FAILED - {result.get('error', 'Unknown error')}"
                    )

        # Step 4: Create DataFrame
        df = pd.DataFrame(all_results)

        logger.info("\n" + "=" * 80)
        logger.info("Analysis Complete")
        logger.info("=" * 80)
        logger.info(f"Total scenarios analyzed: {len(df)}")
        logger.info(f"Successful quotes: {df['quote_success'].sum()}")
        logger.info(f"Failed quotes: {(~df['quote_success']).sum()}")

        if len(df) > 0:
            # Summary statistics
            successful_df = df[df['quote_success']]
            if len(successful_df) > 0:
                logger.info(f"\nPrice Impact Statistics:")
                logger.info(f"  Mean: {successful_df['price_impact_pct'].mean():.2f}%")
                logger.info(f"  Median: {successful_df['price_impact_pct'].median():.2f}%")
                logger.info(f"  Max: {successful_df['price_impact_pct'].max():.2f}%")

                # Risk flags summary
                high_risk_count = df['risk_flags'].apply(lambda x: len(x) > 0).sum()
                logger.info(f"\nHigh-risk scenarios flagged: {high_risk_count}")

        return df

    def _identify_risk_flags(
        self,
        reserve: Dict,
        liquidity_result: Dict,
    ) -> List[str]:
        """
        Identify risk flags for a given scenario.

        Args:
            reserve: Reserve data
            liquidity_result: Liquidity depth result

        Returns:
            List of risk flag strings
        """
        flags = []

        if not liquidity_result["success"]:
            flags.append("QUOTE_FAILED")
            return flags

        # High price impact
        price_impact = liquidity_result.get("price_impact_pct")
        if price_impact and price_impact > HIGH_PRICE_IMPACT_THRESHOLD:
            flags.append(f"HIGH_IMPACT_{price_impact:.1f}%")

        # Route concentration
        concentration = liquidity_result.get("route_concentration")
        if concentration and concentration > ROUTE_CONCENTRATION_THRESHOLD:
            flags.append(f"CONCENTRATED_ROUTE_{concentration:.0f}%")

        # TVL vs swap size ratio
        swap_size = liquidity_result["swap_size_usd"]
        tvl = reserve["tvl_usd"]
        if tvl > 0:
            tvl_ratio = tvl / swap_size
            if tvl_ratio < MIN_TVL_MULTIPLE:
                flags.append(f"LOW_TVL_RATIO_{tvl_ratio:.1f}x")

        return flags


def generate_liquidity_report(
    market_pubkey: str = MAIN_MARKET_PUBKEY,
    jupiter_api_key: Optional[str] = None,
    swap_sizes_usd: Optional[List[float]] = None,
    asset_filter: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Convenience function to generate liquidity report.

    Args:
        market_pubkey: Kamino market to analyze
        jupiter_api_key: Optional Jupiter API key
        swap_sizes_usd: Custom swap sizes
        asset_filter: Optional list of assets to analyze

    Returns:
        Analysis DataFrame
    """
    analyzer = LiquidityAnalyzer(
        market_pubkey=market_pubkey,
        jupiter_api_key=jupiter_api_key,
        swap_sizes_usd=swap_sizes_usd,
    )
    return analyzer.generate_liquidity_report(asset_filter=asset_filter)


def export_report(
    df: pd.DataFrame,
    output_path: str,
    include_failed: bool = True,
) -> None:
    """
    Export analysis report to CSV.

    Args:
        df: Analysis DataFrame
        output_path: Path to save CSV
        include_failed: Whether to include failed quotes
    """
    if not include_failed:
        df = df[df["quote_success"]]

    df.to_csv(output_path, index=False)
    logger.info(f"Report exported to: {output_path}")


def summarize_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create summary pivot table of price impacts.

    Args:
        df: Analysis DataFrame

    Returns:
        Pivot table with assets vs swap sizes
    """
    if len(df) == 0:
        return pd.DataFrame()

    successful_df = df[df["quote_success"]]

    if len(successful_df) == 0:
        logger.warning("No successful quotes to summarize")
        return pd.DataFrame()

    pivot = successful_df.pivot_table(
        index="asset_symbol",
        columns="swap_size_usd",
        values="price_impact_pct",
        aggfunc="first",
    )

    # Format column names
    pivot.columns = [format_usd(col) for col in pivot.columns]

    return pivot
