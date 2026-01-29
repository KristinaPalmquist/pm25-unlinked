import pandas as pd
import requests
from utils import fetchers

# Cache for geocoding results to avoid duplicate API calls
_geocoding_cache = {}


def get_sensor_locations(feature_group):
    """
    Extract sensor location metadata from air quality feature group.
    
    Returns dict: {sensor_id: (latitude, longitude, city, street, country)}
    
    This centralizes the repeated pattern of reading metadata from the feature group
    that appears in all pipelines.
    """
    try:
        df = feature_group.read()
        if df.empty:
            print("ℹ️  Feature group is empty (first run) - starting fresh backfill")
            return {}
        
        # Extract unique sensor metadata
        metadata_df = df[["sensor_id", "latitude", "longitude", "city", "street", "country"]].drop_duplicates(subset=["sensor_id"])
        
        # Build location dictionary
        locations = {}
        for _, row in metadata_df.iterrows():
            locations[row["sensor_id"]] = (
                row["latitude"],
                row["longitude"],
                row["city"],
                row["street"],
                row["country"]
            )
        
        return locations
    
    except Exception as e:
        # If feature group has no data (first run), this is expected
        error_msg = str(e)
        if "No data found" in error_msg:
            print("ℹ️  Feature group is empty (first run) - starting fresh backfill")
        else:
            print(f"⚠️  Error loading sensor locations: {e}")
        return {}


def get_sensor_locations_dict(feature_group):
    """
    Extract sensor location metadata as nested dictionaries (for pipeline 2).
    
    Returns dict: {sensor_id: {"latitude": ..., "longitude": ..., "city": ..., etc}}
    """
    try:
        df = feature_group.read()
        if df.empty:
            print("ℹ️  Feature group is empty - no sensor locations available")
            return {}
        
        metadata_df = df[["sensor_id", "latitude", "longitude", "city", "street", "country", "aqicn_url"]].drop_duplicates(subset=["sensor_id"])
        
        locations = {}
        for _, row in metadata_df.iterrows():
            locations[row["sensor_id"]] = {
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "city": row["city"],
                "street": row["street"],
                "country": row["country"],
                "aqicn_url": row["aqicn_url"]
            }
        
        return locations
    
    except Exception as e:
        print(f"⚠️ Error loading sensor locations: {e}")
        return {}

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
        # Check cache first
        if query in _geocoding_cache:
            return _geocoding_cache[query]
        
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": query, "count": 1, "language": "en"}

        try:
            r = requests.get(url, params=params, timeout=5)
            data = r.json()

            if "results" in data and len(data["results"]) > 0:
                result = data["results"][0]
                coords = (result["latitude"], result["longitude"])
                _geocoding_cache[query] = coords
                return coords
        except Exception:
            pass

    _geocoding_cache[query] = (None, None)
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

def validate_coordinates(lat, lon):
    return lat is not None and lon is not None

# def build_metadata_from_csvs(data_dir, aqicn_api_key):
#     rows = []

#     for file in os.listdir(data_dir):
#         if not file.endswith(".csv"):
#             continue

#         file_path = os.path.join(data_dir, file)

#         aq_df_raw, street, city, country, feed_url, sensor_id = read_sensor_data(
#             file_path, aqicn_api_key
#         )

#         # Clean fields
#         street = clean_field(street)
#         city = clean_field(city)
#         country = clean_field(country)

#         # Geocode
#         lat, lon = get_coordinates(city, street, country)

#         if not validate_coordinates(lat, lon):
#             print(f"[SKIP] Sensor {sensor_id}: cannot geocode location")
#             continue

#         rows.append({
#             "sensor_id": sensor_id,
#             "city": city,
#             "street": street,
#             "country": country,
#             "aqicn_url": feed_url,
#             "latitude": lat,
#             "longitude": lon,
#         })

#     return pd.DataFrame(rows)


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
