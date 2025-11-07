"""
Jupiter Aggregator API client for querying swap quotes and price impact.
"""

import requests
from typing import List, Dict, Optional
import logging
import time

from constants import (
    JUPITER_API_BASE_FREE,
    JUPITER_API_BASE_PAID,
    USDC_MINT,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_BACKOFF_FACTOR,
    RATE_LIMIT_DELAY,
    SWAP_SIZE_BANDS_USD,
)
from utils import (
    usd_to_native_units,
    native_to_usd,
    native_to_tokens,
    parse_route_summary,
    calculate_route_concentration,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JupiterClient:
    """Client for interacting with Jupiter Aggregator API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_paid_tier: bool = False,
    ):
        """
        Initialize Jupiter client.

        Args:
            api_key: Optional API key for paid tier
            use_paid_tier: Whether to use paid tier endpoint
        """
        self.api_key = api_key
        self.api_base = JUPITER_API_BASE_PAID if (use_paid_tier or api_key) else JUPITER_API_BASE_FREE
        self.session = requests.Session()

        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def query_swap_price_impact(
        self,
        input_mint: str,
        output_mint: str,
        amount_in_native: int,
        taker: Optional[str] = None,
    ) -> Dict:
        """
        Query Jupiter for swap quote.

        Args:
            input_mint: Source token mint address
            output_mint: Destination token mint (typically USDC)
            amount_in_native: Amount in smallest unit (e.g., lamports for SOL)
            taker: Optional wallet address

        Returns:
            Dictionary with:
            - price_impact: float (as percentage, e.g., 2.5 for 2.5%)
            - out_amount: int (in native units)
            - out_amount_usd: float
            - slippage_bps: int
            - router: str
            - route_info: List[Dict] (DEX breakdown)
            - success: bool
            - error: Optional[str]
        """
        url = f"{self.api_base}/order"
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount_in_native),
        }

        if taker:
            params["taker"] = taker

        logger.debug(f"Querying Jupiter for swap: {input_mint[:8]}... -> {output_mint[:8]}...")

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=REQUEST_TIMEOUT,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    logger.warning("Rate limited, backing off...")
                    time.sleep(RETRY_BACKOFF_FACTOR ** (attempt + 1))
                    continue

                response.raise_for_status()
                data = response.json()

                # Parse successful response
                return self._parse_quote_response(data)

            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed: {e}")

                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF_FACTOR ** attempt)
                else:
                    # Return error result
                    return {
                        "price_impact": None,
                        "out_amount": 0,
                        "out_amount_usd": 0.0,
                        "slippage_bps": 0,
                        "router": None,
                        "route_info": [],
                        "success": False,
                        "error": str(e),
                    }

        # Should not reach here, but return error just in case
        return {
            "price_impact": None,
            "out_amount": 0,
            "out_amount_usd": 0.0,
            "slippage_bps": 0,
            "router": None,
            "route_info": [],
            "success": False,
            "error": "Max retries exceeded",
        }

    def _parse_quote_response(self, data: Dict) -> Dict:
        """
        Parse Jupiter quote response into standardized format.

        Args:
            data: Raw response from Jupiter API

        Returns:
            Standardized quote dictionary
        """
        try:
            # Extract price impact (as decimal, convert to percentage)
            price_impact_decimal = data.get("priceImpact", 0)
            if isinstance(price_impact_decimal, str):
                price_impact_decimal = float(price_impact_decimal)
            price_impact_pct = abs(price_impact_decimal * 100)  # Convert to percentage

            # Extract output amount
            out_amount = data.get("outAmount", 0)
            if isinstance(out_amount, str):
                out_amount = int(out_amount)

            # Extract other fields
            slippage_bps = data.get("slippageBps", 0)
            router = data.get("router", "unknown")
            route_plan = data.get("routePlan", [])

            return {
                "price_impact": price_impact_pct,
                "out_amount": out_amount,
                "out_amount_usd": 0.0,  # Will be calculated by caller
                "slippage_bps": slippage_bps,
                "router": router,
                "route_info": route_plan,
                "route_summary": parse_route_summary(route_plan),
                "route_concentration": calculate_route_concentration(route_plan),
                "success": True,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Failed to parse Jupiter response: {e}")
            return {
                "price_impact": None,
                "out_amount": 0,
                "out_amount_usd": 0.0,
                "slippage_bps": 0,
                "router": None,
                "route_info": [],
                "success": False,
                "error": f"Parse error: {e}",
            }

    def analyze_liquidity_depth(
        self,
        input_mint: str,
        token_decimals: int,
        token_price_usd: float,
        output_decimals: int = 6,  # USDC has 6 decimals
        output_price_usd: float = 1.0,  # USDC is $1
        swap_sizes_usd: Optional[List[float]] = None,
    ) -> List[Dict]:
        """
        Test multiple swap sizes and return liquidity curve.

        Args:
            input_mint: Token mint to swap from
            token_decimals: Decimals for input token
            token_price_usd: Current price of input token
            output_decimals: Decimals for output token (USDC)
            output_price_usd: Price of output token (typically $1 for USDC)
            swap_sizes_usd: List of USD amounts to test

        Returns:
            List of dictionaries with:
            - swap_size_usd: float
            - swap_size_native: int
            - swap_size_tokens: float
            - price_impact_pct: float
            - output_usd: float
            - effective_price: float
            - router: str
            - route_summary: str
            - success: bool
            - error: Optional[str]
        """
        if swap_sizes_usd is None:
            swap_sizes_usd = SWAP_SIZE_BANDS_USD

        results = []

        for swap_size_usd in swap_sizes_usd:
            # Convert USD to native units
            try:
                amount_native = usd_to_native_units(
                    swap_size_usd,
                    token_price_usd,
                    token_decimals,
                )
            except ValueError as e:
                logger.error(f"Failed to convert {swap_size_usd} USD: {e}")
                results.append({
                    "swap_size_usd": swap_size_usd,
                    "swap_size_native": 0,
                    "swap_size_tokens": 0.0,
                    "price_impact_pct": None,
                    "output_usd": 0.0,
                    "effective_price": 0.0,
                    "router": None,
                    "route_summary": None,
                    "route_concentration": None,
                    "success": False,
                    "error": str(e),
                })
                continue

            swap_size_tokens = native_to_tokens(amount_native, token_decimals)

            # Query Jupiter
            quote = self.query_swap_price_impact(
                input_mint=input_mint,
                output_mint=USDC_MINT,
                amount_in_native=amount_native,
            )

            # Calculate output USD value
            if quote["success"] and quote["out_amount"] > 0:
                output_usd = native_to_usd(
                    quote["out_amount"],
                    output_price_usd,
                    output_decimals,
                )
                quote["out_amount_usd"] = output_usd

                # Calculate effective price
                effective_price = output_usd / swap_size_tokens if swap_size_tokens > 0 else 0.0
            else:
                output_usd = 0.0
                effective_price = 0.0

            results.append({
                "swap_size_usd": swap_size_usd,
                "swap_size_native": amount_native,
                "swap_size_tokens": swap_size_tokens,
                "price_impact_pct": quote["price_impact"],
                "output_usd": output_usd,
                "effective_price": effective_price,
                "slippage_bps": quote["slippage_bps"],
                "router": quote["router"],
                "route_summary": quote.get("route_summary"),
                "route_concentration": quote.get("route_concentration"),
                "success": quote["success"],
                "error": quote.get("error"),
            })

            # Rate limiting - add delay between requests
            time.sleep(RATE_LIMIT_DELAY)

        return results


def query_swap_price_impact(
    input_mint: str,
    output_mint: str,
    amount_in_native: int,
    api_key: Optional[str] = None,
) -> Dict:
    """
    Convenience function to query swap price impact.

    Args:
        input_mint: Source token mint
        output_mint: Destination token mint
        amount_in_native: Amount in native units
        api_key: Optional API key

    Returns:
        Quote dictionary
    """
    client = JupiterClient(api_key=api_key)
    return client.query_swap_price_impact(input_mint, output_mint, amount_in_native)


def analyze_liquidity_depth(
    input_mint: str,
    token_decimals: int,
    token_price_usd: float,
    swap_sizes_usd: Optional[List[float]] = None,
    api_key: Optional[str] = None,
) -> List[Dict]:
    """
    Convenience function to analyze liquidity depth.

    Args:
        input_mint: Token mint to analyze
        token_decimals: Token decimals
        token_price_usd: Current token price
        swap_sizes_usd: List of swap sizes to test
        api_key: Optional API key

    Returns:
        List of liquidity depth results
    """
    client = JupiterClient(api_key=api_key)
    return client.analyze_liquidity_depth(
        input_mint,
        token_decimals,
        token_price_usd,
        swap_sizes_usd=swap_sizes_usd,
    )
