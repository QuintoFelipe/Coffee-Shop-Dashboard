"""Data preparation helpers for the Streamlit dashboard."""
from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd

# --- Reference metadata ----------------------------------------------------
PRODUCT_CATEGORY_MAP: Dict[str, str] = {
    "Latte": "Espresso Classics",
    "Cappuccino": "Espresso Classics",
    "Americano": "Espresso Classics",
    "Espresso": "Espresso Classics",
    "Flat White": "Espresso Classics",
    "Cold Brew": "Cold Classics",
    "Iced Coffee": "Cold Classics",
    "Frappuccino": "Cold Classics",
    "Hot Chocolate": "Non Coffee",
    "Matcha Latte": "Non Coffee",
    "Tea": "Non Coffee",
}

STORE_NAME_MAP: Dict[str, str] = {
    "Mon": "Market Street Roastery",
    "Tue": "Waterfront Kiosk",
    "Wed": "Arts District Cart",
    "Thu": "Lakeside Drive Thru",
    "Fri": "Tech Park Flagship",
    "Sat": "Suburban Express",
    "Sun": "Weekend Farmers Market",
}

STORE_REGION_MAP: Dict[str, str] = {
    "Market Street Roastery": "West Coast",
    "Waterfront Kiosk": "Pacific Northwest",
    "Arts District Cart": "Mountain",
    "Lakeside Drive Thru": "Midwest",
    "Tech Park Flagship": "Northeast",
    "Suburban Express": "South",
    "Weekend Farmers Market": "Southwest",
}

REGION_COORDINATES: Dict[str, Tuple[float, float]] = {
    "West Coast": (37.7749, -122.4194),
    "Pacific Northwest": (47.6062, -122.3321),
    "Mountain": (39.7392, -104.9903),
    "Midwest": (41.8781, -87.6298),
    "Northeast": (40.7128, -74.0060),
    "South": (29.7604, -95.3698),
    "Southwest": (33.4484, -112.0740),
}

MARGIN_MAP: Dict[str, float] = {
    "Espresso Classics": 0.72,
    "Cold Classics": 0.68,
    "Non Coffee": 0.58,
}

SEASON_MAP = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Autumn", 10: "Autumn", 11: "Autumn",
}


def _safe_category(value: str) -> str:
    """Return a friendly category label for each product."""
    return PRODUCT_CATEGORY_MAP.get(value, "Seasonal Specials")


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add engineered fields used across the dashboard."""
    enriched = df.copy()
    enriched["sales_date"] = pd.to_datetime(enriched["Date"], errors="coerce")
    enriched["sales_year"] = enriched["sales_date"].dt.year
    enriched["sales_month"] = enriched["sales_date"].dt.month
    enriched["sales_month_name"] = enriched["sales_date"].dt.strftime("%b")
    enriched["season"] = enriched["sales_month"].map(SEASON_MAP)
    enriched["product_category"] = enriched["coffee_name"].map(_safe_category)
    enriched["store_name"] = enriched["Weekday"].map(STORE_NAME_MAP).fillna("Pop-up Store")
    enriched["region"] = enriched["store_name"].map(STORE_REGION_MAP).fillna("Pop-up Region")
    enriched["units"] = 1
    enriched["margin_pct"] = enriched["product_category"].map(MARGIN_MAP).fillna(0.6)
    enriched["margin_value"] = enriched["money"].astype(float) * enriched["margin_pct"]
    return enriched


def compute_total_revenue(df: pd.DataFrame) -> float:
    return float(df["money"].sum())


def compute_average_ticket(df: pd.DataFrame) -> float:
    return float(df["money"].mean()) if not df.empty else 0.0


def compute_margin(df: pd.DataFrame) -> float:
    return float(df["margin_value"].sum())


def compute_yoy_growth(df: pd.DataFrame) -> float:
    yearly = df.groupby("sales_year")["money"].sum().sort_index()
    if len(yearly) < 2:
        return 0.0
    last, previous = yearly.iloc[-1], yearly.iloc[-2]
    if previous == 0:
        return 0.0
    return float(((last - previous) / previous) * 100)


def calculate_seasonality(df: pd.DataFrame) -> pd.DataFrame:
    """Return revenue aggregated by day for the seasonality line chart."""
    daily = df.groupby("sales_date", as_index=False)["money"].sum()
    return daily.rename(columns={"money": "revenue"})


def calculate_seasonal_averages(df: pd.DataFrame) -> pd.DataFrame:
    seasonal = df.groupby("season", as_index=False)["money"].mean()
    return seasonal.rename(columns={"money": "avg_revenue"})


def rank_stores_by_revenue(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    ranking = (
        df.groupby(["store_name", "region"], as_index=False)["money"].sum()
        .rename(columns={"money": "revenue"})
        .sort_values("revenue", ascending=False)
    )
    return ranking.head(top_n)


def build_product_mix(df: pd.DataFrame) -> pd.DataFrame:
    mix = (
        df.groupby(["product_category", "coffee_name"], as_index=False)["money"].sum()
        .rename(columns={"money": "revenue"})
    )
    mix["share"] = mix["revenue"] / mix["revenue"].sum()
    return mix


def regional_performance(df: pd.DataFrame) -> pd.DataFrame:
    regional = (
        df.groupby("region", as_index=False)
        .agg(revenue=("money", "sum"), orders=("units", "sum"))
    )
    regional["lat"] = regional["region"].map(lambda r: REGION_COORDINATES.get(r, (0.0, 0.0))[0])
    regional["lon"] = regional["region"].map(lambda r: REGION_COORDINATES.get(r, (0.0, 0.0))[1])
    return regional


def profitability_view(df: pd.DataFrame) -> pd.DataFrame:
    """Return aggregated profitability metrics for scatter plotting."""
    grouped = (
        df.groupby("coffee_name", as_index=False)
        .agg(revenue=("money", "sum"), units=("units", "sum"), margin=("margin_value", "sum"))
    )
    grouped["avg_price"] = grouped["revenue"] / grouped["units"].replace(0, pd.NA)
    grouped["margin_pct"] = grouped["margin"] / grouped["revenue"].replace(0, pd.NA)
    grouped = grouped.fillna(0)
    return grouped
