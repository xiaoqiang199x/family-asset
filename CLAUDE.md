# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

家庭资产管理系统 — 个人/家庭资产管理的 Web 应用，支持管理银行理财、股票、基金、黄金四类资产。采用前后端分离的单体架构，数据存储使用 CSV 文件，通过 pandas 进行数据操作。

## Tech Stack

- Backend: Python + FastAPI + uvicorn
- Data: pandas DataFrame + CSV files (two files: `products.csv`, `operations.csv`)
- Frontend: Jinja2 template + vanilla JavaScript + Chart.js (CDN)

## Development Environment

This project uses a conda virtual environment named `family-asset`.

```bash
# Install dependencies
conda run -n family-asset pip install -r requirements.txt

# Run the server
conda run -n family-asset python main.py
```

The server listens on port 8002 (configured in `main.py`).

## Architecture

### Data Layer (`app/storage.py`)

`AssetStore` is the core data layer managing two CSV files under `app/data/`:

- `products.csv` — Product snapshot table. One row = one product's current state. Columns: `id`, `asset_type`, `name`, `amount`, `cost`, `value`, `date`, `category`, `note`.
- `operations.csv` — Operation history table. One row = one operation. Columns: `id`, `product_id`, `product_name`, `asset_type`, `operation_type`, `change_amount`, `price`, `new_amount`, `new_cost`, `new_value`, `date`, `note`.

**No caching strategy:** `_load()` and `_load_ops()` read from disk every time. `add_operation()` sets `self._ops_df = None` to force refresh.

**Key design principles:**
- `cost` = average cost per share. `value` = latest market value per share.
- `total_value = amount * value`
- `profit = (value - cost) * amount`
- `profit_pct = (value - cost) / cost * 100`

### Business Logic

**Buy:** `new_amount = cur_amount + buy_amount`; `new_cost = (cur_amount * cur_cost + buy_amount * new_value) / new_amount`. Cost is updated via weighted average.

**Sell:** `new_amount = cur_amount - sell_amount`; `new_cost` unchanged; `new_value = sell_price`.

**Update value:** Only `value` changes; `amount` and `cost` remain the same.

**Soft delete:** Rename product to `{original_name}_{YYYYMMDD}_删除`. The `delete_record()` method also renames all matching `product_name` entries in `operations.csv`. Frontend and summary calculations filter out names ending with `_删除`.

### API Layer (`app/api.py`)

All routes use `APIRouter` and are included in `main.py`. Form endpoints accept `python-multipart` data.

**Important:** The project uses a newer version of Starlette/FastAPI where `TemplateResponse` signature is `TemplateResponse(request, name, context)` — not the old `TemplateResponse(name, {"request": request})`. See `index()` route.

### Frontend (`app/templates/index.html`)

Single-page application style. HTML is loaded once; data is fetched via `/api/*` endpoints.

Key frontend functions: `loadSummary()`, `loadProducts()`, `showHistory(name)`, `buyProduct()`, `sellProduct()`, `updateValue()`, `editProduct()`, `delByName()`, `openActionModal()`, `addRecord()`.

Operation menu uses `position: fixed` with coordinates from `getBoundingClientRect()` to avoid overflow clipping.

History chart is a dual-Y-axis line chart: left Y = total value (blue gradient), right Y = profit_pct (gray line, green/red square points).

## Data Files

CSV files are auto-created on first startup under `app/data/`. They use `utf-8-sig` encoding for Excel compatibility.
