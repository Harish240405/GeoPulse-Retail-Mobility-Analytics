"""
GeoPulse: data_loader.py
Generates synthetic hyper-local retail store metadata and mobile GPS telemetry
for Nagpur District commercial corridors, and cleans/enriches raw records.
"""

import os
import numpy as np
import pandas as pd


def generate_synthetic_datasets(
    raw_dir: str = "data/raw",
    num_pings: int = 5000,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    np.random.seed(seed)
    os.makedirs(raw_dir, exist_ok=True)

    stores_data = [
        ("STR_001", "Sitabuldi Main Bazaar Mart", "Grocery", "Sitabuldi", 21.1432, 79.0805, 4200),
        ("STR_002", "Eternity Mall Trends", "Apparel", "Sitabuldi", 21.1418, 79.0782, 6500),
        ("STR_003", "Variety Square Tech Hub", "Electronics", "Sitabuldi", 21.1445, 79.0818, 3100),
        ("STR_004", "Modi No. 3 Cafe & Bistro", "F&B", "Sitabuldi", 21.1425, 79.0830, 1800),
        ("STR_005", "Dharampeth Zudio Fashion", "Apparel", "Dharampeth", 21.1402, 79.0615, 5800),
        ("STR_006", "West High Court Road Brews", "F&B", "Dharampeth", 21.1388, 79.0632, 2200),
        ("STR_007", "Laxmi Nagar Fresh Hyper", "Grocery", "Dharampeth", 21.1245, 79.0680, 4900),
        ("STR_008", "Gokulpeth Digital Plaza", "Electronics", "Dharampeth", 21.1415, 79.0590, 3400),
        ("STR_009", "Sadar Residency Lounge", "F&B", "Sadar", 21.1610, 79.0765, 2600),
        ("STR_010", "Mount Road Style Studio", "Apparel", "Sadar", 21.1628, 79.0780, 4100),
        ("STR_011", "Sadar SuperBazaar", "Grocery", "Sadar", 21.1595, 79.0748, 5200),
        ("STR_012", "Kamptee Road Croma Center", "Electronics", "Sadar", 21.1650, 79.0810, 4700),
        ("STR_013", "MIHAN Central Retail Mart", "Grocery", "MIHAN & Hingna", 21.0620, 79.0350, 7200),
        ("STR_014", "Wardha Road Food Court", "F&B", "MIHAN & Hingna", 21.0850, 79.0520, 3000),
        ("STR_015", "Hingna MIDC Gadget World", "Electronics", "MIHAN & Hingna", 21.1120, 79.0150, 3800),
    ]

    stores_df = pd.DataFrame(
        stores_data,
        columns=["store_id", "store_name", "category", "zone", "latitude", "longitude", "floor_area_sqft"],
    )
    stores_path = os.path.join(raw_dir, "retail_stores.csv")
    stores_df.to_csv(stores_path, index=False)

    chosen_indices = np.random.choice(len(stores_df), size=num_pings, p=[
        0.10, 0.09, 0.08, 0.07,
        0.09, 0.08, 0.07, 0.06,
        0.07, 0.06, 0.06, 0.05,
        0.05, 0.04, 0.03,
    ])
    anchor_stores = stores_df.iloc[chosen_indices].reset_index(drop=True)

    lat_offsets = np.random.normal(loc=0.0, scale=0.0016, size=num_pings)
    lon_offsets = np.random.normal(loc=0.0, scale=0.0016, size=num_pings)

    base_timestamps = pd.date_range("2026-10-01", "2026-10-30 23:59:59", periods=num_pings)
    dwell_times = np.round(np.random.gamma(shape=2.5, scale=9.0, size=num_pings), 2)
    est_spend = np.round(dwell_times * np.random.uniform(28, 62, size=num_pings), 2)

    raw_pings = pd.DataFrame({
        "ping_id": [f"PNG_{i:06d}" for i in range(1, num_pings + 1)],
        "device_id": [f"DEV_{np.random.randint(1000, 2800)}" for _ in range(num_pings)],
        "nearest_store_id": anchor_stores["store_id"].values,
        "zone": anchor_stores["zone"].values,
        "latitude": np.round(anchor_stores["latitude"].values + lat_offsets, 6),
        "longitude": np.round(anchor_stores["longitude"].values + lon_offsets, 6),
        "timestamp": base_timestamps,
        "dwell_time_mins": dwell_times,
        "estimated_spend_inr": est_spend,
    })

    raw_pings.loc[np.random.choice(num_pings, 40, replace=False), "latitude"] = np.nan
    raw_pings.loc[np.random.choice(num_pings, 35, replace=False), "dwell_time_mins"] = -5.0
    raw_pings.loc[np.random.choice(num_pings, 34, replace=False), "latitude"] = 0.0

    raw_pings_path = os.path.join(raw_dir, "raw_mobility_pings.csv")
    raw_pings.to_csv(raw_pings_path, index=False)
    print(f"Generated Nagpur retail stores -> {stores_path}")
    print(f"Generated raw mobility pings -> {raw_pings_path}")
    return stores_df, raw_pings


def clean_mobility_pings(
    raw_pings_path: str = "data/raw/raw_mobility_pings.csv",
    processed_dir: str = "data/processed",
) -> pd.DataFrame:
    os.makedirs(processed_dir, exist_ok=True)
    df = pd.read_csv(raw_pings_path)

    clean_df = df.dropna(subset=["latitude", "longitude", "timestamp", "dwell_time_mins"]).copy()
    clean_df = clean_df[
        (clean_df["latitude"].between(20.80, 21.50))
        & (clean_df["longitude"].between(78.70, 79.40))
        & (clean_df["dwell_time_mins"] > 0)
        & (clean_df["dwell_time_mins"] <= 240)
    ].copy()

    clean_df["timestamp"] = pd.to_datetime(clean_df["timestamp"])
    clean_df["date"] = clean_df["timestamp"].dt.date
    clean_df["hour"] = clean_df["timestamp"].dt.hour
    clean_df["day_of_week"] = clean_df["timestamp"].dt.day_name()
    clean_df["is_weekend"] = clean_df["day_of_week"].isin(["Saturday", "Sunday"])

    def assign_time_slot(hr: int) -> str:
        if 6 <= hr < 12:
            return "Morning"
        elif 12 <= hr < 17:
            return "Afternoon"
        elif 17 <= hr < 22:
            return "Evening Peak"
        return "Night"

    clean_df["time_slot"] = clean_df["hour"].apply(assign_time_slot)

    output_path = os.path.join(processed_dir, "cleaned_mobility_pings.csv")
    clean_df.to_csv(output_path, index=False)
    print(f"Cleaned Nagpur mobility pings saved ({len(clean_df)} valid records) -> {output_path}")
    return clean_df


if __name__ == "__main__":
    generate_synthetic_datasets()
    clean_mobility_pings()
