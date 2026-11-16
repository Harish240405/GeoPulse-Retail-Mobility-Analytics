# GeoPulse: Data Dictionary & Schema Governance

## 1. Retail Store Metadata (`data/raw/retail_stores.csv`)
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `store_id` | String | Unique identifier for each retail point of interest (e.g., `STR_001`). |
| `store_name` | String | Commercial name of the retail outlet. |
| `category` | String | Retail segment (`Grocery`, `Apparel`, `Electronics`, `F&B`, etc.). |
|zone: Urban commercial corridor in Nagpur District (Sitabuldi, Dharampeth, Sadar, MIHAN & Hingna).
latitude: Validated latitude (20.80 to 21.50).
longitude: Validated longitude (78.70 to 79.40).

## 2. Cleaned Mobility Pings (`data/processed/cleaned_mobility_pings.csv`)
| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `ping_id` | String | Unique telemetry ping identifier (`PNG_000001`). |
| `device_id` | String | Anonymized mobile device identifier (`DEV_1001`). |
| `nearest_store_id` | String | Foreign key linking to `retail_stores.store_id`. |
| |zone: Urban commercial corridor in Nagpur District (Sitabuldi, Dharampeth, Sadar, MIHAN & Hingna).
latitude: Validated latitude (20.80 to 21.50).
longitude: Validated longitude (78.70 to 79.40). |
| `timestamp` | Datetime | ISO-8601 timestamp of foot-traffic observation. |
| `dwell_time_mins` | Float | Duration spent within store proximity in minutes (`> 0`). |
| `estimated_spend_inr` | Float | Modeled consumer transaction value in INR. |
| `date` | Date | Calendar date extracted from `timestamp`. |
| `hour` | Integer | Hour of day (`0`–`23`). |
| `day_of_week` | String | Day name (`Monday`–`Sunday`). |
| `is_weekend` | Boolean | `True` if Saturday or Sunday, else `False`. |
| `time_slot` | Category | `Morning`, `Afternoon`, `Evening Peak`, or `Night`. |