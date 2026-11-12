"""
GeoPulse: data_loader.py
Generates synthetic hyper-local retail mobility data and executes the cleaning pipeline.
"""

import os
import numpy as np
import pandas as pd


def generate_sample_data(
    raw_dir: str = "data/raw", n_pings: int = 5000
) -> None:
  """Generates synthetic retail store locations and GPS foot traffic pings

  around key commercial hubs (e.g., Bengaluru / urban retail corridors).
  Includes intentional noise/anomalies to demonstrate data cleaning.
  """
  os.makedirs(raw_dir, exist_ok=True)
  np.random.seed(42)

  # 1. Generate Retail Store / POI Metadata
  stores = pd.DataFrame({
      "store_id": [f"STR_{i:03d}" for i in range(1, 16)],
      "store_name": [
          "Pulse Hypermarket",
          "Metro Fashion Hub",
          "TechZone Electronics",
          "FreshMart Groceries",
          "Urban Brew Cafe",
          "StyleVault Apparel",
          "GreenLeaf Organics",
          "Apex Footwear",
          "DailyNeeds Express",
          "GadgetWorld",
          "Luxe Cosmetics",
          "QuickBite FoodCourt",
          "BookHaven",
          "FitGear Sports",
          "HomeDecor Studio",
      ],
      "category": [
          "Grocery",
          "Apparel",
          "Electronics",
          "Grocery",
          "F&B",
          "Apparel",
          "Grocery",
          "Footwear",
          "Convenience",
          "Electronics",
          "Beauty",
          "F&B",
          "Specialty",
          "Sports",
          "Home",
      ],
      "zone": np.random.choice(
          ["Electronic City", "Koramangala", "Indiranagar", "Whitefield"], 15
      ),
      "latitude": np.random.uniform(12.8390, 12.9850, 15).round(6),
      "longitude": np.random.uniform(77.6100, 77.7500, 15).round(6),
      "floor_area_sqft": np.random.randint(1200, 15000, 15),
  })
  stores_path = os.path.join(raw_dir, "retail_stores.csv")
  stores.to_csv(stores_path, index=False)

  # 2. Generate Hyper-Local Foot Traffic GPS Pings clustered around stores
  chosen_stores = stores.sample(n_pings, replace=True).reset_index(drop=True)

  # Add spatial jitter (~50m to 500m around stores)
  lat_jitter = np.random.normal(0, 0.0025, n_pings)
  lon_jitter = np.random.normal(0, 0.0025, n_pings)

  base_time = pd.Timestamp("2026-11-01 08:00:00")
  random_minutes = np.random.randint(0, 10 * 24 * 60, n_pings)
  timestamps = [
      base_time + pd.Timedelta(minutes=int(m)) for m in random_minutes
  ]

  mobility = pd.DataFrame({
      "ping_id": [f"PNG_{i:06d}" for i in range(1, n_pings + 1)],
      "device_id": [
          f"DEV_{np.random.randint(1000, 1800)}" for _ in range(n_pings)
      ],
      "nearest_store_id": chosen_stores["store_id"],
      "zone": chosen_stores["zone"],
      "latitude": (chosen_stores["latitude"] + lat_jitter).round(6),
      "longitude": (chosen_stores["longitude"] + lon_jitter).round(6),
      "timestamp": timestamps,
      "dwell_time_mins": np.random.exponential(scale=22, size=n_pings).round(1),
      "estimated_spend_inr": (
          np.random.gamma(shape=2.2, scale=450, size=n_pings).round(2)
      ),
  })

  # Inject 2% anomalies (missing coordinates, invalid GPS bounds, negative dwell time)
  mobility.loc[mobility.sample(frac=0.01).index, "latitude"] = np.nan
  mobility.loc[mobility.sample(frac=0.005).index, "latitude"] = (
      145.999  # Invalid lat
  )
  mobility.loc[mobility.sample(frac=0.005).index, "dwell_time_mins"] = -15.0

  mobility_path = os.path.join(raw_dir, "raw_mobility_pings.csv")
  mobility.to_csv(mobility_path, index=False)
  print(f"Generated {len(stores)} stores -> {stores_path}")
  print(f"Generated {len(mobility)} raw GPS pings -> {mobility_path}")


def clean_mobility_data(
    raw_path: str = "data/raw/raw_mobility_pings.csv",
    processed_path: str = "data/processed/cleaned_mobility_pings.csv",
) -> pd.DataFrame:
  """Cleans raw mobility logs, removes GPS anomalies, and extracts time features."""
  df = pd.read_csv(raw_path)
  initial_len = len(df)

  # 1. Drop missing core records and duplicates
  df = df.dropna(
      subset=["device_id", "latitude", "longitude", "timestamp"]
  ).drop_duplicates(subset=["ping_id"])

  # 2. Filter valid study-area GPS coordinates & positive dwell time
  df = df[
      (df["latitude"].between(12.70, 13.20))
      & (df["longitude"].between(77.40, 77.90))
  ]
  df = df[df["dwell_time_mins"] > 0]

  # 3. Parse timestamps and engineer temporal features
  df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
  df = df.dropna(subset=["timestamp"])

  df["date"] = df["timestamp"].dt.date
  df["hour"] = df["timestamp"].dt.hour
  df["day_of_week"] = df["timestamp"].dt.day_name()
  df["is_weekend"] = df["timestamp"].dt.dayofweek.isin([5, 6])

  # Classify time of day
  df["time_slot"] = pd.cut(
      df["hour"],
      bins=[-1, 11, 16, 20, 24],
      labels=["Morning", "Afternoon", "Evening Peak", "Night"],
  )

  os.makedirs(os.path.dirname(processed_path), exist_ok=True)
  df.to_csv(processed_path, index=False)

  print(
      f"Cleaning complete: {len(df)} valid records retained ({initial_len - len(df)} anomalies removed)."
  )
  print(f"Saved cleaned dataset -> {processed_path}")
  return df


if __name__ == "__main__":
  generate_sample_data()
  clean_mobility_data()