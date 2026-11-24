"""
GeoPulse: app.py
Interactive Streamlit Executive Dashboard for Hyper-Local Retail Mobility Analytics.
"""
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import os
import plotly.express as px

# Page Configuration
st.set_page_config(
    page_title="GeoPulse Analytics Dashboard",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for modern executive look
st.markdown("""
    <style>
        .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; }
        .sub-header { font-size: 1.1rem; color: #475569; }
        .metric-card { background-color: #F8FAFC; padding: 20px; border-radius: 10px; border-left: 5px solid #3B82F6; }
    </style>
""", unsafe_allow_html=True)

# Load Datasets with caching
@st.cache_data
def load_dashboard_data():
    store_kpis = pd.read_csv("data/processed/store_performance_kpis.csv")
    hotspots = pd.read_csv("data/processed/hotspot_clusters_summary.csv")
    enriched_pings = pd.read_csv("data/processed/enriched_mobility_pings.csv")
    return store_kpis, hotspots, enriched_pings

store_kpis, hotspots, enriched_pings = load_dashboard_data()

# Sidebar Filters
st.sidebar.image("https://img.icons8.com/color/96/marker.png", width=60)
st.sidebar.title("GeoPulse Controls")
st.sidebar.markdown("---")

# Filter logic
selected_zone = st.sidebar.selectbox(
    "Filter by Commercial Zone",
    options=["All Zones"] + sorted(enriched_pings["zone"].dropna().unique().tolist()),
    key="sidebar_zone_filter",
)
selected_category = st.sidebar.selectbox(
    "Filter by Store Category",
    options=["All Categories"] + sorted(store_kpis["category"].dropna().unique().tolist()),
    key="sidebar_category_filter",
)

# Filter stores and pings consistently
filtered_stores = store_kpis.copy()
filtered_pings = enriched_pings.copy()

if selected_zone != "All Zones":
    filtered_stores = filtered_stores[filtered_stores["zone"] == selected_zone]
    if "zone" in filtered_pings.columns:
        filtered_pings = filtered_pings[filtered_pings["zone"] == selected_zone]

if selected_category != "All Categories":
    filtered_stores = filtered_stores[filtered_stores["category"] == selected_category]
    if "nearest_store_id" in filtered_pings.columns and "store_id" in filtered_stores.columns:
        valid_store_ids = set(filtered_stores["store_id"].unique())
        filtered_pings = filtered_pings[filtered_pings["nearest_store_id"].isin(valid_store_ids)]

filtered_stores = filtered_stores.reset_index(drop=True)

# Main Dashboard Header
st.markdown(
    '<p class="main-header">📍 GeoPulse: Hyper-Local Retail Mobility Analytics</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="sub-header">Infotact Solutions Data Analytics Internship Project | Executive Intelligence Suite</p>',
    unsafe_allow_html=True,
)
st.markdown("---")

# Top-level Metric Cards
# ==========================================
# DYNAMIC EXECUTIVE KPI CARDS
# ==========================================

filtered_hotspots = hotspots.copy()

# Apply zone filter when hotspot data supports it
if selected_zone != "All Zones":
    if "dominant_zone" in filtered_hotspots.columns:
        filtered_hotspots = filtered_hotspots[
            filtered_hotspots["dominant_zone"] == selected_zone
        ]

# Apply category filter when hotspot data supports it
if selected_category != "All Categories":
    if "dominant_category" in filtered_hotspots.columns:
        filtered_hotspots = filtered_hotspots[
            filtered_hotspots["dominant_category"] == selected_category
        ]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Filtered Retail Anchors",
        f"{len(filtered_stores):,}"
    )
    st.caption(f"Total dataset outlets: {len(store_kpis):,}")

with col2:
    st.metric(
        "Total Foot Traffic Pings",
        f"{len(filtered_pings):,}"
    )

with col3:
    st.metric(
        "Discovered Hotspots",
        f"{len(filtered_hotspots):,}"
    )

with col4:
    st.metric(
        "Est. Revenue Potential",
        f"₹ {filtered_stores['total_estimated_revenue_inr'].sum():,.2f}"
    )

# Tabs for structured navigation
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Executive Overview",
        "🗺️ Geospatial Hotspots",
        "🏬 Store Performance KPIs",
        "📈 Traffic & Dwell Trends",
    ]
)

with tab1:
    st.subheader("Executive Summary & Business Intelligence")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            """
- **Hyper-Local Intelligence:** Combining mobile GPS telemetry with store boundaries to measure real consumer foot traffic.
- **Catchment Optimization:** Analyzing `100m`, `300m`, and `600m` customer catchment rings to identify underperforming store radii.
- **DBSCAN Hotspot Detection:** Automatically isolating high-density crowd clusters to recommend optimal retail expansion sites.
            """
        )
    with col_b:
        st.info(
            "💡 **Key Finding:** Sitabuldi and Dharampeth exhibit the highest evening peak footfall density in Nagpur "
            "District, driven largely by Apparel, F&B, and Grocery retail anchors."
        )

    st.markdown("### Top Performing Stores by Footfall")
    top_stores_df = (
        filtered_stores[
            [
                "store_name",
                "category",
                "zone",
                "total_footfall",
                "capture_rate_pct",
                "total_estimated_revenue_inr",
            ]
        ]
        .sort_values(by="total_footfall", ascending=False)
        .reset_index(drop=True)
    )
    st.dataframe(top_stores_df, hide_index=True, width="stretch")

with tab2:
    st.subheader("Geospatial Hotspots & Retail Catchment (Nagpur District)")

    map_html_path = "outputs/figures/interactive_retail_hotspots_map.html"

    if os.path.exists(map_html_path):
        with open(map_html_path, "r", encoding="utf-8") as f:
            map_html = f.read()

        st.components.v1.html(
            map_html,
            height=520,
            scrolling=True
        )

    else:
        st.info(
            "Saved HTML map not found — rendering live DBSCAN hotspot map."
        )

        # Use the actual dataset column names
        if {"centroid_lat", "centroid_lon"}.issubset(hotspots.columns):

            map_df = hotspots.copy()

            map_df["centroid_lat"] = pd.to_numeric(
                map_df["centroid_lat"], errors="coerce"
            )
            map_df["centroid_lon"] = pd.to_numeric(
                map_df["centroid_lon"], errors="coerce"
            )

            map_df = map_df.dropna(
                subset=["centroid_lat", "centroid_lon"]
            )

            if not map_df.empty:

                fig_map = px.scatter_map(
                    map_df,
                    lat="centroid_lat",
                    lon="centroid_lon",
                    size="ping_density" if "ping_density" in map_df.columns else None,
                    color=(
                        map_df["cluster_id"].astype(str)
                        if "cluster_id" in map_df.columns
                        else "dominant_zone"
                    ),
                    hover_name=(
                        "dominant_zone"
                        if "dominant_zone" in map_df.columns
                        else None
                    ),
                    hover_data=[
                        c for c in [
                            "nearest_anchor_store",
                            "ping_density",
                            "unique_devices",
                            "avg_dwell_mins",
                            "avg_spend_inr"
                        ] if c in map_df.columns
                    ],
                    zoom=11,
                    center={
                        "lat": map_df["centroid_lat"].mean(),
                        "lon": map_df["centroid_lon"].mean()
                    },
                    map_style="open-street-map",
                    title="Nagpur Retail Footfall Hotspots",
                    height=550
                )

                # Add retail store locations to the existing hotspot map
                store_map_df = filtered_stores.copy()

                store_map_df["latitude_store"] = pd.to_numeric(
                    store_map_df["latitude_store"], errors="coerce"
                )
                store_map_df["longitude_store"] = pd.to_numeric(
                    store_map_df["longitude_store"], errors="coerce"
                )

                store_map_df = store_map_df.dropna(
                    subset=["latitude_store", "longitude_store"]
                )

                if not store_map_df.empty:

                    store_fig = px.scatter_map(
                        store_map_df,
                        lat="latitude_store",
                        lon="longitude_store",
                        hover_name="store_name",
                        hover_data=[
                            "store_id",
                            "category",
                            "zone",
                            "total_footfall",
                            "avg_dwell_time_mins",
                            "total_estimated_revenue_inr"
                        ],
                        zoom=11,
                        map_style="open-street-map"
                    )

                    for trace in store_fig.data:
                        trace.name = "Retail Stores"
                        trace.legendgroup = "Retail Stores"
                        trace.marker.size = 13
                        trace.marker.color = "#EF4444"
                        trace.marker.opacity = 1
                        fig_map.add_trace(trace)

                st.plotly_chart(fig_map, width="stretch")

                # -----------------------------------------
                # RETAIL STORE CATCHMENT RADIUS ANALYSIS
                # -----------------------------------------

                st.markdown("### Retail Store Catchment Analysis")

                selected_store_name = st.selectbox(
                    "Select Retail Store",
                    options=store_map_df["store_name"].tolist(),
                    key="catchment_store_selector"
                )

                selected_store = store_map_df[
                    store_map_df["store_name"] == selected_store_name
                ].iloc[0]

                center_lat = float(selected_store["latitude_store"])
                center_lon = float(selected_store["longitude_store"])

                earth_radius = 6371000
                bearings = np.linspace(0, 2 * np.pi, 100)

                catchment_zones = [
                    (100, "#22C55E"),
                    (300, "#F59E0B"),
                    (600, "#EF4444")
                ]

                for radius, ring_color in catchment_zones:

                    angular_distance = radius / earth_radius

                    lat1 = np.radians(center_lat)
                    lon1 = np.radians(center_lon)

                    lat2 = np.arcsin(
                        np.sin(lat1) * np.cos(angular_distance)
                        + np.cos(lat1) * np.sin(angular_distance)
                        * np.cos(bearings)
                    )

                    lon2 = lon1 + np.arctan2(
                        np.sin(bearings) * np.sin(angular_distance)
                        * np.cos(lat1),
                        np.cos(angular_distance)
                        - np.sin(lat1) * np.sin(lat2)
                    )

                    fig_map.add_trace(
                        go.Scattermap(
                            lat=np.degrees(lat2),
                            lon=np.degrees(lon2),
                            mode="lines",
                            line=dict(
                                color=ring_color,
                                width=2
                            ),
                            name=f"{radius}m Catchment",
                            hovertemplate=(
                                f"{radius}m Catchment"
                                "<extra></extra>"
                            )
                        )
                    )

                st.caption(
                    f"Showing 100m, 300m and 600m catchment "
                    f"radii around {selected_store_name}."
                )

                st.plotly_chart(fig_map, width="stretch")

            else:
                st.warning("No valid hotspot coordinates found.")

        else:
            st.error(
                "Required coordinate columns centroid_lat and centroid_lon "
                "are missing from the hotspot dataset."
            )

    st.markdown("### Discovered DBSCAN Hotspot Summary")

    st.dataframe(
        hotspots.reset_index(drop=True),
        hide_index=True,
        width="stretch"
    )

# ==========================================
# TAB 3: STORE PERFORMANCE KPIs
# ==========================================

with tab3:
    st.subheader("🏬 Retail Store Performance Analysis")

    if not filtered_stores.empty:

        # Store selection
        selected_store = st.selectbox(
            "Select Retail Store",
            filtered_stores["store_name"].unique(),
            key="performance_store"
        )

        store_data = filtered_stores[
            filtered_stores["store_name"] == selected_store
        ].iloc[0]

        # Store KPI metrics
        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Total Footfall",
            f"{store_data['total_footfall']:,.0f}"
        )

        c2.metric(
            "Unique Visitors",
            f"{store_data['unique_visitors']:,.0f}"
        )

        c3.metric(
            "Capture Rate",
            f"{store_data['capture_rate_pct']:.2f}%"
        )

        c4.metric(
            "Average Dwell Time",
            f"{store_data['avg_dwell_time_mins']:.2f} min"
        )

        st.markdown("---")

        # Store performance charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Footfall by Retail Store")

            fig_footfall = px.bar(
                filtered_stores.sort_values(
                    "total_footfall", ascending=False
                ),
                x="store_name",
                y="total_footfall",
                color="category",
                title="Store Footfall Comparison"
            )

            fig_footfall.update_layout(
                xaxis_title="Retail Store",
                yaxis_title="Total Footfall",
                xaxis_tickangle=-45
            )

            st.plotly_chart(fig_footfall, width="stretch")

        with col2:
            st.markdown("### Estimated Revenue by Store")

            fig_revenue = px.bar(
                filtered_stores.sort_values(
                    "total_estimated_revenue_inr",
                    ascending=False
                ),
                x="store_name",
                y="total_estimated_revenue_inr",
                color="category",
                title="Revenue Potential by Store"
            )

            fig_revenue.update_layout(
                xaxis_title="Retail Store",
                yaxis_title="Estimated Revenue (₹)",
                xaxis_tickangle=-45
            )

            st.plotly_chart(fig_revenue, width="stretch")

        # Complete store performance table
        st.markdown("### Detailed Store Performance")

        st.dataframe(
            filtered_stores,
            hide_index=True,
            width="stretch"
        )

    else:
        st.warning("No stores available for the selected filters.")

# ==========================================
# TAB 4: TRAFFIC & DWELL TRENDS
# ==========================================

with tab4:
    st.subheader("📈 Consumer Mobility & Traffic Analysis")

    traffic_df = filtered_pings.copy()

    if not traffic_df.empty:

        traffic_df["timestamp"] = pd.to_datetime(
            traffic_df["timestamp"],
            errors="coerce"
        )

        traffic_df["hour"] = pd.to_numeric(
            traffic_df["hour"],
            errors="coerce"
        )

        traffic_df["dwell_time_mins"] = pd.to_numeric(
            traffic_df["dwell_time_mins"],
            errors="coerce"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Mobility Records",
            f"{len(traffic_df):,}"
        )

        col2.metric(
            "Average Dwell Time",
            f"{traffic_df['dwell_time_mins'].mean():.2f} min"
        )

        col3.metric(
            "Estimated Consumer Spend",
            f"₹ {traffic_df['estimated_spend_inr'].sum():,.2f}"
        )

        st.markdown("---")

        # Hourly footfall trends
        st.markdown("### Hourly Consumer Traffic")

        hourly_traffic = (
            traffic_df.groupby("hour")
            .size()
            .reset_index(name="total_pings")
            .sort_values("hour")
        )

        fig_hourly = px.line(
            hourly_traffic,
            x="hour",
            y="total_pings",
            markers=True,
            title="Hourly Foot Traffic Distribution"
        )

        st.plotly_chart(fig_hourly, width="stretch")

        # Time slot analysis
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Traffic by Time Slot")

            time_slot_data = (
                traffic_df.groupby("time_slot")
                .size()
                .reset_index(name="total_pings")
            )

            fig_slot = px.bar(
                time_slot_data,
                x="time_slot",
                y="total_pings",
                color="time_slot",
                title="Consumer Activity by Time Slot"
            )

            st.plotly_chart(fig_slot, width="stretch")

        with col2:
            st.markdown("### Average Dwell Time by Zone")

            dwell_zone = (
                traffic_df.groupby("zone")["dwell_time_mins"]
                .mean()
                .reset_index()
            )

            fig_dwell = px.bar(
                dwell_zone,
                x="zone",
                y="dwell_time_mins",
                color="dwell_time_mins",
                title="Average Dwell Time Across Zones"
            )

            st.plotly_chart(fig_dwell, width="stretch")

        # Consumer spending trends
        st.markdown("### Consumer Spending Analysis")

        spending = (
            traffic_df.groupby("category")["estimated_spend_inr"]
            .sum()
            .reset_index()
            .sort_values("estimated_spend_inr", ascending=False)
        )

        fig_spending = px.pie(
            spending,
            names="category",
            values="estimated_spend_inr",
            hole=0.45,
            title="Estimated Spending by Store Category"
        )

        st.plotly_chart(fig_spending, width="stretch")


        # ==========================================
        # CATCHMENT PERFORMANCE ANALYSIS
        # ==========================================
        st.markdown("---")
        st.subheader("🎯 Customer Catchment Performance Analysis")

        catchment_required = {
            "ping_id", "catchment_ring", "device_id",
            "dwell_time_mins", "estimated_spend_inr", "is_store_visit"
        }

        missing_catchment_columns = catchment_required.difference(traffic_df.columns)

        if missing_catchment_columns:
            st.warning(
                "Catchment analysis cannot run. Missing columns: "
                + ", ".join(sorted(missing_catchment_columns))
            )
        else:
            catchment_df = traffic_df.copy()
            catchment_df["dwell_time_mins"] = pd.to_numeric(
                catchment_df["dwell_time_mins"], errors="coerce"
            )
            catchment_df["estimated_spend_inr"] = pd.to_numeric(
                catchment_df["estimated_spend_inr"], errors="coerce"
            ).fillna(0)
            catchment_df["is_store_visit"] = catchment_df["is_store_visit"].fillna(False).astype(bool)

            catchment_summary = (
                catchment_df.groupby("catchment_ring", dropna=False)
                .agg(
                    Total_Pings=("ping_id", "count"),
                    Unique_Devices=("device_id", "nunique"),
                    Average_Dwell=("dwell_time_mins", "mean"),
                    Estimated_Spend=("estimated_spend_inr", "sum"),
                    Store_Visits=("is_store_visit", "sum")
                )
                .reset_index()
            )

            if catchment_summary.empty:
                st.info("No catchment records are available for the selected filters.")
            else:
                col_c1, col_c2 = st.columns(2)

                with col_c1:
                    fig_catchment = px.bar(
                        catchment_summary,
                        x="catchment_ring",
                        y="Total_Pings",
                        color="catchment_ring",
                        text_auto=True,
                        title="Customer Distribution by Catchment Ring",
                        labels={
                            "catchment_ring": "Catchment Distance",
                            "Total_Pings": "Total Mobility Pings"
                        }
                    )
                    st.plotly_chart(fig_catchment, width="stretch")

                with col_c2:
                    fig_catchment_spend = px.bar(
                        catchment_summary,
                        x="catchment_ring",
                        y="Estimated_Spend",
                        color="catchment_ring",
                        text_auto=".2s",
                        title="Estimated Consumer Spending by Catchment",
                        labels={
                            "catchment_ring": "Catchment Distance",
                            "Estimated_Spend": "Estimated Spend (INR)"
                        }
                    )
                    st.plotly_chart(fig_catchment_spend, width="stretch")

                st.markdown("### Catchment Performance Summary")
                st.dataframe(
                    catchment_summary.round(2),
                    hide_index=True,
                    width="stretch"
                )

                # ==========================================
                # STORE VISIT CONVERSION ANALYSIS
                # ==========================================
                st.markdown("---")
                st.subheader("📊 Store Visit Conversion Analysis")

                conversion_df = catchment_summary.copy()
                conversion_df["Visit_Rate_Pct"] = (
                    conversion_df["Store_Visits"]
                    .div(conversion_df["Total_Pings"].replace(0, np.nan))
                    .mul(100)
                )
                conversion_df["Spend_Per_Ping"] = (
                    conversion_df["Estimated_Spend"]
                    .div(conversion_df["Total_Pings"].replace(0, np.nan))
                )
                conversion_df[["Visit_Rate_Pct", "Spend_Per_Ping"]] = (
                    conversion_df[["Visit_Rate_Pct", "Spend_Per_Ping"]].fillna(0)
                )

                valid_conversion = conversion_df[conversion_df["Total_Pings"] > 0]
                if not valid_conversion.empty:
                    best_catchment = valid_conversion.loc[
                        valid_conversion["Visit_Rate_Pct"].idxmax()
                    ]
                    overall_spend_per_ping = (
                        conversion_df["Estimated_Spend"].sum()
                        / max(conversion_df["Total_Pings"].sum(), 1)
                    )

                    metric_a, metric_b, metric_c = st.columns(3)
                    metric_a.metric(
                        "Highest Visit Rate",
                        f"{best_catchment['Visit_Rate_Pct']:.2f}%"
                    )
                    metric_b.metric(
                        "Best Catchment by Visit Rate",
                        str(best_catchment["catchment_ring"])
                    )
                    metric_c.metric(
                        "Average Spend per Ping",
                        f"₹{overall_spend_per_ping:,.2f}"
                    )

                    fig_conversion = px.bar(
                        conversion_df,
                        x="catchment_ring",
                        y="Visit_Rate_Pct",
                        color="catchment_ring",
                        text_auto=".2f",
                        title="Store Visit Rate by Catchment Ring",
                        labels={
                            "catchment_ring": "Catchment Ring",
                            "Visit_Rate_Pct": "Visit Rate (%)"
                        }
                    )
                    st.plotly_chart(fig_conversion, width="stretch")

                    st.markdown("### Catchment Business Performance")
                    st.dataframe(
                        conversion_df[[
                            "catchment_ring", "Total_Pings", "Store_Visits",
                            "Visit_Rate_Pct", "Average_Dwell", "Spend_Per_Ping"
                        ]].round(2),
                        hide_index=True,
                        width="stretch"
                    )
                else:
                    st.info("No mobility pings are available to calculate visit conversion.")

    else:
        st.warning("No mobility records available for the selected filters.")
