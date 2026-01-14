import pandas as pd

def clean_and_append_data(df, sensor_id):
    """
    Clean AQ data:
    - extract pm25 (from 'median' or 'pm25')
    - extract timestamp (from 'date', 'time', or 'timestamp')
    - drop missing values
    - attach sensor_id
    Returns a dataframe ready for air_quality_fg insertion.
    """

    clean_df = pd.DataFrame()

    # --- PM2.5 extraction ---
    if "median" in df.columns:
        clean_df["pm25"] = pd.to_numeric(df["median"], errors="coerce")
    elif "pm25" in df.columns:
        clean_df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")
    else:
        raise ValueError("No 'pm25' or 'median' column found in AQ dataframe")

    clean_df = clean_df.dropna(subset=["pm25"])

    # --- Timestamp extraction ---
    if "date" in df.columns:
        ts = df["date"]
    elif "time" in df.columns:
        ts = df["time"]
    elif "timestamp" in df.columns:
        ts = df["timestamp"]
    else:
        raise KeyError("No date/time column found in AQ dataframe")

    clean_df["date"] = pd.to_datetime(ts, errors="coerce")
    clean_df = clean_df.dropna(subset=["date"])

    # --- Attach sensor_id ---
    clean_df["sensor_id"] = int(sensor_id)

    # --- Final dtype normalization ---
    clean_df["pm25"] = clean_df["pm25"].astype("float64")
    clean_df["sensor_id"] = clean_df["sensor_id"].astype("int32")
    # aq_columns = [f.name for f in df.features]
    # clean_df = clean_df[aq_columns].astype({
    #         "sensor_id": "int32",
    #         "location_id": "int32",
    #         "pm25": "float64",
    #         "pm25_lag_1d": "float64",
    #         "pm25_lag_2d": "float64",
    #         "pm25_lag_3d": "float64",
    #         "pm25_rolling_3d": "float64",
    #         "pm25_nearby_avg": "float64",
    #     })

    return clean_df