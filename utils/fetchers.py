import requests
import requests_cache
import openmeteo_requests
import pandas as pd
import json
from retry_requests import retry
import time
from datetime import datetime, timedelta
from threading import Lock


""" Global rate limiting helper """
LAST_REQUEST_TIME = 0
RATE_LIMIT_SECONDS = 1.5   # 1 request every 1.5 seconds ≈ 40 per minute
LOCK = Lock()

def rate_limited_request():
    global LAST_REQUEST_TIME
    with LOCK:
        now = time.time()
        elapsed = now - LAST_REQUEST_TIME
        if elapsed < RATE_LIMIT_SECONDS:
            time.sleep(RATE_LIMIT_SECONDS - elapsed)
        LAST_REQUEST_TIME = time.time()


""" HTTP request trigger function """
def trigger_request(url:str):
    response = requests.get(url)
    if response.status_code == 200:
        # Extract the JSON content from the response
        data = response.json()
    else:
        print("Failed to retrieve data. Status Code:", response.status_code)
        raise requests.exceptions.RequestException(response.status_code)

    return data


""" Weather data helpers """
def get_historical_weather(sensor_id, start_date, end_date, latitude, longitude):
    # Setup Open-Meteo client with caching + retry
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Convert to datetime
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    # Generate monthly chunks
    chunks = pd.date_range(start=start_dt, end=end_dt, freq="MS").tolist()
    chunks.append(end_dt)

    all_frames = []

    for i in range(len(chunks) - 1):
        chunk_start = chunks[i].strftime("%Y-%m-%d")
        chunk_end = chunks[i+1].strftime("%Y-%m-%d")

        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": chunk_start,
            "end_date": chunk_end,
            "daily": [
                "temperature_2m_mean",
                "precipitation_sum",
                "wind_speed_10m_max",
                "wind_direction_10m_dominant"
            ],
            "timezone": "UTC"
        }

        rate_limited_request()
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        daily = response.Daily()
        df = pd.DataFrame({
            "date": pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s"),
                end=pd.to_datetime(daily.TimeEnd(), unit="s"),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            ),
            "temperature_2m_mean": daily.Variables(0).ValuesAsNumpy(),
            "precipitation_sum": daily.Variables(1).ValuesAsNumpy(),
            "wind_speed_10m_max": daily.Variables(2).ValuesAsNumpy(),
            "wind_direction_10m_dominant": daily.Variables(3).ValuesAsNumpy(),
        })

        df["sensor_id"] = sensor_id
        df = df.dropna()

        df = df.astype({
            "temperature_2m_mean": "float64",
            "precipitation_sum": "float64",
            "wind_speed_10m_max": "float64",
            "wind_direction_10m_dominant": "float64",
        })

        all_frames.append(df)
        
        time.sleep(0.3)   # 300 ms pause between requests


    if not all_frames:
        return pd.DataFrame()

    return pd.concat(all_frames, ignore_index=True)


# def get_hourly_weather_forecast(city, latitude, longitude):
#     # Setup the Open-Meteo API client with cache and retry on error
#     cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
#     retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
#     openmeteo = openmeteo_requests.Client(session = retry_session)

#     # Make sure all required weather variables are listed here
#     # The order of variables in hourly or daily is important to assign them correctly below
#     url = "https://api.open-meteo.com/v1/forecast"
#     params = {
#         "latitude": latitude,
#         "longitude": longitude,
#         "hourly": ["temperature_2m", "precipitation", "wind_speed_10m", "wind_direction_10m"],
#         "forecast_days": 7
#     }
#     responses = openmeteo.weather_api(url, params=params)

#     # Process first location. Add a for-loop for multiple locations or weather models
#     response = responses[0]

#     # Process hourly data. The order of variables needs to be the same as requested.

#     hourly = response.Hourly()
#     hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
#     hourly_precipitation = hourly.Variables(1).ValuesAsNumpy()
#     hourly_wind_speed_10m = hourly.Variables(2).ValuesAsNumpy()
#     hourly_wind_direction_10m = hourly.Variables(3).ValuesAsNumpy()

#     hourly_data = {"date": pd.date_range(
#         start = pd.to_datetime(hourly.Time(), unit = "s"),
#         end = pd.to_datetime(hourly.TimeEnd(), unit = "s"),
#         freq = pd.Timedelta(seconds = hourly.Interval()),
#         inclusive = "left"
#     )}
#     hourly_data["temperature_2m_mean"] = hourly_temperature_2m
#     hourly_data["precipitation_sum"] = hourly_precipitation
#     hourly_data["wind_speed_10m_max"] = hourly_wind_speed_10m
#     hourly_data["wind_direction_10m_dominant"] = hourly_wind_direction_10m

#     hourly_dataframe = pd.DataFrame(data = hourly_data)
#     hourly_dataframe = hourly_dataframe.dropna()
#     return hourly_dataframe


def get_weather_forecast(sensor_id, start_date, end_date, latitude, longitude):
    """
    Fetch weather forecast for 7 days ahead using Open-Meteo forecast API.
    """
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date),
        "end_date": end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date),
        "daily": [
            "temperature_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_max",
            "wind_direction_10m_dominant"
        ],
        "timezone": "UTC"
    }

    rate_limited_request()
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    daily = response.Daily()
    df = pd.DataFrame({
        "date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s"),
            end=pd.to_datetime(daily.TimeEnd(), unit="s"),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left"
        ),
        "temperature_2m_mean": daily.Variables(0).ValuesAsNumpy(),
        "precipitation_sum": daily.Variables(1).ValuesAsNumpy(),
        "wind_speed_10m_max": daily.Variables(2).ValuesAsNumpy(),
        "wind_direction_10m_dominant": daily.Variables(3).ValuesAsNumpy(),
    })

    df["sensor_id"] = sensor_id
    return df.dropna()


# def fetch_data_for_sensor(sensor_id, meta, today, AQICN_API_KEY):
#     """Fetch air quality and weather data for a single sensor."""
#     country = meta["country"]
#     city = meta["city"]
#     street = meta["street"]
#     aqicn_url = meta["aqicn_url"]
#     latitude = meta["latitude"]
#     longitude = meta["longitude"]

#     # Fetch current air quality
#     aq_today_df = get_pm25(aqicn_url, country, city, street, today, AQICN_API_KEY)
    
#     # Fetch weather forecast (7 days forward)
#     end_date = today + timedelta(days=7)
#     weather_df = get_weather_forecast(sensor_id, today, end_date, latitude, longitude)
    
#     return aq_today_df, weather_df, sensor_id


def get_latest_weather(latitude: float, longitude: float, since: datetime):
    """
    Fetch only new weather rows since the last datetime.
    Uses forecast API, so always fetches from today onwards (not historical data).
    """
    # Forecast API only works for today and future dates
    # Always use today as start_date, regardless of 'since' parameter
    today = datetime.utcnow().date()
    start_date = today.isoformat()
    # Fetch 7 days ahead
    end_date = (today + timedelta(days=7)).isoformat()

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": [
            "temperature_2m_mean",
            "precipitation_sum",
            "wind_speed_10m_max",
            "wind_direction_10m_dominant"
        ],
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "UTC"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # Convert to dataframe (daily data, not hourly)
    daily = data.get("daily", {})
    if not daily:
        return pd.DataFrame()

    df = pd.DataFrame(daily)

    # Rename time column to date
    df = df.rename(columns={"time": "date"})
    df = df.dropna(subset=["date"])

    return df 


""" Air Quality Sensor helpers """

def get_working_feed_url(sensor_id, AQICN_API_KEY):
    """
    Try to resolve a working feed URL for the sensor.
    Tests both @ and A formats.
    Returns the working feed_url or raises ValueError if none works.
    """
    feed_url_at = f"https://api.waqi.info/feed/@{sensor_id}/"
    feed_url_a = f"https://api.waqi.info/feed/A{sensor_id}/"
    urls_to_try = [feed_url_at, feed_url_a]

    error_details = []

    for feed_url in urls_to_try:
        try:
            response = requests.get(f"{feed_url}?token={AQICN_API_KEY}")
            response.raise_for_status()
            data = response.json()

            if "data" not in data:
                error_details.append(f"{feed_url}: Missing 'data' field")
                continue

            if isinstance(data["data"], str):
                error_details.append(f"{feed_url}: API error - {data['data']}")
                continue

            if "city" not in data["data"]:
                error_details.append(f"{feed_url}: Missing 'city' field")
                continue

            if "geo" not in data["data"]["city"]:
                error_details.append(f"{feed_url}: Missing 'geo' coordinates")
                continue

            return f"{feed_url}"
            # return f"{feed_url}?token={AQICN_API_KEY}"
        

        except requests.exceptions.RequestException as e:
            error_details.append(f"{feed_url}: HTTP error - {e}")
        except json.JSONDecodeError as e:
            error_details.append(f"{feed_url}: Invalid JSON - {e}")
        except Exception as e:
            error_details.append(f"{feed_url}: Unexpected error - {e}")

    detailed_errors = "; ".join(error_details)
    raise ValueError(f"Failed to resolve feed URL for sensor {sensor_id}. Details: {detailed_errors}")


# def get_sensor_coordinates(feed_url, sensor_id, AQICN_API_KEY):
#     response = requests.get(f"{feed_url}?token={AQICN_API_KEY}")
#     data = response.json()
#     latitude = data["data"]["city"]["geo"][0]
#     longitude = data["data"]["city"]["geo"][1]
#     return latitude, longitude

    
def get_pm25(aqicn_url: str, country: str, city: str, street: str, day: datetime.date, AQI_API_KEY: str):
    """
    Returns DataFrame with air quality (pm25) as dataframe
    """
    # The API endpoint URL
    url = f"{aqicn_url}/?token={AQI_API_KEY}"

    # Make a GET request to fetch the data from the API
    data = trigger_request(url)

    # if we get 'Unknown station' response then retry with city in url
    if data['data'] == "Unknown station":
        url1 = f"https://api.waqi.info/feed/{country}/{street}/?token={AQI_API_KEY}"
        data = trigger_request(url1)

    if data['data'] == "Unknown station":
        url2 = f"https://api.waqi.info/feed/{country}/{city}/{street}/?token={AQI_API_KEY}"
        data = trigger_request(url2)


    # Check if the API response contains the data
    if data['status'] == 'ok':
        # Extract the air quality data
        aqi_data = data['data']
        aq_today_df = pd.DataFrame()
        
        # Check if iaqi field exists and contains pm25 data
        pm25_value = None
        if 'iaqi' in aqi_data and isinstance(aqi_data['iaqi'], dict):
            pm25_value = aqi_data['iaqi'].get('pm25', {}).get('v', None)
        
        aq_today_df['pm25'] = [pm25_value]
        aq_today_df['pm25'] = aq_today_df['pm25'].astype('float32')

        aq_today_df['country'] = country
        aq_today_df['city'] = city
        aq_today_df['street'] = street
        aq_today_df['date'] = day
        aq_today_df['date'] = pd.to_datetime(aq_today_df['date'])
        aq_today_df['url'] = aqicn_url
    else:
        print("Error: There may be an incorrect URL for your Sensor or it is not contactable right now. The API response does not contain data.  Error message:", data['data'])
        raise requests.exceptions.RequestException(data['data'])

    return aq_today_df

def fetch_latest_aq_data(sensor_id: str, feed_url: str, since: datetime, AQICN_API_KEY: str):
    """
    Fetch only new AQ measurements for a sensor since the last datetime.
    """

    if since is None:
        since = pd.Timestamp.min
    else:
        since = pd.to_datetime(since)
        if since.tz is not None:
            since = since.tz_localize(None)

    response = requests.get(f"{feed_url}?token={AQICN_API_KEY}")
    response.raise_for_status()
    data = response.json()

    # Extract timestamp
    try:
        ts_str = data["data"]["time"]["s"]
        ts = pd.to_datetime(ts_str).tz_localize(None)
    except Exception:
        return pd.DataFrame()

    # Skip if not newer
    if ts <= since:
        return pd.DataFrame()

    pm25 = data["data"]["iaqi"].get("pm25", {}).get("v", None)

    df = pd.DataFrame([{
        "sensor_id": sensor_id,
        "date": ts,
        "pm25": pm25,
        "aqicn_url": feed_url
    }])

    return df