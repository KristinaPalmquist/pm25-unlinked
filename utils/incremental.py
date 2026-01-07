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
    aq_new["datetime"] = pd.to_datetime(aq_new["datetime"], errors="coerce")
    aq_new = aq_new.dropna(subset=["datetime"])
    aq_new["datetime"] = aq_new["datetime"].dt.tz_localize(None)

    # Incremental filtering
    if last_ts is not None:
        last_ts_naive = last_ts.replace(tzinfo=None) if last_ts.tzinfo else last_ts
        aq_new = aq_new[aq_new["datetime"] > last_ts_naive]

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

    # Clean schema
    aq_new = aq_new.drop(columns=["aqicn_url"], errors="ignore")
    aq_new["sensor_id"] = int(sensor_id)
    aq_new["pm25"] = aq_new["pm25"].astype(float)

    for col in ["pm25_rolling_3d", "pm25_lag_1d", "pm25_lag_2d", "pm25_lag_3d"]:
        if col in aq_new.columns:
            aq_new[col] = aq_new[col].astype(float)

    return aq_new


def process_weather_increment(sensor_id, meta, last_ts):
    # Skip if updated in the last 24 hours
    if last_ts is not None:
        time_since_last = datetime.now(timezone.utc) - last_ts.replace(tzinfo=timezone.utc)
        if time_since_last < timedelta(minutes=60):
            print(f"⏭️ Sensor {sensor_id}: Weather updated {time_since_last.total_seconds()/3600:.1f} hours ago, skipping")
            return None
    
    weather_new = fetchers.get_latest_weather(
        latitude=meta["latitude"],
        longitude=meta["longitude"],
        since=last_ts
    )

    if weather_new.empty:
        print(f"ℹ️ Sensor {sensor_id}: No new weather data available")
        return None

    # Standardize datetime
    weather_new["datetime"] = pd.to_datetime(weather_new["datetime"], errors="coerce")
    weather_new = weather_new.dropna(subset=["datetime"])
    weather_new["datetime"] = weather_new["datetime"].dt.tz_localize(None)

    # Incremental filtering
    if last_ts is not None:
        last_ts_naive = last_ts.replace(tzinfo=None) if last_ts.tzinfo else last_ts
        weather_new = weather_new[weather_new["datetime"] > last_ts_naive]

    if weather_new.empty:
        print(f"ℹ️ Sensor {sensor_id}: Weather data filtered out (older than last_ts)")
        return None

    print(f"✅ Sensor {sensor_id}: Found {len(weather_new)} new weather records")

    # Rename to match feature group schema
    weather_new = weather_new.rename(columns={
        "temperature_2m": "temperature_2m_mean",
        "wind_speed_10m": "wind_speed_10m_max",
        "wind_direction_10m": "wind_direction_10m_dominant",
    })

    # Ensure required columns exist
    weather_new["precipitation_sum"] = weather_new.get("precipitation_sum", 0.0)
    weather_new["wind_direction_10m_dominant"] = weather_new.get(
        "wind_direction_10m_dominant", 0.0
    )

    # Add metadata
    weather_new["sensor_id"] = int(sensor_id)
    weather_new["city"] = meta["city"]
    weather_new["latitude"] = meta["latitude"]
    weather_new["longitude"] = meta["longitude"]

    # Cast types
    weather_new = weather_new.astype({
        "sensor_id": "int64",
        "latitude": "float64",
        "longitude": "float64",
        "temperature_2m_mean": "float64",
        "precipitation_sum": "float64",
        "wind_speed_10m_max": "float64",
        "wind_direction_10m_dominant": "float64",
    })

    # Final schema
    weather_new = weather_new[[
        "sensor_id",
        "datetime",
        "temperature_2m_mean",
        "precipitation_sum",
        "wind_speed_10m_max",
        "wind_direction_10m_dominant",
        "city",
        "latitude",
        "longitude",
    ]]

    return weather_new


def run_incremental_update(
    sensor_metadata_fg,
    air_quality_fg,
    weather_fg,
    latest_per_sensor
):
    metadata_df = sensor_metadata_fg.read().set_index("sensor_id")

    locations = {
        sid: {
            "latitude": row["latitude"],
            "longitude": row["longitude"]
        }
        for sid, row in metadata_df.iterrows()
    }

    if metadata_df.empty:
        print("⏭️ Skipping incremental updates - no sensors configured yet")
        return

    now = datetime.now(timezone.utc)
    min_update_interval = pd.Timedelta(hours=1)
    
    updated_count = 0
    
    for sensor_id, meta in metadata_df.iterrows():
        last_ts = latest_per_sensor.get(sensor_id)
        
        # Skip if recently updated
        if last_ts is not None:
            time_since_update = now - last_ts.replace(tzinfo=timezone.utc)
            if time_since_update < min_update_interval:
                print(f"⏭️ Skipping sensor {sensor_id} - updated {time_since_update.total_seconds()/60:.1f} minutes ago")
                continue

        aq_new = process_aq_increment(sensor_id, meta, last_ts)

        # Only proceed if there is new AQ data
        if not aq_new.empty:

            # AQ update
            aq_new["city"] = meta["city"]
            aq_new["country"] = meta["country"]
            aq_new["feed_url"] = meta["feed_url"]
            air_quality_fg.insert(aq_new)
            updated_count += 1

            # Weather update
            weather_new = process_weather_increment(sensor_id, meta, last_ts)
            if not weather_new.empty:
                weather_fg.insert(weather_new)
        
        time.sleep(1) # Rate limiting - 1 second between sensors

    print(f"✅ Incremental update complete. Updated {updated_count} sensors.")