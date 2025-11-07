"""
Configuration and constants for Kamino liquidity analysis.
"""

# Kamino Configuration
MAIN_MARKET_PUBKEY = "7u3HeHxYDLhnCoErrtycNokbQYbWGzLs6JSDqGAv5PfF"
KLEND_PROGRAM_ID = "KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD"

# API URLs
KAMINO_API_BASE = "https://api.kamino.finance"
JUPITER_API_BASE_FREE = "https://lite-api.jup.ag/ultra/v1"
JUPITER_API_BASE_PAID = "https://api.jup.ag/ultra/v1"

# Output token (USDC)
USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# Asset categories for filtering
SOL_BASED_ASSETS = [
    "SOL",
    "MSOL",      # Marinade SOL
    "JITOSOL",   # Jito SOL
    "BSOL",      # Blaze SOL
    "STSOL",     # Lido staked SOL
    "JSOL",      # Jupiter SOL
    "BNSOL",     # BlazeStake SOL
    "HBSOL",     # Hubble SOL
    "COMPASSSOL", # Compass SOL
    "SUPSOL",    # Superfast SOL
    "INF",       # Infinity SOL
]

BTC_BASED_ASSETS = [
    "WBTC",      # Wrapped BTC
    "LBTC",      # Lombard BTC
    "TBTC",      # Threshold BTC
    "SBTC",      # Solana BTC
]

ETH_BASED_ASSETS = [
    "WETH",      # Wrapped ETH
    "STETH",     # Lido staked ETH
    "RETH",      # Rocket Pool ETH
    "CBETH",     # Coinbase ETH
]

# Combine all volatile assets
VOLATILE_ASSETS = SOL_BASED_ASSETS + BTC_BASED_ASSETS + ETH_BASED_ASSETS

# Swap size bands to test (in USD)
SWAP_SIZE_BANDS_USD = [
    1_000_000,      # $1M
    5_000_000,      # $5M
    10_000_000,     # $10M
    20_000_000,     # $20M
    50_000_000,     # $50M
    100_000_000,    # $100M
]

# API Configuration
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # exponential backoff multiplier
RATE_LIMIT_DELAY = 0.5  # seconds between Jupiter API calls

# Risk Thresholds
HIGH_PRICE_IMPACT_THRESHOLD = 5.0  # percent
ROUTE_CONCENTRATION_THRESHOLD = 70.0  # percent
MIN_TVL_MULTIPLE = 5.0  # TVL should be at least 5x swap size
