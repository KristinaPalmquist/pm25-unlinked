import pandas as pd
import numpy as np

def add_lagged_features(df, column="pm25", lags=[1, 2, 3]):
    df["sensor_id"] = df["sensor_id"].astype("int32")
    df = df.sort_values(["sensor_id", "date"]).copy()
    for lag in lags:
        df[f"{column}_lag_{lag}d"] = df.groupby("sensor_id")[column].shift(lag)
    return df


def add_rolling_window_feature(df, window_days=3, column="pm25", new_column="pm25_rolling_3d"):
    df["sensor_id"] = df["sensor_id"].astype("int32")
    df = df.sort_values(["sensor_id", "date"]).copy()
    df[new_column] = (
        df.groupby("sensor_id")
          .rolling(f"{window_days}D", on="date")[column]
          .mean()
          .reset_index(level=0, drop=True)
    )
    return df


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (
        np.sin(dlat/2)**2 +
        np.cos(np.radians(lat1)) *
        np.cos(np.radians(lat2)) *
        np.sin(dlon/2)**2
    )
    return 2 * R * np.arcsin(np.sqrt(a))


def add_nearby_sensor_feature(df, metadata_df, n_closest=3):
    df["sensor_id"] = df["sensor_id"].astype("int32")
    df = df.sort_values(["sensor_id", "date"]).copy()

    # Precompute lag
    df["pm25_lag_1d"] = df.groupby("sensor_id")["pm25"].shift(1)

    results = []

    for sid, group in df.groupby("sensor_id"):
        lat = metadata_df.loc[sid, "latitude"]
        lon = metadata_df.loc[sid, "longitude"]

        distances = metadata_df.apply(
            lambda row: haversine(lat, lon, row["latitude"], row["longitude"]),
            axis=1
        )

        distances = distances[distances.index != sid]
        nearest_ids = distances.nsmallest(n_closest).index.tolist()

        neighbor_data = (
            df[df["sensor_id"].isin(nearest_ids)]
            .groupby("date")["pm25_lag_1d"]
            .mean()
        )

        aligned = group["date"].map(neighbor_data)
        results.append(pd.Series(aligned.values, index=group.index))

    df["pm25_nearby_avg"] = pd.concat(results).sort_index()
    return df


# import numpy as np
# from math import radians, cos, sin, asin, sqrt


# def add_rolling_window_feature(df, window_days=3, column="pm25", new_column="pm25_rolling_3d"):
#     df = df.sort_values(["sensor_id", "date"]).copy()
#     df_indexed = df.set_index("date", append=False)

#     df_indexed[f"{column}_shifted"] = df_indexed.groupby("sensor_id")[column].shift(1)
    
#     df[new_column] = (
#         df_indexed.groupby("sensor_id")[f"{column}_shifted"]
#         .rolling(window=f"{window_days}D", min_periods=1)
#         .mean()
#         .reset_index(level=0, drop=True)
#         .values
#     )
#     return df


# def add_lagged_features(df, column="pm25", lags=[1, 2, 3]):
#     df = df.sort_values(["sensor_id", "date"]).copy()
    
#     for lag in lags:
#         new_column = f"{column}_lag_{lag}d"
#         df[new_column] = df.groupby("sensor_id")[column].shift(lag)
#     return df


# def add_nearby_sensor_feature(df, locations, column="pm25_lag_1d", n_closest=3, new_column="pm25_nearby_avg"):
#     """
#     Adds a feature by averaging the specified column from the n_closest sensors.
#     """
#     def haversine(lat1, lon1, lat2, lon2):
#         # Function to calculate the distance between two points on the Earth's surface
#         R = 6371
#         dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
#         a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
#         return 2 * R * asin(sqrt(a))
    
#     closest_map = {}
#     for sid, loc in locations.items():
#         distances = [
#             (oid, haversine(loc['latitude'], loc['longitude'], 
#                            locations[oid]['latitude'], locations[oid]['longitude']))
#             for oid in locations.keys() if oid != sid and 'latitude' in locations[oid]
#         ]
#         closest_map[sid] = [oid for oid, _ in sorted(distances, key=lambda x: x[1])[:n_closest]]
    
#     df = df.copy()
#     df[new_column] = np.nan
    
#     for sensor_id in df['sensor_id'].unique():
#         if sensor_id not in closest_map:
#             continue
#         nearby_ids = closest_map[sensor_id]
#         nearby_data = df[df['sensor_id'].isin(nearby_ids)][['datetime', column]].groupby('datetime')[column].mean()
#         mask = df['sensor_id'] == sensor_id
#         df.loc[mask, new_column] = df.loc[mask, 'datetime'].map(nearby_data)
    
#     return df.sort_values(['sensor_id', 'datetime'])