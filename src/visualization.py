"""
GeoPulse: visualization.py
Generates Folium interactive geospatial hotspot maps and Plotly analytical charts
for retail mobility and foot-traffic insights.
"""

import os
import pandas as pd
import folium
from folium.plugins import HeatMap, MarkerCluster
import plotly.express as px
import plotly.graph_objects as go


def generate_folium_hotspot_map(
    clustered_path: str = "data/processed/clustered_mobility_pings.csv",
    stores_path: str = "data/raw/retail_stores.csv",
    output_map_path: str = "outputs/figures/interactive_retail_hotspots_map.html",
) -> str:
    """
    Creates an interactive Folium map visualizing store anchor locations,
    foot-traffic density heatmaps, and DBSCAN clusters.
    """
    df = pd.read_csv(clustered_path)
    stores = pd.read_csv(stores_path)

    # Center map around Bengaluru / Electronic City commercial hubs
    center_lat = stores["latitude"].mean()
    center_lon = stores["longitude"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="CartoDB positron")

    # 1. Add HeatMap layer for overall foot traffic density
    heat_data = df[["latitude", "longitude"]].dropna().values.tolist()
    HeatMap(heat_data, radius=15, blur=20, max_zoom=15, name="Foot Traffic Density").add_to(m)

    # 2. Add Retail Store Anchor Markers
    store_cluster = MarkerCluster(name="Retail Store Anchors").add_to(m)
    for _, row in stores.iterrows():
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=f"<b>{row['store_name']}</b><br>Category: {row['category']}<br>Zone: {row['zone']}<br>Area: {row['floor_area_sqft']} sq.ft",
            icon=folium.Icon(color="blue", icon="shopping-bag", prefix="fa"),
        ).add_to(store_cluster)

    # 3. Add Layer Control
    folium.LayerControl().add_to(m)

    os.makedirs(os.path.dirname(output_map_path), exist_ok=True)
    m.save(output_map_path)
    print(f"Interactive geospatial map saved -> {output_map_path}")
    return output_map_path


def generate_plotly_analytics_charts(
    enriched_path: str = "data/processed/enriched_mobility_pings.csv",
) -> dict:
    """
    Generates key analytical Plotly charts for hourly traffic curves,
    dwell time vs spend correlations, and category capture rates.
    """
    df = pd.read_csv(enriched_path)
    os.makedirs("outputs/figures", exist_ok=True)

    # Chart 1: Hourly Foot Traffic by Zone
    hourly_zone = df.groupby(["hour", "zone"]).size().reset_index(name="footfall_count")
    fig_hourly = px.line(
        hourly_zone,
        x="hour",
        y="footfall_count",
        color="zone",
        markers=True,
        title="Hourly Foot Traffic Trends Across Commercial Corridors",
        labels={"hour": "Hour of Day", "footfall_count": "Foot Traffic Volume", "zone": "Commercial Zone"},
    )
    fig_hourly.write_html("outputs/figures/hourly_traffic_trend.html")

    # Chart 2: Dwell Time vs Estimated Spend Scatter
    fig_spend = px.scatter(
        df.sample(min(1000, len(df))),
        x="dwell_time_mins",
        y="estimated_spend_inr",
        color="category",
        opacity=0.7,
        title="Consumer Dwell Time vs. Estimated Spend Correlation",
        labels={"dwell_time_mins": "Dwell Time (Minutes)", "estimated_spend_inr": "Estimated Spend (INR)", "category": "Retail Category"},
    )
    fig_spend.write_html("outputs/figures/dwell_vs_spend.html")

    print("Plotly analytical charts generated successfully in outputs/figures/")
    return {"hourly_trend": "outputs/figures/hourly_traffic_trend.html", "spend_correlation": "outputs/figures/dwell_vs_spend.html"}


if __name__ == "__main__":
    generate_folium_hotspot_map()
    generate_plotly_analytics_charts()