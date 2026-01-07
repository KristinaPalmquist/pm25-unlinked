from hsfs.transformation_function import TransformationFunction
import pandas as pd
import numpy as np


# Lag features
@TransformationFunction
def pm25_lag_1d(df: pd.DataFrame) -> pd.Series:
    return df.groupby("sensor_id")["pm25"].shift(1)


@TransformationFunction
def pm25_lag_2d(df: pd.DataFrame) -> pd.Series:
    return df.groupby("sensor_id")["pm25"].shift(2)


@TransformationFunction
def pm25_lag_3d(df: pd.DataFrame) -> pd.Series:
    return df.groupby("sensor_id")["pm25"].shift(3)


# Rolling window feature
@TransformationFunction
def pm25_rolling_3d(df: pd.DataFrame) -> pd.Series:
    # Rolling window over 3 days using datetime as the time index
    return (
        df.sort_values(["sensor_id", "datetime"])
          .groupby("sensor_id")
          .rolling("3D", on="datetime")["pm25"]
          .mean()
          .reset_index(level=0, drop=True)
    )


# Nearby sensor feature
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(np.radians(lat1))
        * np.cos(np.radians(lat2))
        * np.sin(dlon / 2) ** 2
    )
    return 2 * R * np.arcsin(np.sqrt(a))

@TransformationFunction
def pm25_nearby_avg(df: pd.DataFrame) -> pd.Series:
    """
    Computes the average pm25_lag_1d from the 3 nearest sensors.
    Works out-of-the-box for any user, anywhere.
    """
    df = df.sort_values(["sensor_id", "datetime"]).copy()

    # Precompute lag
    df["pm25_lag_1d"] = df.groupby("sensor_id")["pm25"].shift(1)

    results = []

    # For each sensor, compute distances to all others
    for sid, group in df.groupby("sensor_id"):
        lat = group["latitude"].iloc[0]
        lon = group["longitude"].iloc[0]

        # Compute distances to all sensors
        distances = df.groupby("sensor_id").apply(
            lambda g: haversine(lat, lon, g["latitude"].iloc[0], g["longitude"].iloc[0])
        )

        # Remove itself
        distances = distances[distances.index != sid]

        # Select 3 nearest
        nearest_ids = distances.nsmallest(3).index.tolist()

        # Compute average lagged PM2.5 from nearest sensors
        neighbor_data = (
            df[df["sensor_id"].isin(nearest_ids)]
            .groupby("datetime")["pm25_lag_1d"]
            .mean()
        )

        aligned = group["datetime"].map(neighbor_data)
        results.append(pd.Series(aligned.values, index=group.index))

    return pd.concat(results).sort_index()