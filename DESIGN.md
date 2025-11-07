# Kamino Liquidity Analysis Tool - Design Document

This document captures the complete design specification for the Kamino Liquidity Analysis Tool.

## 1. Overview

### 1.1 Purpose
Build a Python-based analysis tool to assess liquidity risk for Kamino's Main Market by simulating liquidation scenarios. Given various drawdown percentages on collateral assets, determine how much can be swapped to USDC and at what price impact.

### 1.2 Scope
- **In Scope:**
  - Fetch all reserves from Kamino Main Market via API
  - Filter for volatile collateral (SOL, BTC, ETH based assets)
  - Query Jupiter aggregator for price impact across multiple swap sizes
  - Generate on-demand analysis table

- **Out of Scope:**
  - Historical tracking / data persistence (explicitly excluded per requirements)
  - Automated monitoring / alerting
  - Multi-market analysis (only Main Market: `7u3HeHxYDLhnCoErrtycNokbQYbWGzLs6JSDqGAv5PfF`)

## 2. Technical Architecture

### 2.1 Data Sources

#### Kamino API
- **Base URL:** `https://api.kamino.finance`
- **Program ID:** `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`
- **Main Market Pubkey:** `7u3HeHxYDLhnCoErrtycNokbQYbWGzLs6JSDqGAv5PfF`

#### Jupiter Aggregator API
- **Base URL:** `https://lite-api.jup.ag/ultra/v1` (free tier) or `https://api.jup.ag/ultra/v1` (paid tier)
- **Primary Endpoint:** GET `/order?inputMint={mint}&outputMint={mint}&amount={amount}`

### 2.2 Module Structure

```
kamino_liquidity_analysis/
├── __init__.py           # Package exports
├── constants.py          # Configuration and constants
├── kamino_client.py      # Kamino API interactions
├── jupiter_client.py     # Jupiter API interactions
├── utils.py              # Helper functions (token conversions, etc.)
├── analyzer.py           # Main analysis logic
└── main.py              # CLI entry point
```

## 3. Asset Configuration

### Volatile Assets Tracked
- **SOL-based:** SOL, MSOL, JITOSOL, BSOL, STSOL, JSOL, etc.
- **BTC-based:** WBTC, LBTC, TBTC
- **ETH-based:** WETH, STETH, RETH, CBETH

### Swap Size Bands (USD)
- $1M, $5M, $10M, $20M, $50M, $100M

## 4. Key Features

### 4.1 Liquidity Depth Analysis
- Tests multiple swap sizes per asset
- Queries real liquidity via Jupiter
- Calculates price impact and effective prices

### 4.2 Risk Identification
Automatically flags:
- **HIGH_IMPACT**: Price impact > 5%
- **CONCENTRATED_ROUTE**: >70% from single pool
- **LOW_TVL_RATIO**: TVL < 5x swap size
- **QUOTE_FAILED**: No route found

### 4.3 Output Formats
- CSV export
- Pandas DataFrame
- Summary pivot tables
- CLI display

## 5. Implementation Details

### 5.1 Token Decimal Handling
Different tokens have different decimals:
- SOL: 9 decimals
- USDC: 6 decimals
- BTC: 8 decimals

Always uses the `decimals` field from Kamino API.

### 5.2 Rate Limiting
- Kamino API: Single call at start
- Jupiter API: 0.5s delay between calls
- Exponential backoff on failures
- Max 3 retries per request

### 5.3 Error Handling
- Graceful handling of API failures
- Continues analysis if some quotes fail
- Logs all errors with context
- Returns success/failure per quote

## 6. Usage Examples

### CLI
```bash
# Basic usage
python kamino_liquidity_analysis/main.py

# Save to CSV
python kamino_liquidity_analysis/main.py --output analysis.csv

# Specific assets
python kamino_liquidity_analysis/main.py --assets SOL,MSOL

# Custom swap sizes
python kamino_liquidity_analysis/main.py --swap-sizes 5000000,10000000
```

### Python API
```python
from kamino_liquidity_analysis import generate_liquidity_report

df = generate_liquidity_report()
print(df.head())
```

## 7. Output Schema

The analysis generates a DataFrame with:

| Column | Type | Description |
|--------|------|-------------|
| asset_symbol | str | Token symbol |
| mint_address | str | Token mint address |
| current_price_usd | float | Current token price |
| current_tvl_usd | float | Total deposits on Kamino |
| swap_size_usd | float | Hypothetical swap size |
| swap_size_tokens | float | Swap size in token terms |
| price_impact_pct | float | Price impact % |
| output_usd | float | Actual USD received |
| effective_price | float | Actual price after impact |
| slippage_bps | int | Slippage in basis points |
| router | str | Jupiter router used |
| route_summary | str | Top DEXes used |
| route_concentration | float | % from largest pool |
| quote_success | bool | Whether quote succeeded |
| error_msg | str | Error message if failed |
| timestamp | datetime | When analysis was run |
| risk_flags | List[str] | Risk flags identified |

## 8. Testing Strategy

### Unit Tests
- Token conversion accuracy
- API response parsing
- Risk flag logic

### Integration Tests
- Live API connectivity
- End-to-end analysis flow
- Error handling

### Validation
- Compare with Kamino UI
- Spot-check Jupiter quotes
- Verify decimal handling

## 9. Future Enhancements

Potential additions (currently out of scope):
- Historical tracking
- Multi-asset liquidation scenarios
- Time-of-day analysis
- Automated alerting
- Multi-market support
- Gas cost estimates

## 10. Dependencies

- `requests` - API calls
- `pandas` - Data analysis
- `python-dotenv` - Configuration
- `aiohttp` - Async operations (optional)
- `jupyter` - Notebooks (optional)
- `matplotlib` - Visualization (optional)

## 11. Risk Thresholds

Configurable in `constants.py`:
- High price impact: 5%
- Route concentration: 70%
- Min TVL multiple: 5x

## 12. Deliverables

✓ Core Python modules
✓ Configuration files
✓ CLI interface
✓ Example Jupyter notebook
✓ README documentation
✓ This design document
✓ Test scripts
✓ Setup/installation files

---

**Status:** Complete
**Version:** 1.0.0
**Last Updated:** 2025-11-07
