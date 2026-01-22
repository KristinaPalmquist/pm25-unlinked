from math import radians, sqrt, sin, cos, asin
import pandas as pd
import numpy as np
from requests_cache import Dict, Union
from collections.abc import Mapping



# 📍 Haversine distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))


def add_lagged_features(df, column="pm25", lags=[1, 2, 3]):
    df = df.sort_values(["sensor_id", "date"]).copy()
    for lag in lags:
        df[f"{column}_lag_{lag}d"] = df.groupby("sensor_id")[column].shift(lag)
    return df


def add_rolling_window_feature(df, window_days=3, column="pm25", new_column="pm25_rolling_3d"):
    df = df.sort_values(["sensor_id", "date"]).copy()
    df[new_column] = (
        df.groupby("sensor_id")[column]
          .transform(lambda x: x.rolling(window_days, min_periods=1).mean().shift(1))
    )
    return df


def build_sensor_location_map(df, metadata):
    # metadata is already a mapping: sensor_id -> dict with latitude/longitude
    from collections.abc import Mapping

    if isinstance(metadata, Mapping):
        return {
            sid: {
                "latitude": float(meta["latitude"]),
                "longitude": float(meta["longitude"]),
            }
            for sid, meta in metadata.items()
        }
    raise TypeError("metadata must be a mapping of sensor_id -> {latitude, longitude}")


# def build_sensor_location_map(df, metadata):
#     """Return dict: sensor_id → {latitude, longitude}"""

#     # Case 1: metadata is already a dict of dicts
#     if isinstance(metadata, Mapping):
#         cleaned = {}
#         for sid, meta in metadata.items():
#             cleaned[sid] = {
#                 "latitude": float(meta["latitude"]),
#                 "longitude": float(meta["longitude"])
#             }
#         return cleaned

#     # Case 2: metadata is a DataFrame
#     if not isinstance(metadata, pd.DataFrame):
#         raise TypeError("metadata must be a DataFrame or dict")

#     required = {"sensor_id", "latitude", "longitude"}
#     if not required.issubset(metadata.columns):
#         raise ValueError("metadata must contain ['sensor_id', 'latitude', 'longitude']")

#     sensor_locations = (
#         metadata[["sensor_id", "latitude", "longitude"]]
#         .drop_duplicates("sensor_id")
#         .set_index("sensor_id")
#         .astype(float)
#     )

#     return sensor_locations.to_dict(orient="index")


def compute_closest_sensors(locations, n_closest):
    """Return dict: sensor_id → list of nearest sensor_ids"""

    closest_map = {}

    for sid, loc in locations.items():
        lat, lon = loc["latitude"], loc["longitude"]
        lat = float(lat)
        lon = float(lon)

        distances = [
            (
                oid,
                haversine(lat, lon,
                          locations[oid]["latitude"],
                          locations[oid]["longitude"])
            )
            for oid in locations
            if oid != sid
        ]

        closest_map[sid] = [
            oid for oid, _ in sorted(distances, key=lambda x: x[1])[:n_closest]
        ]

    return closest_map


def add_nearby_sensor_feature(
    df,
    sensor_metadata,
    column="pm25_lag_1d",
    n_closest=3,
    new_column="pm25_nearby_avg",
):
    df = df.sort_values(["sensor_id", "date"]).copy()

    locations = build_sensor_location_map(df, sensor_metadata)
    closest_map = compute_closest_sensors(locations, n_closest)

    df[new_column] = np.nan

    for sid in df["sensor_id"].unique():
        neighbors = closest_map.get(sid, [])
        if not neighbors:
            continue

        neighbor_df = df[df["sensor_id"].isin(neighbors)][["date", column]]
        neighbor_avg = neighbor_df.groupby("date")[column].mean().reset_index()
        neighbor_avg.columns = ["date", new_column]

        # Get the indices where sensor_id matches
        sensor_mask = df["sensor_id"] == sid
        sensor_indices = df[sensor_mask].index
        
        # Merge and preserve the index
        sensor_data = df.loc[sensor_indices, ["date"]].reset_index()
        merged = sensor_data.merge(neighbor_avg, on="date", how="left")
        
        # Assign using the original indices
        df.loc[sensor_indices, new_column] = merged[new_column].values

    return df

# def add_nearby_sensor_feature(
#     df,
#     sensor_metadata: Union[pd.DataFrame, Dict],
#     column="pm25_lag_1d",
#     n_closest=3,
#     new_column="pm25_nearby_avg"
# ):
#     df = df.sort_values(["sensor_id", "date"]).copy()

#     locations = build_sensor_location_map(df, sensor_metadata)
#     print("DEBUG LOCATIONS:", list(locations.items())[:3])

#     if isinstance(sensor_metadata, Mapping):
#         sensor_metadata = pd.DataFrame([
#             {
#                 "sensor_id": sid,
#                 "latitude": meta["latitude"],
#                 "longitude": meta["longitude"]
#             }
#             for sid, meta in sensor_metadata.items()
#         ])

#     locations = build_sensor_location_map(df, sensor_metadata)
#     closest_map = compute_closest_sensors(locations, n_closest)

#     df[new_column] = np.nan

#     for sid in df["sensor_id"].unique():
#         neighbors = closest_map.get(sid, [])
#         if not neighbors:
#             continue

#         neighbor_df = df[df["sensor_id"].isin(neighbors)][["date", column]]
#         neighbor_avg = neighbor_df.groupby("date")[column].mean().reset_index()

#         merged = df[df["sensor_id"] == sid].merge(neighbor_avg, on="date", how="left")
#         df.loc[df["sensor_id"] == sid, new_column] = merged[column + "_y"]

#     return df



# def add_nearby_sensor_feature(
#     df,
#     sensor_metadata: Union[pd.DataFrame, Dict],
#     column="pm25_lag_1d",
#     n_closest=3,
#     new_column="pm25_nearby_avg"
# ):
#     # Convert dict to DataFrame if needed
#     if isinstance(sensor_metadata, dict):
#         sensor_metadata = pd.DataFrame([
#             {"sensor_id": sid, "latitude": lat, "longitude": lon}
#             for sid, (lat, lon, *_) in sensor_metadata.items()
#         ])
#     df = df.sort_values(["sensor_id", "date"]).copy()

#     locations = build_sensor_location_map(df, sensor_metadata)

#     closest_map = compute_closest_sensors(locations, n_closest)

#     df[new_column] = np.nan

#     for sid in df["sensor_id"].unique():
#         neighbors = closest_map.get(sid, [])
#         if not neighbors:
#             continue

#         neighbor_df = df[df["sensor_id"].isin(neighbors)][["date", column]]
#         neighbor_avg = neighbor_df.groupby("date")[column].mean().reset_index()

#         merged = df[df["sensor_id"] == sid].merge(neighbor_avg, on="date", how="left")
#         df.loc[df["sensor_id"] == sid, new_column] = merged[column + "_y"]

#     return df

# def add_nearby_sensor_feature(df, locations, column="pm25_lag_1d", n_closest=3, new_column="pm25_nearby_avg"):
#     df = df.sort_values(["sensor_id", "date"]).copy()

#     # 🔧 Convert DataFrame to dict if needed
#     if isinstance(locations, pd.DataFrame):
#         if not {"latitude", "longitude"}.issubset(locations.columns):
#             raise ValueError("locations DataFrame must contain 'latitude' and 'longitude' columns")
#         locations = locations[["latitude", "longitude"]].to_dict(orient="index")

#     # 🔁 Precompute closest sensors
#     closest_map = {}
#     for sid, loc in locations.items():
#         if "latitude" not in loc or "longitude" not in loc:
#             continue
#         distances = [
#             (oid, haversine(loc["latitude"], loc["longitude"],
#                             locations[oid]["latitude"], locations[oid]["longitude"]))
#             for oid in locations if oid != sid and "latitude" in locations[oid] and "longitude" in locations[oid]
#         ]
#         closest_map[sid] = [oid for oid, _ in sorted(distances, key=lambda x: x[1])[:n_closest]]

#     # 🧮 Compute nearby averages
#     df[new_column] = np.nan
#     for sid in df["sensor_id"].unique():
#         neighbors = closest_map.get(sid, [])
#         if not neighbors:
#             continue

#         neighbor_df = df[df["sensor_id"].isin(neighbors)][["date", column]]
#         neighbor_avg = neighbor_df.groupby("date")[column].mean().reset_index()

#         merged = df[df["sensor_id"] == sid].merge(neighbor_avg, on="date", how="left")
#         df.loc[df["sensor_id"] == sid, new_column] = merged[column + "_y"]

#     return df