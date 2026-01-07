import pandas as pd


def clean_and_append_data(df, street, city, country, feed_url, sensor_id):
    """
    Clean AQ data, convert date → datetime, keep pm25, and append metadata.
    """

    clean_df = pd.DataFrame()


    if "date" in df.columns:
        clean_df["datetime"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    elif "datetime" in df.columns:
        clean_df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize(None)
    else:
        raise ValueError("No date or datetime column found in AQ dataframe")

    # PM2.5
    if "median" in df.columns:
        clean_df["pm25"] = df["median"].astype(float)
    elif "pm25" in df.columns:
        clean_df["pm25"] = df["pm25"].astype(float)
    else:
        raise ValueError("No pm25 or median column found in AQ dataframe")


    # # Convert date → datetime
    # clean_df["datetime"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

    # # PM2.5 value
    # clean_df["pm25"] = df["median"].astype(float)

    # Drop rows with missing pm25
    clean_df = clean_df.dropna(subset=["pm25"])

    # Metadata
    clean_df["sensor_id"] = sensor_id
    clean_df["street"] = street
    clean_df["city"] = city
    clean_df["country"] = country
    clean_df["feed_url"] = feed_url

    return clean_df