import os
import pandas as pd
import requests
from not_needed_files import airquality
from utils import fetchers


def get_coordinates(city, street, country):
    candidates = []

    # Most specific → least specific
    if street and city:
        candidates.append(f"{street}, {city}, {country}")
    if city:
        candidates.append(f"{city}, {country}")
    if street:
        candidates.append(f"{street}, {country}")
    if country:
        candidates.append(country)

    for query in candidates:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": query, "count": 1, "language": "en"}

        try:
            r = requests.get(url, params=params, timeout=5)
            data = r.json()

            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                return result["latitude"], result["longitude"]
        except Exception:
            pass

    return None, None


def clean_field(value):
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    value = str(value).strip()
    if value.lower() in ("none", "nan", "", "unknown"):
        return None
    return value

def validate_aqicn_feed(feed_url):
    try:
        r = requests.get(feed_url)
        data = r.json()
        return data.get("status") == "ok"
    except:
        return False
    
def validate_coordinates(lat, lon):
    return lat is not None and lon is not None

def build_metadata_from_csvs(data_dir, aqicn_api_key):
    rows = []

    for file in os.listdir(data_dir):
        if not file.endswith(".csv"):
            continue

        file_path = os.path.join(data_dir, file)

        aq_df_raw, street, city, country, feed_url, sensor_id = read_sensor_data(
            file_path, aqicn_api_key
        )

        # Clean fields
        street = clean_field(street)
        city = clean_field(city)
        country = clean_field(country)

        # Validate feed URL
        if not validate_aqicn_feed(feed_url):
            print(f"[SKIP] Sensor {sensor_id}: invalid AQICN feed")
            continue

        # Geocode
        lat, lon = get_coordinates(city, street, country)

        if not validate_coordinates(lat, lon):
            print(f"[SKIP] Sensor {sensor_id}: cannot geocode location")
            continue

        rows.append({
            "sensor_id": sensor_id,
            "city": city,
            "street": street,
            "country": country,
            "aqicn_url": feed_url,
            "latitude": lat,
            "longitude": lon,
        })

    return pd.DataFrame(rows)


def read_sensor_data(file_path, aqicn_api_key):
    """
    Reads the sensor data from the CSV file. The first three rows contain metadata.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        # Parse location
        location_parts = [
            s.strip()
            for s in f.readline()
            .strip()
            .lstrip("# Sensor ")
            .split("(")[0]
            .strip()
            .split(",")
        ]

        if len(location_parts) == 3:
            street, city, country = location_parts
        elif len(location_parts) == 2:
            street, country = location_parts
            city = street
        else:
            raise ValueError(f"Unexpected location format: {location_parts}")

        url_line = f.readline().strip().lstrip("# ").strip()
        sensor_id = url_line.split("@")[1].split("/")[0]

        _ = f.readline().strip()

    df = pd.read_csv(file_path, skiprows=3)

    feed_url = fetchers.get_working_feed_url(sensor_id, aqicn_api_key)

    return df, street, city, country, feed_url, sensor_id
