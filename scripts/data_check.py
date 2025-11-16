#!/usr/bin/env python3
"""Basic data quality checks for the coffee sales dataset."""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List

CRITICAL_COLUMNS = ["Date", "Time", "coffee_name", "money"]
NUMERIC_COLUMNS = ["money", "hour_of_day", "Weekdaysort", "Monthsort"]


def load_rows(csv_path: Path) -> List[Dict[str, str]]:
    """Load the CSV into a list of dictionaries."""
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def validate_required_fields(rows: Iterable[Dict[str, str]]) -> None:
    """Raise a ValueError if any required column contains null / blank values."""
    failures: Dict[str, int] = defaultdict(int)
    for row in rows:
        for column in CRITICAL_COLUMNS:
            value = row.get(column, "")
            if value is None or not str(value).strip():
                failures[column] += 1
    if failures:
        breakdown = ", ".join(f"{col}: {count}" for col, count in failures.items())
        raise ValueError(f"Missing values detected -> {breakdown}")


def summarize(rows: List[Dict[str, str]]) -> None:
    """Print row counts, numeric summaries, and calendar coverage."""
    total_rows = len(rows)
    print(f"✅ Loaded {total_rows:,} rows")

    numeric_summary = {}
    for column in NUMERIC_COLUMNS:
        values: List[float] = []
        for row in rows:
            raw = row.get(column, "")
            if raw is None or not str(raw).strip():
                continue
            try:
                values.append(float(raw))
            except ValueError:
                continue
        if values:
            numeric_summary[column] = {
                "min": min(values),
                "max": max(values),
                "mean": mean(values),
            }
    if numeric_summary:
        print("\nNumeric columns:")
        for column, stats in numeric_summary.items():
            print(
                f" • {column}: min={stats['min']:.2f} max={stats['max']:.2f} "
                f"mean={stats['mean']:.2f}"
            )

    dates: List[datetime] = []
    for row in rows:
        raw_date = row.get("Date")
        if not raw_date:
            continue
        try:
            dates.append(datetime.fromisoformat(raw_date))
        except ValueError:
            continue
    dates.sort()
    if dates:
        print(
            f"\nCalendar coverage: {dates[0].date()} → {dates[-1].date()} "
            f"({(dates[-1] - dates[0]).days} days)"
        )

    products = {row.get("coffee_name") for row in rows if row.get("coffee_name")}
    payment_methods = {row.get("cash_type") for row in rows if row.get("cash_type")}
    print(
        f"Products tracked: {len(products)} | Payment methods observed: "
        f"{', '.join(sorted(payment_methods)) or 'n/a'}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=Path("Data/coffee_sales.csv"),
        type=Path,
        help="Path to the coffee sales CSV (defaults to Data/coffee_sales.csv)",
    )
    args = parser.parse_args()
    rows = load_rows(args.csv_path)
    validate_required_fields(rows)
    summarize(rows)


if __name__ == "__main__":
    main()
