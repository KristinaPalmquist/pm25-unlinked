from math import radians, sqrt, sin, cos, asin
import pandas as pd
import numpy as np


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
        df.groupby("sensor_id", group_keys=False)
          .apply(lambda g: g.set_index("date")[column]
                          .rolling(f"{window_days}D")
                          .mean()
                          .reset_index(drop=True))
          .reset_index(drop=True)
    )
    return df


def build_sensor_location_map(df, metadata):
    """Return dict: sensor_id → {latitude, longitude}"""

    if isinstance(metadata, dict):
        return metadata

    if not isinstance(metadata, pd.DataFrame):
        raise TypeError("metadata must be a DataFrame or dict")

    cols = set(metadata.columns)

    # If metadata already contains sensor_id + lat/lon
    if {"sensor_id", "latitude", "longitude"}.issubset(cols):
        sensor_locations = (
            metadata[["sensor_id", "latitude", "longitude"]]
            .drop_duplicates("sensor_id")
            .set_index("sensor_id")
        )
        return sensor_locations.to_dict(orient="index")

    # If metadata contains location_id + lat/lon
    if {"location_id", "latitude", "longitude"}.issubset(cols):
        sensor_locations = (
            df[["sensor_id", "location_id"]]
            .drop_duplicates()
            .merge(
                metadata[["location_id", "latitude", "longitude"]]
                .drop_duplicates("location_id"),
                on="location_id",
                how="left"
            )
            .drop_duplicates("sensor_id")
            .set_index("sensor_id")
        )
        return sensor_locations[["latitude", "longitude"]].to_dict(orient="index")

    raise ValueError(
        "metadata must contain either "
        "['sensor_id','latitude','longitude'] or "
        "['location_id','latitude','longitude']"
    )


def compute_closest_sensors(locations, n_closest):
    """Return dict: sensor_id → list of nearest sensor_ids"""

    closest_map = {}

    for sid, loc in locations.items():
        lat, lon = loc["latitude"], loc["longitude"]

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
    metadata,
    column="pm25_lag_1d",
    n_closest=3,
    new_column="pm25_nearby_avg"
):
    df = df.sort_values(["sensor_id", "date"]).copy()

    locations = build_sensor_location_map(df, metadata)

    closest_map = compute_closest_sensors(locations, n_closest)

    df[new_column] = np.nan

    for sid in df["sensor_id"].unique():
        neighbors = closest_map.get(sid, [])
        if not neighbors:
            continue

        neighbor_df = df[df["sensor_id"].isin(neighbors)][["date", column]]
        neighbor_avg = neighbor_df.groupby("date")[column].mean().reset_index()

        merged = df[df["sensor_id"] == sid].merge(neighbor_avg, on="date", how="left")
        df.loc[df["sensor_id"] == sid, new_column] = merged[column + "_y"]

    return df

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