import pandas as pd
from datetime import datetime, timezone, timedelta
import time
from . import fetchers
from . import feature_engineering


def process_aq_increment(sensor_id, meta, last_ts):
    if last_ts is not None:
        time_since_last = datetime.now(timezone.utc) - last_ts.replace(tzinfo=timezone.utc)
        if time_since_last < timedelta(minutes=60):
            print(f"⏭️ Sensor {sensor_id}: Last update was {time_since_last.total_seconds()/60:.1f} min ago, skipping")
            return None
        
    aq_new = fetchers.fetch_latest_aq_data(
        sensor_id=sensor_id,
        feed_url=meta["aqicn_url"],
        since=last_ts
    )

    if aq_new.empty:
        print(f"ℹ️ Sensor {sensor_id}: No new AQ data available")
        return None

    # Standardize datetime
    aq_new["date"] = pd.to_datetime(aq_new["date"], errors="coerce")
    aq_new = aq_new.dropna(subset=["date"])
    aq_new["date"] = aq_new["date"].dt.tz_localize(None)

    # Incremental filtering
    if last_ts is not None:
        last_ts_naive = last_ts.replace(tzinfo=None) if last_ts.tzinfo else last_ts
        aq_new = aq_new[aq_new["date"] > last_ts_naive]

    if aq_new.empty:
        print(f"ℹ️ Sensor {sensor_id}: Data filtered out (older than last_ts)")
        return None
    
    print(f"✅ Sensor {sensor_id}: Found {len(aq_new)} new AQ records")


    # Feature engineering
    aq_new = feature_engineering.add_rolling_window_feature(
        aq_new, window_days=3, column="pm25", new_column="pm25_rolling_3d"
    )
    aq_new = feature_engineering.add_lagged_features(
        aq_new, column="pm25", lags=[1, 2, 3]
    )
    aq_new["pm25_nearby_avg"] = None

    # Clean schema
    aq_new = aq_new.drop(columns=["aqicn_url"], errors="ignore")
    aq_new["sensor_id"] = int(sensor_id)
    aq_new["pm25"] = aq_new["pm25"].astype(float)

    for col in ["pm25_rolling_3d", "pm25_lag_1d", "pm25_lag_2d", "pm25_lag_3d"]:
        if col in aq_new.columns:
            aq_new[col] = aq_new[col].astype(float)

    return aq_new


def _weather_start_date(last_ts):
    """Return the correct start date string for the weather API."""
    if last_ts is None:
        # First run → fetch today's weather only
        return datetime.now(timezone.utc).date().isoformat()
    return last_ts.date().isoformat()


def _fetch_weather(meta, start_date):
    return fetchers.get_latest_weather(
        latitude=meta["latitude"],
        longitude=meta["longitude"],
        since=start_date
    )


def _clean_weather_df(df):
    if df is None or df.empty:
        return None

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["date"] = df["date"].dt.tz_localize(None)

    return df


def _finalize_weather_schema(df, sensor_id, meta):
    df = df.rename(columns={
        "temperature_2m": "temperature_2m_mean",
        "wind_speed_10m": "wind_speed_10m_max",
        "wind_direction_10m": "wind_direction_10m_dominant",
    })

    df["precipitation_sum"] = df.get("precipitation_sum", 0.0)
    df["wind_direction_10m_dominant"] = df.get("wind_direction_10m_dominant", 0.0)

    df["sensor_id"] = int(sensor_id)
    df["city"] = meta["city"]
    df["latitude"] = meta["latitude"]
    df["longitude"] = meta["longitude"]

    df = df.astype({
        "sensor_id": "int64",
        "latitude": "float64",
        "longitude": "float64",
        "temperature_2m_mean": "float64",
        "precipitation_sum": "float64",
        "wind_speed_10m_max": "float64",
        "wind_direction_10m_dominant": "float64",
    })

    return df[[
        "sensor_id",
        "date",
        "temperature_2m_mean",
        "precipitation_sum",
        "wind_speed_10m_max",
        "wind_direction_10m_dominant",
        "city",
        "latitude",
        "longitude",
    ]]


def process_weather_increment(sensor_id, meta, last_ts):
    # Skip if updated recently
    if last_ts is not None:
        time_since_last = datetime.now(timezone.utc) - last_ts.replace(tzinfo=timezone.utc)
        if time_since_last < timedelta(hours=1):
            print(f"⏭️ Sensor {sensor_id}: Weather updated {time_since_last.total_seconds()/3600:.1f} hours ago, skipping")
            return None

    # Determine start date safely
    start_date = _weather_start_date(last_ts)

    # Fetch raw weather
    weather_new = _fetch_weather(meta, start_date)
    if weather_new is None or weather_new.empty:
        print(f"ℹ️ Sensor {sensor_id}: No new weather data available")
        return None

    # Clean + standardize
    weather_new = _clean_weather_df(weather_new)
    if weather_new is None or weather_new.empty:
        print(f"ℹ️ Sensor {sensor_id}: Weather data invalid or empty after cleaning")
        return None

    # Filter incremental rows
    if last_ts is not None:
        last_ts_naive = last_ts.replace(tzinfo=None) if last_ts.tzinfo else last_ts
        weather_new = weather_new[weather_new["date"] > last_ts_naive]

    if weather_new.empty:
        print(f"ℹ️ Sensor {sensor_id}: No weather newer than last_ts")
        return None

    print(f"✅ Sensor {sensor_id}: Found {len(weather_new)} new weather records")

    return _finalize_weather_schema(weather_new, sensor_id, meta)


def run_incremental_update(sensor_metadata_fg, air_quality_fg, weather_fg, latest_per_sensor):
    """
    Update all sensors with new data if >24 hours since last update.
    """
    metadata_df = sensor_metadata_fg.read().set_index("sensor_id")

    if metadata_df.empty:
        print("⏭️ No sensors configured — skipping incremental update")
        return
    
    locations = {}
    for sensor_id, row in metadata_df.iterrows():
        locations[sensor_id] = {
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "city": row["city"],
            "country": row["country"],
            "street": row["street"],
            "aqicn_url": row["aqicn_url"],
        }

    # now = datetime.now(timezone.utc)
    # min_update_interval = pd.Timedelta(hours=1)
    updated_count = 0
    all_new_aq = []

    for sensor_id, meta in metadata_df.iterrows():
        last_ts = latest_per_sensor.get(sensor_id)

        # if last_ts is not None:
        #     if now - last_ts.replace(tzinfo=timezone.utc) < min_update_interval:
        #         continue

        aq_new = process_aq_increment(sensor_id, meta, last_ts)
        if aq_new is not None and not aq_new.empty:
            all_new_aq.append(aq_new)
            updated_count += 1

            weather_new = process_weather_increment(sensor_id, meta, last_ts)
            if weather_new is not None and not weather_new.empty:
                weather_fg.insert(weather_new)

        time.sleep(1)

    if all_new_aq:
            combined_aq = pd.concat(all_new_aq, ignore_index=True)
            combined_aq = feature_engineering.add_nearby_sensor_feature(
                combined_aq,
                locations,
                column="pm25_lag_1d",
                n_closest=3
            )
            air_quality_fg.insert(combined_aq)

    print(f"✅ Incremental update complete. Updated {updated_count} sensors.")