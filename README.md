# GeoPulse: Hyper-Local Retail Mobility Analytics

**GeoPulse** is an advanced data analytics and spatial mobility intelligence pipeline designed to analyze urban foot traffic, retail congregation zones, and consumer movement patterns for strategic retail site selection and spatial optimization.

---

## 📁 Repository Directory Structure

```text
GeoPulse/
│
├── data/                    # Data directory (ignored in git except samples)
│   ├── raw/                 # Original GPS pings, foot traffic sensor logs, and store metadata
│   ├── processed/           # Cleaned datasets, spatially aggregated grids, and merged features
│   └── external/            # Census tracts, administrative boundaries, and POI shapefiles
│
├── notebooks/               # Jupyter Notebooks for iterative analysis and prototyping
│   ├── 01_data_cleaning.ipynb
│   ├── 02_spatial_eda.ipynb
│   ├── 03_mobility_clustering.ipynb
│   └── 04_predictive_hotspots.ipynb
│
├── src/                     # Core production python modules
│   ├── __init__.py
│   ├── data_loader.py       # Ingestion, validation, and cleaning pipelines
│   ├── spatial_utils.py     # GeoPandas and Shapely spatial operations & transformations
│   ├── clustering.py        # Spatial clustering models (DBSCAN / HDBSCAN / K-Means)
│   └── visualization.py     # Folium and Plotly interactive map generators
│
├── dashboards/              # Interactive dashboard application
│   └── app.py               # Streamlit web app for retail mobility insights
│
├── outputs/                 # Generated deliverables, figures, and reports
│   ├── figures/             # Exported maps, correlation matrices, and charts
│   └── reports/             # PDF reports and analytical summaries
│
├── tests/                   # Unit tests for data pipelines and utilities
│   └── test_data_loader.py
│
├── .gitignore               # Git ignore rules for virtualenvs, cache, and raw data
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
