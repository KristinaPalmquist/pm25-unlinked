import os
import pandas as pd
from geopy.geocoders import Nominatim
from utils import airquality

geolocator = Nominatim(user_agent="pm25-metadata-builder")

def get_coordinates(city, street, country):
    """Geocode a sensor location with fallbacks."""
    candidates = []
    if street and city:
        candidates.append(f"{street}, {city}, {country}")
    if city:
        candidates.append(f"{city}, {country}")
    if street:
        candidates.append(f"{street}, {country}")
    candidates.append(country)

    for query in candidates:
        loc = geolocator.geocode(query)
        if loc:
            return loc.latitude, loc.longitude

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


def build_metadata_from_csvs(data_dir, aqicn_api_key):
    rows = []

    for file in os.listdir(data_dir):
        if not file.endswith(".csv"):
            continue

        file_path = os.path.join(data_dir, file)

        aq_df_raw, street, city, country, feed_url, sensor_id = airquality.read_sensor_data(
            file_path, aqicn_api_key
        )

        # Clean fields
        street = clean_field(street)
        city = clean_field(city)
        country = clean_field(country)

        # Geocode with fallbacks
        lat, lon = get_coordinates(city, street, country)

        if lat is None or lon is None:
            print(f"[WARN] Could not geocode sensor {sensor_id} ({street}, {city}, {country})")
            continue  # or keep it but mark as invalid?

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