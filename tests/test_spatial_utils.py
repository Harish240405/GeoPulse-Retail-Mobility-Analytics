"""Unit tests for spatial utilities, Nagpur bounds, and dwell-spend helpers."""

import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    )
    return 2.0 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def is_within_nagpur_bounds(lat: float, lon: float) -> bool:
    return (20.80 <= lat <= 21.50) and (78.70 <= lon <= 79.40)


def spend_per_minute(estimated_spend_inr: float, dwell_time_mins: float) -> float:
    safe_dwell = max(dwell_time_mins, 1.0)
    return estimated_spend_inr / safe_dwell


def test_haversine_zero_distance() -> None:
    assert haversine_km(21.1458, 79.0882, 21.1458, 79.0882) == 0.0


def test_haversine_symmetry() -> None:
    d_ab = haversine_km(21.1458, 79.0882, 21.0450, 79.0550)
    d_ba = haversine_km(21.0450, 79.0550, 21.1458, 79.0882)
    assert math.isclose(d_ab, d_ba, rel_tol=1e-9)


def test_haversine_sitabuldi_to_mihan_approx() -> None:
    dist = haversine_km(21.1458, 79.0882, 21.0450, 79.0550)
    assert 10.0 < dist < 14.0


def test_nagpur_corridor_bounds_valid_and_out_of_bounds() -> None:
    assert is_within_nagpur_bounds(21.1458, 79.0882) is True   # Sitabuldi
    assert is_within_nagpur_bounds(21.1466, 79.0560) is True   # Dharampeth
    assert is_within_nagpur_bounds(21.1615, 79.0822) is True   # Sadar
    assert is_within_nagpur_bounds(21.0450, 79.0550) is True   # MIHAN
    assert is_within_nagpur_bounds(19.0760, 72.8777) is False  # Mumbai (outside)
    assert is_within_nagpur_bounds(22.5000, 79.0882) is False  # Latitude too high


def test_spend_per_minute_clamps_short_dwell() -> None:
    assert spend_per_minute(300.0, 0.0) == 300.0
    assert spend_per_minute(300.0, 10.0) == 30.0
