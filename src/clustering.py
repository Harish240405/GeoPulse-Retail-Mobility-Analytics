"""
GeoPulse: clustering.py
Spatial density clustering using DBSCAN with Haversine distance to identify
hyper-local retail mobility hotspots and evaluate model performance.
"""

import os
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score


def run_spatial_clustering(
    input_path: str = "data/processed/enriched_mobility_pings.csv",
    clustered_pings_path: str = "data/processed/clustered_mobility_pings.csv",
    hotspots_summary_path: str = "data/processed/hotspot_clusters_summary.csv",
    eps_meters: float = 180.0,
    min_samples: int = 25,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Applies DBSCAN clustering using great-circle Haversine distance on GPS pings
    to identify dense retail foot-traffic hotspots.
    """
    df = pd.read_csv(input_path)

    # Convert latitude and longitude to radians for Haversine metric
    coords_rad = np.radians(df[["latitude", "longitude"]].values)

    # Convert eps from meters to radians (Earth radius ~ 6,371,000 meters)
    earth_radius_m = 6371000.0
    eps_rad = eps_meters / earth_radius_m

    # Fit DBSCAN
    db = DBSCAN(eps=eps_rad, min_samples=min_samples, metric="haversine", algorithm="ball_tree")
    df["cluster_id"] = db.fit_predict(coords_rad)
    df["is_hotspot"] = df["cluster_id"] != -1

    # Compute clustering evaluation metrics (excluding noise points where cluster_id == -1)
    clustered_mask = df["cluster_id"] != -1
    n_clusters = df.loc[clustered_mask, "cluster_id"].nunique()
    noise_ratio_pct = round((~clustered_mask).mean() * 100, 2)

    sil_score = np.nan
    if n_clusters > 1:
        sil_score = round(
            float(silhouette_score(coords_rad[clustered_mask], df.loc[clustered_mask, "cluster_id"], metric="haversine")),
            4,
        )

    # Summarize discovered hotspots
    hotspots = (
        df[clustered_mask]
        .groupby("cluster_id")
        .agg(
            dominant_zone=("zone", lambda x: x.mode().iloc[0] if not x.mode().empty else "Unknown"),
            nearest_anchor_store=("store_name", lambda x: x.mode().iloc[0] if not x.mode().empty else "Unknown"),
            centroid_lat=("latitude", "mean"),
            centroid_lon=("longitude", "mean"),
            ping_density=("ping_id", "count"),
            unique_devices=("device_id", "nunique"),
            avg_dwell_mins=("dwell_time_mins", "mean"),
            avg_spend_inr=("estimated_spend_inr", "mean"),
            total_spend_potential_inr=("estimated_spend_inr", "sum"),
        )
        .reset_index()
    )

    hotspots["centroid_lat"] = hotspots["centroid_lat"].round(6)
    hotspots["centroid_lon"] = hotspots["centroid_lon"].round(6)
    hotspots["avg_dwell_mins"] = hotspots["avg_dwell_mins"].round(2)
    hotspots["avg_spend_inr"] = hotspots["avg_spend_inr"].round(2)
    hotspots["total_spend_potential_inr"] = hotspots["total_spend_potential_inr"].round(2)
    hotspots = hotspots.sort_values(by="ping_density", ascending=False).reset_index(drop=True)

    os.makedirs(os.path.dirname(clustered_pings_path), exist_ok=True)
    df.to_csv(clustered_pings_path, index=False)
    hotspots.to_csv(hotspots_summary_path, index=False)

    metrics = {
        "n_clusters": int(n_clusters),
        "clustered_pings": int(clustered_mask.sum()),
        "noise_pings": int((~clustered_mask).sum()),
        "noise_ratio_pct": noise_ratio_pct,
        "silhouette_score": sil_score,
    }

    print(f"DBSCAN Clustering Complete: {n_clusters} high-density hotspots discovered.")
    print(f"Clustered Pings: {metrics['clustered_pings']} | Noise Ratio: {noise_ratio_pct}% | Silhouette Score: {sil_score}")
    print(f"Saved clustered pings -> {clustered_pings_path}")
    print(f"Saved hotspot summary -> {hotspots_summary_path}")

    return df, hotspots, metrics


if __name__ == "__main__":
    run_spatial_clustering()