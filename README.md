# Coffee-Shop-Dashboard

Streamlit application that surfaces KPIs for a coffee shop using the curated dataset in `Data/coffee_sales.csv`.

## Data overview

- Columns, data types, and quirks are documented in [`Data/README.md`](Data/README.md).
- All data assets live under the `Data/` directory so that analysts can swap the sample CSV for a fresh drop when needed.

## Validating a new data drop

Run the lightweight checker anytime you replace `Data/coffee_sales.csv`:

```bash
python scripts/data_check.py  # optionally pass an alternate path
```

The script loads the CSV, confirms critical fields (`Date`, `Time`, `coffee_name`, `money`) are non-null, and prints summary statistics (row counts, numeric ranges, observed date span, and product/payment coverage).

## Refreshing the dataset

1. Place the new CSV into `Data/` and name it `coffee_sales.csv` (or pass the alternate path to `scripts/data_check.py`).
2. Execute `python scripts/data_check.py` to ensure the drop is healthy.
3. Update any downstream documentation or app logic if the schema changes before committing.

## Running the dashboard

```bash
streamlit run app.py
```

Make sure your Python environment includes the dependencies referenced by `app.py` (Streamlit, pandas, Plotly, etc.).
