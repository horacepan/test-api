"""
Kamino API client for fetching market and reserve data.
"""

import requests
from typing import List, Dict, Optional
import logging
from decimal import Decimal

from constants import (
    KAMINO_API_BASE,
    MAIN_MARKET_PUBKEY,
    KLEND_PROGRAM_ID,
    VOLATILE_ASSETS,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_BACKOFF_FACTOR,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KaminoClient:
    """Client for interacting with Kamino API."""

    def __init__(
        self,
        api_base: str = KAMINO_API_BASE,
        program_id: str = KLEND_PROGRAM_ID,
    ):
        self.api_base = api_base
        self.program_id = program_id
        self.session = requests.Session()

    def fetch_market_reserves(
        self,
        market_pubkey: str = MAIN_MARKET_PUBKEY,
    ) -> List[Dict]:
        """
        Fetch all reserves from Kamino market.

        Args:
            market_pubkey: Market public key to query

        Returns:
            List of reserve dictionaries with standardized keys:
            - symbol: str
            - mint_address: str
            - decimals: int
            - total_deposits: float (in token units, not native)
            - usd_price: float
            - tvl_usd: float
            - reserve_pubkey: str

        Raises:
            requests.RequestException: If API call fails
        """
        url = f"{self.api_base}/kamino-market/{market_pubkey}"
        params = {"programId": self.program_id}

        logger.info(f"Fetching market data from Kamino API: {market_pubkey}")

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                data = response.json()

                # Parse reserves from response
                reserves = self._parse_reserves(data)
                logger.info(f"Successfully fetched {len(reserves)} reserves")
                return reserves

            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    import time
                    time.sleep(RETRY_BACKOFF_FACTOR ** attempt)
                else:
                    logger.error("Max retries reached, raising exception")
                    raise

        return []

    def _parse_reserves(self, market_data: Dict) -> List[Dict]:
        """
        Parse raw market data into standardized reserve format.

        Args:
            market_data: Raw response from Kamino API

        Returns:
            List of parsed reserve dictionaries
        """
        reserves = []

        # The response structure may vary, handle different formats
        reserves_data = market_data.get("reserves", [])

        if not reserves_data:
            # Try alternative structure
            reserves_data = market_data.get("data", {}).get("reserves", [])

        for reserve_raw in reserves_data:
            try:
                reserve = self._parse_single_reserve(reserve_raw)
                if reserve:
                    reserves.append(reserve)
            except Exception as e:
                logger.warning(f"Failed to parse reserve: {e}")
                continue

        return reserves

    def _parse_single_reserve(self, reserve_data: Dict) -> Optional[Dict]:
        """
        Parse a single reserve entry.

        Args:
            reserve_data: Raw reserve data from API

        Returns:
            Standardized reserve dictionary or None if parsing fails
        """
        try:
            # Extract basic info
            symbol = reserve_data.get("symbol", "").upper()
            mint_address = reserve_data.get("mintAddress", reserve_data.get("mint"))
            decimals = reserve_data.get("decimals", 0)
            reserve_pubkey = reserve_data.get("reserve", reserve_data.get("address"))

            if not symbol or not mint_address:
                logger.warning(f"Missing symbol or mint address in reserve data")
                return None

            # Extract price
            price = reserve_data.get("assetPriceUSD", 0.0)
            if isinstance(price, str):
                price = float(price)

            # Extract total deposits/liquidity
            # Different possible field names
            total_deposits_wads = reserve_data.get(
                "totalLiquidityWads",
                reserve_data.get("totalDepositsWads", 0)
            )

            # Convert from wads (native units) to token units
            if isinstance(total_deposits_wads, str):
                total_deposits_wads = int(total_deposits_wads)
            elif isinstance(total_deposits_wads, float):
                total_deposits_wads = int(total_deposits_wads)

            total_deposits = total_deposits_wads / (10 ** decimals)

            # Calculate TVL
            tvl_usd = total_deposits * price

            return {
                "symbol": symbol,
                "mint_address": mint_address,
                "decimals": decimals,
                "total_deposits": total_deposits,
                "usd_price": price,
                "tvl_usd": tvl_usd,
                "reserve_pubkey": reserve_pubkey,
            }

        except Exception as e:
            logger.warning(f"Error parsing reserve: {e}")
            return None

    def filter_volatile_collateral(
        self,
        reserves: List[Dict],
        asset_symbols: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Filter reserves to only volatile collateral we care about.

        Args:
            reserves: List of all reserves
            asset_symbols: List of symbols to filter for (default: VOLATILE_ASSETS)

        Returns:
            Filtered list of reserves
        """
        if asset_symbols is None:
            asset_symbols = VOLATILE_ASSETS

        # Create set for faster lookup (case-insensitive)
        symbols_upper = {s.upper() for s in asset_symbols}

        filtered = []
        for reserve in reserves:
            symbol = reserve.get("symbol", "").upper()
            if symbol in symbols_upper:
                filtered.append(reserve)

        logger.info(
            f"Filtered {len(reserves)} reserves to {len(filtered)} volatile assets"
        )
        return filtered


def fetch_market_reserves(
    market_pubkey: str = MAIN_MARKET_PUBKEY,
    program_id: str = KLEND_PROGRAM_ID,
) -> List[Dict]:
    """
    Convenience function to fetch market reserves.

    Args:
        market_pubkey: Market public key
        program_id: Kamino program ID

    Returns:
        List of reserve dictionaries
    """
    client = KaminoClient(program_id=program_id)
    return client.fetch_market_reserves(market_pubkey)


def filter_volatile_collateral(
    reserves: List[Dict],
    asset_symbols: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Convenience function to filter volatile collateral.

    Args:
        reserves: List of all reserves
        asset_symbols: List of symbols to filter for

    Returns:
        Filtered list of reserves
    """
    client = KaminoClient()
    return client.filter_volatile_collateral(reserves, asset_symbols)
