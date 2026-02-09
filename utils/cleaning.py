import pandas as pd

def clean_and_append_data(df, sensor_id, city=None, street=None, country=None, latitude=None, longitude=None, aqicn_url=None):
    clean_df = pd.DataFrame()

    # PM2.5 extraction
    if "median" in df.columns:
        clean_df["pm25"] = pd.to_numeric(df["median"], errors="coerce")
    elif "pm25" in df.columns:
        clean_df["pm25"] = pd.to_numeric(df["pm25"], errors="coerce")
    else:
        raise ValueError("No 'pm25' or 'median' column found in AQ dataframe")

    clean_df = clean_df.dropna(subset=["pm25"])

    # Timestamp extraction
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

    # Attach sensor_id and metadata
    clean_df["sensor_id"] = int(sensor_id)
    clean_df["city"] = city
    clean_df["street"] = street
    clean_df["country"] = country
    clean_df["latitude"] = latitude
    clean_df["longitude"] = longitude
    clean_df["aqicn_url"] = aqicn_url

    # Final dtype normalization
    clean_df["pm25"] = clean_df["pm25"].astype("float64")
    clean_df["sensor_id"] = clean_df["sensor_id"].astype("int32")

    return clean_df