"""
Utility functions for token conversions and helper operations.
"""

from typing import Optional
from decimal import Decimal, ROUND_DOWN


def usd_to_native_units(
    amount_usd: float,
    token_price_usd: float,
    decimals: int
) -> int:
    """
    Convert USD amount to native token units.

    Args:
        amount_usd: USD amount to convert
        token_price_usd: Current token price in USD
        decimals: Token decimal places

    Returns:
        Amount in native token units (smallest denomination)

    Example:
        $10M of SOL at $200/SOL with 9 decimals
        = 10_000_000 / 200 = 50,000 SOL
        = 50,000 * 10^9 = 50,000,000,000,000 lamports
    """
    if token_price_usd <= 0:
        raise ValueError(f"Invalid token price: {token_price_usd}")

    # Use Decimal for precision
    amount_decimal = Decimal(str(amount_usd))
    price_decimal = Decimal(str(token_price_usd))

    # Calculate token amount
    token_amount = amount_decimal / price_decimal

    # Convert to native units
    multiplier = Decimal(10 ** decimals)
    native_amount = int((token_amount * multiplier).to_integral_value(ROUND_DOWN))

    return native_amount


def native_to_usd(
    amount_native: int,
    token_price_usd: float,
    decimals: int
) -> float:
    """
    Convert native units back to USD.

    Args:
        amount_native: Amount in native units (smallest denomination)
        token_price_usd: Current token price in USD
        decimals: Token decimal places

    Returns:
        USD value as float
    """
    token_amount = amount_native / (10 ** decimals)
    return token_amount * token_price_usd


def native_to_tokens(
    amount_native: int,
    decimals: int
) -> float:
    """
    Convert native units to human-readable token amount.

    Args:
        amount_native: Amount in native units
        decimals: Token decimal places

    Returns:
        Token amount as float
    """
    return amount_native / (10 ** decimals)


def tokens_to_native(
    amount_tokens: float,
    decimals: int
) -> int:
    """
    Convert token amount to native units.

    Args:
        amount_tokens: Human-readable token amount
        decimals: Token decimal places

    Returns:
        Amount in native units
    """
    return int(amount_tokens * (10 ** decimals))


def format_usd(amount: float) -> str:
    """Format USD amount for display."""
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.2f}K"
    else:
        return f"${amount:.2f}"


def calculate_effective_price(
    amount_in_usd: float,
    amount_out_usd: float,
    original_price: float
) -> float:
    """
    Calculate effective price after price impact.

    Args:
        amount_in_usd: Input amount in USD
        amount_out_usd: Output amount received in USD
        original_price: Original token price

    Returns:
        Effective price per token after impact
    """
    if amount_in_usd <= 0:
        return 0.0

    # Calculate how much value was lost
    price_ratio = amount_out_usd / amount_in_usd
    effective_price = original_price * price_ratio

    return effective_price


def parse_route_summary(route_plan: list) -> str:
    """
    Parse Jupiter route plan to get summary of top DEXes.

    Args:
        route_plan: List of route steps from Jupiter response

    Returns:
        Comma-separated string of top DEXes
    """
    if not route_plan:
        return "Unknown"

    # Extract swap info from route plan
    dexes = []
    for step in route_plan:
        if isinstance(step, dict):
            # Try different possible field names
            swap_info = step.get('swapInfo', step.get('swap_info', {}))
            if isinstance(swap_info, dict):
                label = swap_info.get('label', swap_info.get('ammKey', 'Unknown'))
                if label and label not in dexes:
                    dexes.append(label)

    # Return top 3 DEXes
    return ", ".join(dexes[:3]) if dexes else "Unknown"


def calculate_route_concentration(route_plan: list) -> Optional[float]:
    """
    Calculate concentration risk - what % comes from largest pool.

    Args:
        route_plan: List of route steps from Jupiter response

    Returns:
        Percentage of swap from largest single pool, or None if unable to calculate
    """
    if not route_plan:
        return None

    # Try to extract percentages from route plan
    percentages = []
    for step in route_plan:
        if isinstance(step, dict):
            swap_info = step.get('swapInfo', step.get('swap_info', {}))
            if isinstance(swap_info, dict):
                percent = swap_info.get('percent', swap_info.get('percentage'))
                if percent is not None:
                    percentages.append(float(percent))

    if percentages:
        return max(percentages)

    return None
