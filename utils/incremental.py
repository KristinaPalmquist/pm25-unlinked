import pandas as pd
from datetime import datetime, timezone, timedelta
import time
from . import fetchers
from . import feature_engineering


def _normalize_timestamp(ts):
    """Convert timestamp to tz-naive datetime for consistent handling."""
    if ts is None:
        return None
    ts = pd.to_datetime(ts)
    if ts.tz is not None:
        ts = ts.tz_localize(None)
    return ts


def process_aq_increment(sensor_id, meta, last_ts, AQICN_API_KEY):
    last_ts = _normalize_timestamp(last_ts)
    
    if last_ts is not None:
        # Make tz-aware (UTC) for time comparison
        last_ts_aware = last_ts.tz_localize("UTC")
        time_since_last = datetime.now(timezone.utc) - last_ts_aware

        if time_since_last < timedelta(minutes=60):
            print(f"⏭️ Sensor {sensor_id}: Last update was {time_since_last.total_seconds()/60:.1f} min ago, skipping")
            return None

    aq_new = fetchers.fetch_latest_aq_data(
        sensor_id=sensor_id,
        feed_url=meta["aqicn_url"],
        since=last_ts,
        AQICN_API_KEY=AQICN_API_KEY
    )

    if aq_new.empty:
        print(f"ℹ️ Sensor {sensor_id}: No new AQ data available")
        return None

    # Standardize datetime
    aq_new["date"] = pd.to_datetime(aq_new["date"], errors="coerce")
    aq_new = aq_new.dropna(subset=["date"])
    aq_new["date"] = aq_new["date"].dt.tz_localize(None)

    # Filter to only new records (last_ts already tz-naive)
    if last_ts is not None:
        aq_new = aq_new[aq_new["date"] > last_ts]

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
    aq_new["location_id"] = int(meta["location_id"])
    aq_new["pm25"] = aq_new["pm25"].astype(float)

    for col in ["pm25_rolling_3d", "pm25_lag_1d", "pm25_lag_2d", "pm25_lag_3d"]:
        if col in aq_new.columns:
            aq_new[col] = aq_new[col].astype(float)

    return aq_new


def _fetch_weather(meta):
    """Fetch latest weather forecast for sensor location."""
    return fetchers.get_latest_weather(
        latitude=meta["latitude"],
        longitude=meta["longitude"],
        since=None  # get_latest_weather always fetches from today onwards
    )


def _clean_weather_df(df):
    """Clean and standardize weather dataframe datetime column."""
    if df is None or df.empty:
        return None

    df = df.copy()
    # Ensure date column is datetime type
    if df["date"].dtype == "object":
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    elif not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    df = df.dropna(subset=["date"])
    
    # Ensure tz-naive
    if df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_localize(None)

    return df


def _finalize_weather_schema(df, location_id, meta):
    """Finalize weather dataframe schema to match feature group."""
    # API now returns correct column names, no renaming needed
    df["location_id"] = int(location_id)

    # Ensure all columns have correct types
    df = df.astype({
        "location_id": "int32",
        "temperature_2m_mean": "float64",
        "precipitation_sum": "float64",
        "wind_speed_10m_max": "float64",
        "wind_direction_10m_dominant": "float64",
    })
    
    # Ensure date is datetime64[ns] (pandas datetime type)
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])

    return df[[
        "date",
        "location_id",
        "temperature_2m_mean",
        "precipitation_sum",
        "wind_speed_10m_max",
        "wind_direction_10m_dominant",
    ]]


def process_weather_increment(sensor_id, meta, last_ts):
    last_ts = _normalize_timestamp(last_ts)
    
    # Skip if updated recently
    if last_ts is not None:
        # Make tz-aware (UTC) for time comparison
        last_ts_aware = last_ts.tz_localize("UTC")
        time_since_last = datetime.now(timezone.utc) - last_ts_aware
        if time_since_last < timedelta(hours=1):
            print(f"⏭️ Sensor {sensor_id}: Weather updated {time_since_last.total_seconds()/3600:.1f} hours ago, skipping")
            return None

    # Fetch raw weather forecast
    weather_new = _fetch_weather(meta)
    if weather_new is None or weather_new.empty:
        print(f"ℹ️ Sensor {sensor_id}: No new weather data available")
        return None

    # Clean + standardize
    weather_new = _clean_weather_df(weather_new)

    if weather_new is None or weather_new.empty:
        print(f"ℹ️ Sensor {sensor_id}: Weather data invalid or empty after cleaning")
        return None

    # Filter to only new records (last_ts already tz-naive)
    if last_ts is not None:
        weather_new = weather_new[weather_new["date"] > last_ts]

    if weather_new.empty:
        print(f"ℹ️ Sensor {sensor_id}: No weather newer than last_ts")
        return None

    print(f"✅ Sensor {sensor_id}: Found {len(weather_new)} new weather records")

    return _finalize_weather_schema(weather_new, meta["location_id"], meta)


def run_incremental_update(sensor_metadata_fg, air_quality_fg, weather_fg, latest_per_sensor, AQICN_API_KEY):
    """
    Update all sensors with new data if >1 hour since last update.
    Each sensor is processed and inserted independently with retry logic.
    """
    metadata_df = sensor_metadata_fg.read()

    if metadata_df.empty:
        print("⏭️ No sensors configured — skipping incremental update")
        return
    
    metadata_df["sensor_id"] = metadata_df["sensor_id"].astype(int)
    metadata_indexed = metadata_df.set_index("sensor_id")

    updated_count = 0
    skipped_count = 0
    failed_count = 0
    failed_sensors = []

    for sensor_id, meta in metadata_indexed.iterrows():
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                last_ts = latest_per_sensor.get(sensor_id)

                aq_new = process_aq_increment(sensor_id, meta, last_ts, AQICN_API_KEY)
                if aq_new is None or aq_new.empty:
                    skipped_count += 1
                    break  # No retry needed, just skip
                
                # Add nearby sensor features for this sensor's data
                aq_new = feature_engineering.add_nearby_sensor_feature(
                    aq_new,
                    metadata_indexed,
                    n_closest=3
                )
                aq_new["sensor_id"] = aq_new["sensor_id"].astype("int32")
                aq_new["location_id"] = aq_new["location_id"].astype("int32")
                
                # Insert air quality data immediately
                air_quality_fg.insert(aq_new)
                
                # Process and insert weather data
                weather_new = process_weather_increment(sensor_id, meta, last_ts)
                if weather_new is not None and not weather_new.empty:
                    weather_fg.insert(weather_new)
                
                updated_count += 1
                break  # Success, exit retry loop
                
            except (ConnectionError, TimeoutError, Exception) as e:
                error_type = type(e).__name__
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
                    print(f"⚠️  Sensor {sensor_id}: {error_type}, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    failed_count += 1
                    failed_sensors.append((sensor_id, error_type))
                    print(f"❌ Sensor {sensor_id}: Failed after {max_retries} attempts - {error_type}")
                    break
        
        # Brief pause between sensors to avoid rate limiting
        time.sleep(1)

    print(f"\n✅ Incremental update complete!")
    print(f"   Updated: {updated_count}, Skipped: {skipped_count}, Failed: {failed_count}")
    
    if failed_sensors:
        print(f"\n⚠️  Failed sensors:")
        for sid, error in failed_sensors:
            print(f"   • Sensor {sid}: {error}")