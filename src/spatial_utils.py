"""
GeoPulse: spatial_utils.py
Geospatial transformations, Haversine distance calculations, and retail catchment metrics.
"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


def to_geodataframe(df: pd.DataFrame, lat_col: str = "latitude", lon_col: str = "longitude") -> gpd.GeoDataFrame:
    """
    Converts a standard Pandas DataFrame with lat/lon columns into a GeoPandas GeoDataFrame (EPSG:4326).
    """
    geometry = [Point(xy) for xy in zip(df[lon_col], df[lat_col])]
    gdf = gpd.GeoDataFrame(df.copy(), geometry=geometry, crs="EPSG:4326")
    return gdf


def haversine_distance_m(lat1, lon1, lat2, lon2) -> np.ndarray:
    """
    Calculates the great-circle distance in meters between two points on Earth using vectorized numpy.
    """
    r = 6371000.0  # Earth radius in meters
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return (r * c).round(2)


def enrich_spatial_metrics(
    mobility_path: str = "data/processed/cleaned_mobility_pings.csv",
    stores_path: str = "data/raw/retail_stores.csv",
    output_pings_path: str = "data/processed/enriched_mobility_pings.csv",
    output_store_kpis_path: str = "data/processed/store_performance_kpis.csv",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Merges cleaned mobility pings with store coordinates, computes distance to nearest store,
    classifies catchment rings, and aggregates store-level retail KPIs.
    """
    pings = pd.read_csv(mobility_path)
    stores = pd.read_csv(stores_path)

    # Merge store coordinates & details
    merged = pings.merge(
        stores[["store_id", "store_name", "category", "latitude", "longitude", "floor_area_sqft"]],
        left_on="nearest_store_id",
        right_on="store_id",
        suffixes=("_ping", "_store"),
    )

    # Calculate exact distance in meters from ping to store
    merged["distance_to_store_m"] = haversine_distance_m(
        merged["latitude_ping"],
        merged["longitude_ping"],
        merged["latitude_store"],
        merged["longitude_store"],
    )

    # Rename ping coordinates back to standard names
    merged = merged.rename(columns={"latitude_ping": "latitude", "longitude_ping": "longitude"})

    # Define retail catchment tier
    merged["catchment_ring"] = pd.cut(
        merged["distance_to_store_m"],
        bins=[-1, 100, 300, 600, 10000],
        labels=["Immediate (<100m)", "Primary (100-300m)", "Secondary (300-600m)", "Outlier (>600m)"],
    )

    # Flag high-intent visits (within 150m and dwell time >= 10 mins)
    merged["is_store_visit"] = (merged["distance_to_store_m"] <= 150) & (merged["dwell_time_mins"] >= 10)

    # Compute Store-Level Performance KPIs
    store_kpis = (
        merged.groupby(["store_id", "store_name", "category", "zone", "latitude_store", "longitude_store", "floor_area_sqft"])
        .agg(
            total_footfall=("ping_id", "count"),
            unique_visitors=("device_id", "nunique"),
            verified_store_visits=("is_store_visit", "sum"),
            avg_dwell_time_mins=("dwell_time_mins", "mean"),
            avg_distance_m=("distance_to_store_m", "mean"),
            total_estimated_revenue_inr=("estimated_spend_inr", "sum"),
            avg_spend_inr=("estimated_spend_inr", "mean"),
        )
        .reset_index()
    )

    store_kpis["capture_rate_pct"] = ((store_kpis["verified_store_visits"] / store_kpis["total_footfall"]) * 100).round(2)
    store_kpis["footfall_per_1000_sqft"] = ((store_kpis["total_footfall"] / store_kpis["floor_area_sqft"]) * 1000).round(2)
    store_kpis["avg_dwell_time_mins"] = store_kpis["avg_dwell_time_mins"].round(2)
    store_kpis["avg_distance_m"] = store_kpis["avg_distance_m"].round(2)
    store_kpis["total_estimated_revenue_inr"] = store_kpis["total_estimated_revenue_inr"].round(2)
    store_kpis["avg_spend_inr"] = store_kpis["avg_spend_inr"].round(2)

    os.makedirs(os.path.dirname(output_pings_path), exist_ok=True)
    merged.to_csv(output_pings_path, index=False)
    store_kpis.to_csv(output_store_kpis_path, index=False)

    print(f"Enriched {len(merged)} mobility records -> {output_pings_path}")
    print(f"Generated KPI summary for {len(store_kpis)} stores -> {output_store_kpis_path}")
    return merged, store_kpis


if __name__ == "__main__":
    enrich_spatial_metrics()