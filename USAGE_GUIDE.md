# Kamino Liquidity Analysis Tool - Usage Guide

Complete guide for using the Kamino Liquidity Analysis Tool.

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Run Your First Analysis

```bash
# Basic analysis (analyzes all volatile assets)
python kamino_liquidity_analysis/main.py

# Or if installed as package
kamino-analyze
```

## Command-Line Interface (CLI)

### Basic Commands

```bash
# Analyze all volatile assets with default swap sizes
python kamino_liquidity_analysis/main.py

# Save results to CSV
python kamino_liquidity_analysis/main.py --output results.csv

# Show summary pivot table
python kamino_liquidity_analysis/main.py --summary

# Quiet mode (errors only)
python kamino_liquidity_analysis/main.py --quiet

# Verbose mode (debug output)
python kamino_liquidity_analysis/main.py --verbose
```

### Filtering Assets

```bash
# Analyze specific assets
python kamino_liquidity_analysis/main.py --assets SOL,MSOL,JITOSOL

# Just SOL
python kamino_liquidity_analysis/main.py --assets SOL

# All BTC-based assets
python kamino_liquidity_analysis/main.py --assets WBTC,LBTC
```

### Custom Swap Sizes

```bash
# Test specific swap sizes (in USD)
python kamino_liquidity_analysis/main.py --swap-sizes 1000000,5000000,10000000

# Test smaller sizes for more granular data
python kamino_liquidity_analysis/main.py --swap-sizes 500000,1000000,2000000,3000000

# Test very large sizes
python kamino_liquidity_analysis/main.py --swap-sizes 50000000,100000000,200000000
```

### Using Jupiter API Key

```bash
# Use paid tier for better rate limits
python kamino_liquidity_analysis/main.py --jupiter-api-key YOUR_API_KEY

# Combine with other options
python kamino_liquidity_analysis/main.py \
  --jupiter-api-key YOUR_API_KEY \
  --output results.csv \
  --summary
```

### Complete Example

```bash
# Comprehensive analysis: SOL assets, custom sizes, save to CSV, show summary
python kamino_liquidity_analysis/main.py \
  --assets SOL,MSOL,JITOSOL,BSOL \
  --swap-sizes 1000000,5000000,10000000,25000000,50000000 \
  --output sol_liquidity_analysis.csv \
  --summary \
  --verbose
```

## Python API Usage

### Basic Usage

```python
from kamino_liquidity_analysis import generate_liquidity_report

# Run analysis
df = generate_liquidity_report()

# Display results
print(f"Analyzed {len(df)} scenarios")
print(df.head())
```

### Filter to Specific Assets

```python
from kamino_liquidity_analysis import generate_liquidity_report

# Analyze only SOL-based assets
df = generate_liquidity_report(
    asset_filter=['SOL', 'MSOL', 'JITOSOL']
)
```

### Custom Swap Sizes

```python
from kamino_liquidity_analysis import generate_liquidity_report

# Test custom swap sizes
custom_sizes = [
    500_000,      # $500K
    1_000_000,    # $1M
    2_500_000,    # $2.5M
    5_000_000,    # $5M
    10_000_000,   # $10M
]

df = generate_liquidity_report(
    swap_sizes_usd=custom_sizes
)
```

### Using Jupiter API Key

```python
from kamino_liquidity_analysis import generate_liquidity_report

# Use paid tier
df = generate_liquidity_report(
    jupiter_api_key='YOUR_API_KEY'
)
```

### Export Results

```python
from kamino_liquidity_analysis import generate_liquidity_report, export_report

df = generate_liquidity_report()

# Export to CSV
export_report(df, 'analysis.csv', include_failed=True)
```

### Generate Summary

```python
from kamino_liquidity_analysis import generate_liquidity_report, summarize_report

df = generate_liquidity_report()

# Create pivot table
summary = summarize_report(df)
print(summary)
```

## Advanced Usage

### Filter and Analyze Results

```python
import pandas as pd
from kamino_liquidity_analysis import generate_liquidity_report

df = generate_liquidity_report()

# Filter to successful quotes only
successful = df[df['quote_success']].copy()

# Find high-impact scenarios (>5%)
high_impact = successful[successful['price_impact_pct'] > 5.0]
print(f"High-impact scenarios: {len(high_impact)}")

# Find scenarios with risk flags
risky = df[df['risk_flags'].apply(lambda x: len(x) > 0)]
print(f"Risky scenarios: {len(risky)}")

# Group by asset
by_asset = successful.groupby('asset_symbol').agg({
    'price_impact_pct': ['mean', 'max'],
    'swap_size_usd': 'count'
})
print(by_asset)
```

### Visualize Results

```python
import matplotlib.pyplot as plt
from kamino_liquidity_analysis import generate_liquidity_report

df = generate_liquidity_report()
successful = df[df['quote_success']]

# Plot liquidity curves
for asset in successful['asset_symbol'].unique():
    asset_df = successful[successful['asset_symbol'] == asset]
    asset_df = asset_df.sort_values('swap_size_usd')

    plt.plot(
        asset_df['swap_size_usd'] / 1e6,  # Convert to millions
        asset_df['price_impact_pct'],
        marker='o',
        label=asset
    )

plt.xlabel('Swap Size ($M)')
plt.ylabel('Price Impact (%)')
plt.title('Liquidity Depth by Asset')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

### Compare Assets

```python
from kamino_liquidity_analysis import generate_liquidity_report

df = generate_liquidity_report()

# For $10M swaps, compare assets
ten_million = df[df['swap_size_usd'] == 10_000_000].copy()
ten_million = ten_million[ten_million['quote_success']]

# Sort by price impact
comparison = ten_million.sort_values('price_impact_pct')
print("\n$10M Swap Impact Comparison:")
print(comparison[['asset_symbol', 'price_impact_pct', 'output_usd', 'router']])
```

### Analyze Route Concentration

```python
from kamino_liquidity_analysis import generate_liquidity_report

df = generate_liquidity_report()

# Find scenarios with high route concentration
concentrated = df[df['route_concentration'] > 70].copy()
print(f"Highly concentrated routes: {len(concentrated)}")
print(concentrated[['asset_symbol', 'swap_size_usd', 'route_concentration', 'route_summary']])
```

## Using the Clients Directly

### Kamino Client

```python
from kamino_liquidity_analysis import KaminoClient

client = KaminoClient()

# Fetch all reserves
reserves = client.fetch_market_reserves()
print(f"Found {len(reserves)} reserves")

# Filter to volatile assets
volatile = client.filter_volatile_collateral(reserves)
print(f"Volatile assets: {len(volatile)}")

# Display reserve info
for reserve in volatile[:5]:
    print(f"{reserve['symbol']:10} - TVL: ${reserve['tvl_usd']:,.0f} - Price: ${reserve['usd_price']:.2f}")
```

### Jupiter Client

```python
from kamino_liquidity_analysis import JupiterClient
from kamino_liquidity_analysis.constants import USDC_MINT

client = JupiterClient()

# Query single swap
quote = client.query_swap_price_impact(
    input_mint='So11111111111111111111111111111111111111112',  # SOL
    output_mint=USDC_MINT,
    amount_in_native=1_000_000_000,  # 1 SOL (9 decimals)
)

print(f"Price impact: {quote['price_impact']:.2f}%")
print(f"Router: {quote['router']}")
print(f"Success: {quote['success']}")

# Analyze liquidity depth for an asset
results = client.analyze_liquidity_depth(
    input_mint='So11111111111111111111111111111111111111112',  # SOL
    token_decimals=9,
    token_price_usd=100.0,  # Hypothetical price
    swap_sizes_usd=[1_000_000, 5_000_000, 10_000_000]
)

for result in results:
    print(f"${result['swap_size_usd']/1e6:.0f}M: {result['price_impact_pct']:.2f}% impact")
```

## Interpreting Results

### Understanding Price Impact

```
Price Impact < 1%    = Excellent liquidity
Price Impact 1-3%    = Good liquidity
Price Impact 3-5%    = Moderate liquidity
Price Impact 5-10%   = Poor liquidity (risky)
Price Impact > 10%   = Very poor liquidity (high risk)
```

### Understanding Risk Flags

- **HIGH_IMPACT_X%**: Price impact exceeds threshold
- **CONCENTRATED_ROUTE_X%**: Most liquidity from single pool (fragile)
- **LOW_TVL_RATIO_Xx**: TVL is low relative to swap size (risky)
- **QUOTE_FAILED**: No route found (insufficient liquidity)

### Reading the Summary Table

```python
summary = summarize_report(df)
print(summary)
```

Output:
```
              $1.00M  $5.00M  $10.00M  $50.00M
asset_symbol
SOL             0.15    0.75     1.25     5.80
MSOL            0.25    1.10     2.00     8.50
WBTC            0.30    1.50     2.10     7.20
```

- Rows = Assets
- Columns = Swap sizes
- Values = Price impact %

## Troubleshooting

### No Data Generated

```bash
# Check with verbose mode
python kamino_liquidity_analysis/main.py --verbose

# Test with single asset
python kamino_liquidity_analysis/main.py --assets SOL
```

### Rate Limiting

```bash
# Use paid Jupiter tier
python kamino_liquidity_analysis/main.py --jupiter-api-key YOUR_KEY

# Or reduce number of tests
python kamino_liquidity_analysis/main.py --swap-sizes 1000000,10000000
```

### Import Errors

```bash
# Make sure you're in the right directory
cd /path/to/test-api

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

## Best Practices

1. **Start small**: Test with one asset first
2. **Use verbose mode**: When debugging issues
3. **Save to CSV**: For later analysis
4. **Check timestamps**: Results can become stale
5. **Monitor risk flags**: Pay attention to warnings
6. **Compare multiple runs**: Liquidity varies over time
7. **Use paid tier**: For production use

## Examples by Use Case

### Daily Risk Check

```bash
python kamino_liquidity_analysis/main.py \
  --output daily_check_$(date +%Y%m%d).csv \
  --summary
```

### Deep Dive on SOL

```bash
python kamino_liquidity_analysis/main.py \
  --assets SOL \
  --swap-sizes 1000000,2000000,3000000,5000000,7500000,10000000 \
  --output sol_deep_dive.csv \
  --verbose
```

### Quick Comparison

```bash
python kamino_liquidity_analysis/main.py \
  --assets SOL,MSOL,JITOSOL \
  --swap-sizes 5000000,10000000 \
  --summary
```

### Production Monitoring

```python
from kamino_liquidity_analysis import generate_liquidity_report
import datetime

# Run analysis
df = generate_liquidity_report(jupiter_api_key='YOUR_KEY')

# Check for high-risk scenarios
high_risk = df[df['risk_flags'].apply(lambda x: len(x) > 0)]

if len(high_risk) > 0:
    # Alert or log
    print(f"WARNING: {len(high_risk)} high-risk scenarios detected")
    high_risk.to_csv(f'risk_alert_{datetime.datetime.now():%Y%m%d_%H%M}.csv')
```

## Additional Resources

- See `example_notebook.ipynb` for interactive examples
- See `DESIGN.md` for technical details
- See `README.md` for overview
- See `test_basic.py` for simple test example

---

For issues or questions, please check the documentation or open an issue on GitHub.
