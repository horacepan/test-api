"""
Kamino Liquidity Analysis Tool

A Python-based tool to assess liquidity risk for Kamino's Main Market
by simulating liquidation scenarios and querying Jupiter for price impact.
"""

from .analyzer import generate_liquidity_report, export_report, summarize_report
from .kamino_client import KaminoClient, fetch_market_reserves, filter_volatile_collateral
from .jupiter_client import JupiterClient, query_swap_price_impact, analyze_liquidity_depth
from .constants import (
    MAIN_MARKET_PUBKEY,
    KLEND_PROGRAM_ID,
    USDC_MINT,
    SWAP_SIZE_BANDS_USD,
    VOLATILE_ASSETS,
    SOL_BASED_ASSETS,
    BTC_BASED_ASSETS,
    ETH_BASED_ASSETS,
)

__version__ = "1.0.0"
__all__ = [
    # Main functions
    "generate_liquidity_report",
    "export_report",
    "summarize_report",
    # Clients
    "KaminoClient",
    "JupiterClient",
    # Kamino functions
    "fetch_market_reserves",
    "filter_volatile_collateral",
    # Jupiter functions
    "query_swap_price_impact",
    "analyze_liquidity_depth",
    # Constants
    "MAIN_MARKET_PUBKEY",
    "KLEND_PROGRAM_ID",
    "USDC_MINT",
    "SWAP_SIZE_BANDS_USD",
    "VOLATILE_ASSETS",
    "SOL_BASED_ASSETS",
    "BTC_BASED_ASSETS",
    "ETH_BASED_ASSETS",
]
