# Examples — OBQ Performance Reporting

| File | Description | Charts Rendered |
|------|-------------|-----------------|
| `01_minimal_usage.py` | Simplest possible integration — nav Series only | 14 charts (no benchmark, no VBT object) |
| `02_full_clenow2_example.py` | Complete FTT Clenow 2 P24 Universe integration | All 19 charts |

## Running the Examples

Both examples are designed to run inside a **Jupyter Notebook**. Plotly charts
require a live browser context to display. Run from the project root:

```bash
jupyter notebook
```

Then open an example file and run all cells, or copy the code into a new notebook cell.

## Adapting for Your Strategy

Start with `01_minimal_usage.py` and add parameters one at a time:
1. Add `benchmark=` — unlocks 6 more charts
2. Add `pf=` — unlocks VIZ 15 (sector attribution) and VIZ 16 (trade duration)
3. Add `contract_specs=` — adds sector labels to VIZ 15
4. Add `ohlc=` — converts VIZ 16 durations to calendar days
