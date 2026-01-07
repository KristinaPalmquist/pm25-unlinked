import pandas as pd


def clean_and_append_data(df, street, city, country, feed_url, sensor_id):
    """
    Clean AQ data, convert date → datetime, keep pm25, and append metadata.
    """

    clean_df = pd.DataFrame()

    # PM2.5
    if "median" in df.columns:
        clean_df["pm25"] = df["median"].astype(float)
    elif "pm25" in df.columns:
        clean_df["pm25"] = df["pm25"].astype(float)
    else:
        raise ValueError("No pm25 or median column found in AQ dataframe")

    # Drop rows with missing pm25
    clean_df = clean_df.dropna(subset=["pm25"])

    if "date" in df.columns:
        clean_df["date"] = pd.to_datetime(df["date"])
    elif "time" in df.columns:
        clean_df["date"] = pd.to_datetime(df["time"])
    elif "timestamp" in df.columns:
        clean_df["date"] = pd.to_datetime(df["timestamp"])
    else:
        raise KeyError("No date or time column found in AQ dataframe")


    # Metadata
    clean_df["sensor_id"] = sensor_id
    clean_df["street"] = street
    clean_df["city"] = city
    clean_df["country"] = country
    clean_df["feed_url"] = feed_url


    return clean_df