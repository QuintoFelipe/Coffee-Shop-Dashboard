"""Coffee Shop performance dashboard built with Streamlit."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

from app_utils.data_processing import (
    build_product_mix,
    calculate_seasonality,
    calculate_seasonal_averages,
    compute_average_ticket,
    compute_margin,
    compute_total_revenue,
    compute_yoy_growth,
    prepare_features,
    profitability_view,
    rank_stores_by_revenue,
    regional_performance,
)
from theme import THEME

COFFEE_CONTINUOUS = ["#fce8d5", "#f2c8a2", "#da9b6c", "#b66a3d", "#6b2f17"]
COFFEE_HIGHLIGHTS = ["#8b4a2d", "#c0824f", "#f2c8a2", "#5c2b16"]
PLOT_BACKGROUND = "rgba(255, 250, 243, 0.95)"

DATA_PATH = Path("Data/coffee_sales.csv")


@st.cache_data(show_spinner=False)
def load_sales_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load and cache the sales dataset."""
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
    return df


def inject_theme() -> None:
    colors = THEME["colors"]
    fonts = THEME["fonts"]
    st.set_page_config(
        page_title="Coffee Shop Performance",
        page_icon="☕",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        f"""
        <style>
            .stApp {{
                background: radial-gradient(circle at top, rgba(255,255,255,0.65), transparent 45%),
                            linear-gradient(135deg, {colors['background']} 0%, #f1e3d5 100%);
                font-family: {fonts['base']};
                color: {colors['text']};
            }}
            .block-container {{
                padding-top: 2rem;
            }}
            .awesome-card {{
                background: {colors['surface']};
                border-radius: 18px;
                padding: 1.35rem 1.5rem;
                box-shadow: {THEME['shadows']['soft']};
                border: 1px solid rgba(138, 74, 45, 0.08);
                min-height: 150px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                gap: 0.35rem;
            }}
            .awesome-card h3 {{
                font-size: 2.35rem;
                font-family: {fonts['numeric']};
                margin: 0;
                color: {colors['accent']};
            }}
            .awesome-card span {{
                font-size: 0.85rem;
                color: {colors['muted']};
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }}
            .awesome-card p {{
                margin-top: 0.35rem;
                color: {colors['secondary']};
                font-weight: 600;
            }}
            .section-title {{
                font-size: 1.25rem;
                text-transform: uppercase;
                letter-spacing: 0.3em;
                color: {colors['muted']};
            }}
            [data-testid="stSidebar"] > div:first-child {{
                background: rgba(255, 255, 255, 0.9);
                border-right: 1px solid rgba(91, 53, 30, 0.15);
            }}
            [data-testid="stSidebar"] label {{
                color: {colors['text']};
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 0.8rem;
                font-weight: 600;
            }}
            .stSidebar .stMultiSelect div[data-baseweb="select"] > div {{
                background: rgba(245, 241, 234, 0.8);
                color: {colors['text']};
            }}
            .stSidebar .stDateInput input {{
                color: {colors['text']};
            }}
            .stSidebar input, .stSidebar select {{
                color: {colors['text']};
            }}
            .stSidebar .stSlider > div {{
                color: {colors['text']};
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_kpi(label: str, value: float, delta: float | None = None, prefix: str = "$", suffix: str = "") -> None:
    delta_html = ""
    if delta is not None:
        delta_html = f"<p>{delta:+.1f}% YoY</p>"
    st.markdown(
        f"""
        <div class="awesome-card">
            <span>{label}</span>
            <h3>{prefix}{value:,.0f}{suffix}</h3>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_filters(df: pd.DataFrame) -> Tuple[pd.Timestamp, pd.Timestamp, Iterable[str], Iterable[str]]:
    st.sidebar.header("Control Tower")
    min_date = df["sales_date"].min().date()
    max_date = df["sales_date"].max().date()
    date_range = st.sidebar.date_input(
        "Date range",
        (min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, date):
        start_date = end_date = date_range
    else:
        start_date, end_date = date_range
    categories = sorted(df["product_category"].dropna().unique().tolist())
    selected_categories = st.sidebar.multiselect(
        "Product category",
        options=categories,
        default=categories,
    )
    regions = sorted(df["region"].dropna().unique().tolist())
    selected_regions = st.sidebar.multiselect(
        "Location / Region",
        options=regions,
        default=regions,
    )
    st.sidebar.markdown("---")
    st.sidebar.metric("YoY Growth", f"{compute_yoy_growth(df):.1f}%")
    return pd.to_datetime(start_date), pd.to_datetime(end_date), selected_categories, selected_regions


def build_seasonality_section(filtered: pd.DataFrame) -> None:
    st.markdown("### Seasonality pulse")
    daily = calculate_seasonality(filtered)
    if daily.empty:
        st.info("No sales for the selected period.")
        return
    fig = px.line(
        daily,
        x="sales_date",
        y="revenue",
        markers=True,
        title="Revenue by day",
        color_discrete_sequence=[THEME["colors"]["primary"]],
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BACKGROUND,
        font_color=THEME["colors"]["text"],
        margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)


def build_product_mix_section(filtered: pd.DataFrame) -> None:
    st.markdown("### Product mix")
    mix = build_product_mix(filtered)
    if mix.empty:
        st.warning("No categories to display.")
        return
    fig = px.treemap(
        mix,
        path=["product_category", "coffee_name"],
        values="revenue",
        color="share",
        color_continuous_scale=COFFEE_CONTINUOUS,
        title="Category contribution",
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font_color=THEME["colors"]["text"],
    )
    st.plotly_chart(fig, use_container_width=True)


def build_regional_section(filtered: pd.DataFrame) -> None:
    st.markdown("### Regional performance")
    regional = regional_performance(filtered)
    if regional.empty:
        st.info("Add more filters to view regional insights.")
        return
    map_fig = px.scatter_geo(
        regional,
        lat="lat",
        lon="lon",
        size="revenue",
        color="region",
        hover_name="region",
        hover_data={"revenue": ":$,.0f", "orders": True},
        projection="natural earth",
        title="Store footprint",
        color_discrete_sequence=COFFEE_HIGHLIGHTS,
    )
    map_fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font_color=THEME["colors"]["text"],
    )
    bar_fig = px.bar(
        regional.sort_values("revenue", ascending=False),
        x="region",
        y="revenue",
        color="orders",
        color_continuous_scale=COFFEE_CONTINUOUS,
        title="Revenue and order volume",
        text_auto=".2s",
    )
    bar_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BACKGROUND,
        font_color=THEME["colors"]["text"],
        margin=dict(l=0, r=0, t=40, b=0),
    )
    col1, col2 = st.columns((2, 1))
    col1.plotly_chart(map_fig, use_container_width=True)
    col2.plotly_chart(bar_fig, use_container_width=True)


def build_profitability_section(filtered: pd.DataFrame) -> None:
    st.markdown("### Product profitability")
    profitability = profitability_view(filtered)
    if profitability.empty:
        st.info("Not enough data for profitability analysis.")
        return
    fig = px.scatter(
        profitability,
        x="avg_price",
        y="units",
        size="margin",
        color="margin_pct",
        hover_name="coffee_name",
        color_continuous_scale=COFFEE_CONTINUOUS,
        labels={"avg_price": "Average price", "units": "Units sold"},
        title="Price vs volume",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=PLOT_BACKGROUND,
        font_color=THEME["colors"]["text"],
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    inject_theme()
    raw_df = load_sales_data()
    df = prepare_features(raw_df)

    start, end, categories, regions = sidebar_filters(df)

    filtered = df[(df["sales_date"] >= start) & (df["sales_date"] <= end)]
    if categories:
        filtered = filtered[filtered["product_category"].isin(categories)]
    if regions:
        filtered = filtered[filtered["region"].isin(regions)]

    st.title("☕ Coffee Shop Revenue Intelligence")
    st.caption("High-frequency insights powered by the Coffee Sales dataset")

    total_sales = compute_total_revenue(filtered)
    avg_ticket = compute_average_ticket(filtered)
    margin = compute_margin(filtered)
    yoy = compute_yoy_growth(filtered)

    col1, col2, col3 = st.columns(3)
    with col1:
        render_kpi("Total sales", total_sales, yoy)
    with col2:
        render_kpi("Average ticket", avg_ticket, prefix="$", suffix=" avg")
    with col3:
        render_kpi("Gross margin", margin, prefix="$")

    build_seasonality_section(filtered)

    col_a, col_b = st.columns((1.2, 1))
    with col_a:
        build_product_mix_section(filtered)
    with col_b:
        seasonal = calculate_seasonal_averages(filtered)
        if seasonal.empty:
            st.info("Seasonal trend unavailable for this selection.")
        else:
            seasonal_fig = px.bar(
                seasonal,
                x="season",
                y="avg_revenue",
                color="avg_revenue",
                color_continuous_scale=COFFEE_CONTINUOUS,
                title="Seasonal averages",
            )
            seasonal_fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor=PLOT_BACKGROUND,
                font_color=THEME["colors"]["text"],
            )
            st.plotly_chart(seasonal_fig, use_container_width=True)

    build_regional_section(filtered)

    build_profitability_section(filtered)

    with st.expander("Store leaderboard"):
        ranking = rank_stores_by_revenue(filtered, top_n=10)
        st.dataframe(ranking, hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
