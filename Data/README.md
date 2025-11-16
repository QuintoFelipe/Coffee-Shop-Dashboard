# Coffee sales dataset

- **File name:** `coffee_sales.csv`
- **Location:** `Data/`
- **Row count:** 3,547 transactions (2024-03-01 through 2025-03-23).
- **Encoding:** UTF-8, comma-delimited CSV.

| Column | Type | Units / Format | Description & notes |
| --- | --- | --- | --- |
| `hour_of_day` | Integer | Hour of day (0-23) | Extracted from the event timestamp. Useful for intraday analysis. |
| `cash_type` | Categorical string | Text (`card`, `cash`, etc.) | Payment method. Current sample only includes `card`, so downstream logic should not assume multiple values are present. |
| `money` | Decimal number | Currency (USD) | Net ticket value for each order. Amounts range from 18.12 to 38.70 in the provided sample. |
| `coffee_name` | Categorical string | N/A | Beverage or product sold (8 unique values in the sample). |
| `Time_of_Day` | Categorical string | Morning / Afternoon / Night | Bucket that mirrors `hour_of_day` for higher-level reporting. |
| `Weekday` | Categorical string | Mon, Tue, ... | Abbreviated weekday of the sale. |
| `Month_name` | Categorical string | Jan, Feb, ... | Abbreviated month of the sale. |
| `Weekdaysort` | Integer | 1 (Monday) – 7 (Sunday) | Numeric helper for sorting weekdays chronologically. |
| `Monthsort` | Integer | 1 (January) – 12 (December) | Numeric helper for sorting months chronologically. |
| `Date` | Date string | ISO 8601 (`YYYY-MM-DD`) | Calendar day of the transaction. Presently covers 2024-03-01 to 2025-03-23. |
| `Time` | Time string | `HH:MM:SS.ssssss` | Time-of-day including microseconds. Combine with `Date` for precise timestamps. |

## Known quirks

- All records in the curated sample were paid via card; expect additional payment methods when replacing the dataset.
- The `money` column reflects the total ticket amount rather than per-item price; repeated values are expected because of fixed menu pricing.
- Timestamps already arrive in ISO 8601 strings, so avoid locale-dependent parsing.

## Replacing the dataset

1. Drop the new CSV into `Data/` as `coffee_sales.csv` (keep UTF-8 encoding and headers intact).
2. Run `python scripts/data_check.py` to validate nulls, numeric ranges, and date coverage before pushing changes.
3. Commit both the refreshed CSV (if appropriate for sharing) and any documentation updates describing the new drop.

See `scripts/data_check.py` for the automated validation steps used by the project.
