# back_test_forBTC

A Python backtesting engine that tests a liquidity-sweep (SMC) trading strategy against historical Bitcoin (BTC/USDT) price data, using EMA/SMA filters and a risk-based position sizing model to evaluate performance.

## About

This project downloads historical BTC/USDT 1-hour candle data directly from Binance's public data archive, then runs a backtest of a custom trading strategy over that data. The strategy looks for **liquidity sweeps** (price briefly breaking a recent high/low and reversing) filtered by EMA-200 and SMA-50 trend context, and simulates long/short trades with:

- Percentage-based risk per trade
- Stop-loss / take-profit levels (2:1 reward-to-risk)
- Leverage cap
- Trading fees
- Drawdown, win rate, and profit factor statistics

Results are written to `summary.txt` and also printed to the console.

## Project structure

| File | Description |
|---|---|
| `abc.sh` | Downloads and merges historical BTC/USDT 1h kline data from Binance's public data archive |
| `main.py` | Loads the CSV data, calculates indicators, runs the backtest engine, and generates the report |
| `btc_1h_data/` | Folder where downloaded/merged CSV data is stored |
| `summary.txt` | Generated backtest report (created after running `main.py`) |
| `Makefile` | Convenience build/run rules |
| `.gitignore` | Git ignore rules |

## Requirements

- Python 3.9+
- `wget` and `unzip` installed on your system (used by `abc.sh` to fetch and extract data)
- Internet access to `data.binance.vision`

## Setup (step by step)

### 1. Clone the repository

```bash
git clone https://github.com/bckblt/back_test_forBTC.git
cd back_test_forBTC
```

### 2. Create a virtual environment

It's strongly recommended to isolate the project's dependencies in a Python virtual environment (`venv`) instead of installing packages globally.

```bash
# Create the virtual environment (creates a "venv" folder)
python3 -m venv venv
```

### 3. Activate the virtual environment

**macOS / Linux:**

```bash
source venv/bin/activate
```

**Windows (PowerShell):**

```powershell
venv\Scripts\Activate.ps1
```

**Windows (cmd.exe):**

```cmd
venv\Scripts\activate.bat
```

Once activated, your terminal prompt should be prefixed with `(venv)`.

### 4. Upgrade pip (recommended)

```bash
pip install --upgrade pip
```

### 5. Install the required packages

```bash
pip install pandas numpy
```

Alternatively, if a `requirements.txt` is present:

```bash
pip install -r requirements.txt
```

### 6. Fetch the historical BTC data

`abc.sh` downloads monthly BTC/USDT 1h kline data from Binance's public archive and merges it into a single CSV under `btc_1h_data/`.

```bash
chmod +x abc.sh   # only needed once, if not already executable
./abc.sh
```

This will create:

```
btc_1h_data/BTCUSDT-1h-all.csv
```

> **Note:** `main.py` expects the data file at `./btc_1h_data/btc.csv`. After running `abc.sh`, rename or copy the merged file accordingly:
>
> ```bash
> cp btc_1h_data/BTCUSDT-1h-all.csv btc_1h_data/btc.csv
> ```

### 7. Run the backtest

```bash
python3 main.py
```

This will print the results to the console and also write a detailed report to `summary.txt`.

### 8. Deactivate the virtual environment (when done)

```bash
deactivate
```

## Configuration

You can adjust the date range and symbol pulled from Binance by editing the variables at the top of `abc.sh`:

```bash
SYMBOL="BTCUSDT"
INTERVAL="1h"
YEARS=("2024" "2025")
```

Strategy parameters (risk percentage, leverage, fees, stop-loss distance, etc.) can be adjusted inside `motoru_calistir()` in `main.py`.

## Resources

While building this project, the following resource was especially helpful:

- **[Binance Public Data Repository](https://data.binance.vision/)** — source of the historical kline (candlestick) data used for backtesting.

## Author

[bckblt](https://github.com/bckblt)
