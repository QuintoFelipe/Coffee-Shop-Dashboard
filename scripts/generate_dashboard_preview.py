"""Generate a lightweight SVG preview of the dashboard layout."""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

DATA_PATH = Path('Data/coffee_sales.csv')
ASSET_PATH = Path('assets/dashboard-preview.svg')

PRODUCT_CATEGORY_MAP = {
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

STORE_NAME_MAP = {
    "Mon": "Market Street Roastery",
    "Tue": "Waterfront Kiosk",
    "Wed": "Arts District Cart",
    "Thu": "Lakeside Drive Thru",
    "Fri": "Tech Park Flagship",
    "Sat": "Suburban Express",
    "Sun": "Weekend Farmers Market",
}


def currency(value: float) -> str:
    return f"${value:,.0f}"


def load_data() -> list[dict[str, str]]:
    with DATA_PATH.open() as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def aggregate(rows: list[dict[str, str]]):
    total_revenue = 0.0
    orders = 0
    date_revenue: dict[str, float] = defaultdict(float)
    store_revenue: dict[str, float] = defaultdict(float)
    category_revenue: dict[str, float] = defaultdict(float)
    year_revenue: dict[int, float] = defaultdict(float)

    for row in rows:
        amount = float(row.get('money', 0) or 0)
        total_revenue += amount
        orders += 1
        date_revenue[row['Date']] += amount
        store = STORE_NAME_MAP.get(row.get('Weekday'), 'Pop-up Store')
        store_revenue[store] += amount
        category = PRODUCT_CATEGORY_MAP.get(row.get('coffee_name'), 'Seasonal Specials')
        category_revenue[category] += amount
        try:
            year = datetime.fromisoformat(row['Date']).year
        except ValueError:
            continue
        year_revenue[year] += amount

    avg_ticket = total_revenue / orders if orders else 0
    years = sorted(year_revenue)
    yoy = 0.0
    if len(years) >= 2:
        last, prev = years[-1], years[-2]
        prev_value = year_revenue[prev]
        if prev_value:
            yoy = ((year_revenue[last] - prev_value) / prev_value) * 100

    return {
        'total_revenue': total_revenue,
        'orders': orders,
        'avg_ticket': avg_ticket,
        'yoy': yoy,
        'date_revenue': date_revenue,
        'store_revenue': store_revenue,
        'category_revenue': category_revenue,
    }


def scale_points(date_revenue: dict[str, float]):
    points = []
    parsed = []
    for date_str, value in date_revenue.items():
        try:
            parsed.append((datetime.fromisoformat(date_str), value))
        except ValueError:
            continue
    if not parsed:
        return points
    parsed.sort(key=lambda x: x[0])
    min_date = parsed[0][0]
    max_date = parsed[-1][0]
    min_value = 0
    max_value = max(v for _, v in parsed) or 1
    total_days = max((max_date - min_date).days, 1)

    width = 520
    height = 180
    for dt, value in parsed:
        days = (dt - min_date).days
        x = 60 + (days / total_days) * width
        y = 320 - (value - min_value) / (max_value - min_value) * height
        points.append((x, y))
    return points


def build_svg(metrics: dict) -> str:
    width, height = 1200, 720
    points = scale_points(metrics['date_revenue'])
    top_stores = Counter(metrics['store_revenue']).most_common(5)
    top_categories = Counter(metrics['category_revenue']).most_common(4)

    svg_parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>",
        "<defs>",
        "<linearGradient id='bgGrad' x1='0%' y1='0%' x2='100%' y2='100%'>",
        "<stop offset='0%' stop-color='#0f172a' />",
        "<stop offset='100%' stop-color='#1e293b' />",
        "</linearGradient>",
        "</defs>",
        "<rect width='100%' height='100%' fill='url(#bgGrad)' rx='32' />",
        "<text x='60' y='70' fill='#f8fafc' font-size='32' font-family='Inter, sans-serif'>Coffee Shop Performance Dashboard</text>",
        "<text x='60' y='105' fill='#94a3b8' font-size='18'>Sample view rendered from the March 2024 drop</text>",
    ]

    # KPI cards
    kpi_templates = [
        ("Total revenue", currency(metrics['total_revenue']), f"YoY {metrics['yoy']:+.1f}%"),
        ("Average ticket", f"{currency(metrics['avg_ticket'])}", "per order"),
        ("Total orders", f"{metrics['orders']:,}", "transactions"),
    ]
    for idx, (label, value, caption) in enumerate(kpi_templates):
        x = 60 + idx * 360
        svg_parts.append(
            f"<g transform='translate({x},140)'>"
            "<rect width='320' height='130' rx='24' fill='rgba(15,23,42,0.8)' stroke='rgba(148,163,184,0.3)' />"
            f"<text x='24' y='48' fill='#94a3b8' font-size='16'>{label}</text>"
            f"<text x='24' y='92' fill='#f8fafc' font-size='36' font-weight='600'>{value}</text>"
            f"<text x='24' y='118' fill='#38bdf8' font-size='14'>{caption}</text>"
            "</g>"
        )

    # Seasonality line chart frame
    svg_parts.extend([
        "<g transform='translate(40,310)'>",
        "<rect width='560' height='260' rx='24' fill='rgba(15,23,42,0.8)' stroke='rgba(148,163,184,0.2)' />",
        "<text x='24' y='46' fill='#f8fafc' font-size='20'>Seasonality pulse</text>",
        "<polyline fill='none' stroke='#f97316' stroke-width='3' points='" + " ".join(f"{x-40},{y-230}" for x, y in points) + "' />" if points else "",
        "</g>",
    ])

    # Store performance bars
    bar_group = ["<g transform='translate(640,310)'>",
                 "<rect width='520' height='260' rx='24' fill='rgba(15,23,42,0.8)' stroke='rgba(148,163,184,0.2)' />",
                 "<text x='24' y='46' fill='#f8fafc' font-size='20'>Store leaderboard</text>"]
    if top_stores:
        max_value = top_stores[0][1]
        for idx, (store, value) in enumerate(top_stores):
            bar_y = 80 + idx * 36
            bar_width = (value / max_value) * 420 if max_value else 0
            bar_group.append(
                f"<text x='24' y='{bar_y}' fill='#94a3b8' font-size='14'>{store}</text>"
                f"<rect x='220' y='{bar_y-14}' width='{bar_width}' height='18' fill='#34d399' rx='9' />"
                f"<text x='{220 + bar_width + 10}' y='{bar_y}' fill='#f8fafc' font-size='14'>{currency(value)}</text>"
            )
    bar_group.append("</g>")
    svg_parts.extend(bar_group)

    # Product mix chips
    mix_group = ["<g transform='translate(40,600)'>",
                 "<rect width='1120' height='90' rx='24' fill='rgba(15,23,42,0.8)' stroke='rgba(148,163,184,0.2)' />",
                 "<text x='24' y='46' fill='#f8fafc' font-size='20'>Product mix</text>"]
    total = sum(value for _, value in top_categories) or 1
    for idx, (category, value) in enumerate(top_categories):
        share = value / total * 100
        mix_group.append(
            f"<g transform='translate({260 + idx * 200},20)'>"
            f"<rect width='180' height='50' rx='16' fill='rgba(56,189,248,0.15)' stroke='rgba(56,189,248,0.4)' />"
            f"<text x='16' y='35' fill='#f8fafc' font-size='16'>{category}: {share:.1f}%</text>"
            "</g>"
        )
    mix_group.append("</g>")
    svg_parts.extend(mix_group)

    svg_parts.append("</svg>")
    return "".join(svg_parts)


def main() -> None:
    rows = load_data()
    metrics = aggregate(rows)
    svg = build_svg(metrics)
    ASSET_PATH.write_text(svg, encoding='utf-8')
    print(f"Wrote {ASSET_PATH}")


if __name__ == '__main__':
    main()
