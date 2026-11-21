"""End-to-end orchestration runner for GeoPulse Retail Mobility Analytics."""

from __future__ import annotations

import inspect
import logging
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from src.clustering import run_spatial_clustering
from src.data_loader import clean_mobility_pings, generate_synthetic_datasets
from src.spatial_utils import enrich_spatial_metrics, haversine_distance_m
from src.visualization import (
    generate_folium_hotspot_map,
    generate_plotly_analytics_charts,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("geopulse.pipeline")


def call_with_available_args(func: Callable[..., Any], context: dict[str, Any]) -> Any:
    """Invoke func using matching context values; fail clearly if a required arg is missing."""
    sig = inspect.signature(func)
    kwargs: dict[str, Any] = {}
    missing_required: list[str] = []

    for param_name, param in sig.parameters.items():
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if param_name in context:
            kwargs[param_name] = context[param_name]
        elif param.default is inspect.Parameter.empty:
            missing_required.append(param_name)

    if missing_required:
        raise TypeError(
            f"{func.__name__} requires unprovided arguments {missing_required} "
            f"(signature: {sig})"
        )

    return func(**kwargs)


def resolve_data(project_root: Path) -> pd.DataFrame:
    """Load existing processed/raw mobility data or generate synthetic Nagpur dataset."""
    candidates = [
        project_root / "data" / "processed" / "enriched_mobility_pings.csv",
        project_root / "data" / "processed" / "cleaned_mobility_pings.csv",
        project_root / "data" / "raw" / "mobility_pings.csv",
    ]
    existing = next((path for path in candidates if path.exists()), None)

    if existing is not None:
        logger.info("Loading dataset from %s", existing)
        df = pd.read_csv(existing)
    else:
        logger.info("No CSV found on disk; generating synthetic Nagpur dataset")
        generated = call_with_available_args(
            generate_synthetic_datasets,
            {"project_root": project_root, "output_dir": project_root / "data" / "raw"},
        )
        df = generated[0] if isinstance(generated, tuple) else generated

    if isinstance(df, pd.DataFrame):
        cleaned = call_with_available_args(
            clean_mobility_pings,
            {"df": df, "data": df, "raw_df": df},
        )
        return cleaned if isinstance(cleaned, pd.DataFrame) else df

    raise RuntimeError("Data loader did not return a pandas DataFrame.")


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    logger.info("Starting GeoPulse pipeline in %s", project_root)

    df = resolve_data(project_root)
    logger.info("Prepared DataFrame shape: %s", df.shape)

    # Sanity-check Haversine distance between Sitabuldi and MIHAN
    sample_dist_m = call_with_available_args(
        haversine_distance_m,
        {
            "lat1": 21.1458,
            "lon1": 79.0882,
            "lat2": 21.0450,
            "lon2": 79.0550,
        },
    )
    logger.info("Sample Sitabuldi -> MIHAN distance: %.1f m", float(sample_dist_m))

    enriched = call_with_available_args(
        enrich_spatial_metrics,
        {"df": df, "data": df, "pings_df": df},
    )
    if isinstance(enriched, pd.DataFrame):
        df = enriched
    logger.info("Spatial enrichment complete | columns=%d", len(df.columns))

    clustered = call_with_available_args(
        run_spatial_clustering,
        {"df": df, "data": df, "enriched_df": df},
    )
    if isinstance(clustered, pd.DataFrame):
        df = clustered
    logger.info("DBSCAN spatial clustering complete | rows=%d", len(df))

    output_dir = project_root / "reports" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    folium_out = call_with_available_args(
        generate_folium_hotspot_map,
        {"df": df, "data": df, "output_dir": output_dir, "save_path": output_dir / "nagpur_hotspot_map.html"},
    )
    logger.info("Folium map step finished -> %s", folium_out)

    plotly_out = call_with_available_args(
        generate_plotly_analytics_charts,
        {"df": df, "data": df, "output_dir": output_dir},
    )
    logger.info("Plotly charts step finished -> %s", plotly_out)

    logger.info("GeoPulse end-to-end pipeline run completed successfully.")


if __name__ == "__main__":
    main()
