# Kamino Liquidity Analysis Tool

A Python-based analysis tool to assess liquidity risk for Kamino's Main Market by simulating liquidation scenarios. Given various drawdown percentages on collateral assets, this tool determines how much can be swapped to USDC and at what price impact.

## Overview

This tool helps assess the liquidation risk of volatile collateral assets (SOL, BTC, ETH-based tokens) on Kamino Finance by:

1. Fetching reserve data from Kamino's Main Market
2. Querying Jupiter Aggregator for realistic swap quotes
3. Testing multiple swap size scenarios ($1M to $100M)
4. Identifying liquidity risks and concentration issues

## Features

- **Real-time Analysis**: Query live data from Kamino and Jupiter APIs
- **Multiple Assets**: Analyze SOL, BTC, and ETH-based collateral
- **Liquidity Depth Testing**: Test swap sizes from $1M to $100M
- **Risk Flagging**: Automatically identify high-risk scenarios
- **Flexible Output**: CSV export, summary tables, and programmatic access
- **CLI and Library**: Use as command-line tool or import as Python library

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd test-api

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Command Line Usage

```bash
# Basic analysis of all volatile assets
python kamino_liquidity_analysis/main.py

# Save results to CSV
python kamino_liquidity_analysis/main.py --output analysis.csv

# Analyze specific assets
python kamino_liquidity_analysis/main.py --assets SOL,MSOL,JITOSOL

# Use custom swap sizes
python kamino_liquidity_analysis/main.py --swap-sizes 5000000,10000000,25000000

# Show summary table
python kamino_liquidity_analysis/main.py --summary

# Use Jupiter API key (paid tier)
python kamino_liquidity_analysis/main.py --jupiter-api-key YOUR_KEY
```

### Python Library Usage

```python
from kamino_liquidity_analysis import generate_liquidity_report, summarize_report

# Run full analysis
df = generate_liquidity_report()

# Display summary pivot table
summary = summarize_report(df)
print(summary)

# Filter to high-impact scenarios
high_impact = df[df['price_impact_pct'] > 5.0]
print(f"Found {len(high_impact)} high-impact scenarios")

# Export to CSV
df.to_csv('liquidity_analysis.csv', index=False)
```

## Architecture

### Module Structure

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

### Data Flow

```
1. Kamino API → Fetch Reserves → Filter Volatile Assets
                     ↓
2. For Each Asset → Query Jupiter → Multiple Swap Sizes
                     ↓
3. Collect Results → Identify Risks → Generate Report
```

## Configuration

All configuration is in `kamino_liquidity_analysis/constants.py`:

- **Market**: Main Market pubkey
- **Assets**: SOL/BTC/ETH-based tokens to analyze
- **Swap Sizes**: Default test amounts ($1M, $5M, $10M, $20M, $50M, $100M)
- **Risk Thresholds**: Price impact, route concentration, TVL ratios

## Output Schema

The analysis generates a DataFrame with the following columns:

| Column | Description |
|--------|-------------|
| `asset_symbol` | Token symbol (e.g., "SOL", "MSOL") |
| `mint_address` | Token mint address |
| `current_price_usd` | Current token price |
| `current_tvl_usd` | Total deposits on Kamino |
| `swap_size_usd` | Hypothetical swap size |
| `swap_size_tokens` | Swap size in token terms |
| `price_impact_pct` | Price impact % |
| `output_usd` | Actual USD received after impact |
| `effective_price` | Actual price after impact |
| `slippage_bps` | Slippage in basis points |
| `router` | Jupiter router used |
| `route_summary` | Top DEXes used |
| `route_concentration` | % from largest pool |
| `quote_success` | Whether quote succeeded |
| `error_msg` | Error message if failed |
| `timestamp` | When analysis was run |
| `risk_flags` | List of risk flags |

## Risk Flags

The tool automatically identifies:

- **HIGH_IMPACT**: Price impact > 5%
- **CONCENTRATED_ROUTE**: >70% from single pool
- **LOW_TVL_RATIO**: TVL < 5x swap size
- **QUOTE_FAILED**: No route found

## API Rate Limits

- **Kamino API**: Generally permissive
- **Jupiter API (free)**: Limited requests per minute
  - Tool includes automatic rate limiting
  - Consider upgrading to paid tier for faster analysis
  - Use `--jupiter-api-key` flag for paid tier

## Examples

See `example_notebook.ipynb` for detailed usage examples including:

- Basic analysis workflow
- Filtering and visualization
- Risk assessment
- Custom scenarios

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=kamino_liquidity_analysis
```

## Limitations

**In Scope:**
- On-demand analysis (no historical tracking)
- Single market (Main Market only)
- Price impact analysis via Jupiter

**Out of Scope:**
- Historical data persistence
- Automated monitoring/alerting
- Multi-market analysis
- Actual transaction execution

## Future Enhancements

- Multi-asset liquidation scenarios (combined impact)
- Time-of-day liquidity variations
- Real vs theoretical TVL (accounting for utilization)
- Gas cost estimates
- Integration with monitoring dashboards

## Contributing

Contributions welcome! Please open an issue or pull request.

## License

MIT

## Acknowledgments

- Kamino Finance for providing the lending platform and API
- Jupiter Aggregator for swap routing and price impact data
