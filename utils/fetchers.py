import requests
import requests_cache
import openmeteo_requests

import pandas as pd
import json
from retry_requests import retry
import datetime
import time



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

def get_historical_weather(city, start_date, end_date, latitude, longitude):
    # latitude, longitude = get_city_coordinates(city)

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["temperature_2m_mean", "precipitation_sum", "wind_speed_10m_max", "wind_direction_10m_dominant"]
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_temperature_2m_mean = daily.Variables(0).ValuesAsNumpy()
    daily_precipitation_sum = daily.Variables(1).ValuesAsNumpy()
    daily_wind_speed_10m_max = daily.Variables(2).ValuesAsNumpy()
    daily_wind_direction_10m_dominant = daily.Variables(3).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s"),
        end = pd.to_datetime(daily.TimeEnd(), unit = "s"),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left"
    )}
    daily_data["temperature_2m_mean"] = daily_temperature_2m_mean
    daily_data["precipitation_sum"] = daily_precipitation_sum
    daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
    daily_data["wind_direction_10m_dominant"] = daily_wind_direction_10m_dominant

    daily_dataframe = pd.DataFrame(data = daily_data)
    daily_dataframe = daily_dataframe.dropna()
    daily_dataframe['city'] = city
    return daily_dataframe


def get_hourly_weather_forecast(city, latitude, longitude):

    # latitude, longitude = get_city_coordinates(city)

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "precipitation", "wind_speed_10m", "wind_direction_10m"],
        "forecast_days": 7
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # Process hourly data. The order of variables needs to be the same as requested.

    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(1).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(2).ValuesAsNumpy()
    hourly_wind_direction_10m = hourly.Variables(3).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s"),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s"),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}
    hourly_data["temperature_2m_mean"] = hourly_temperature_2m
    hourly_data["precipitation_sum"] = hourly_precipitation
    hourly_data["wind_speed_10m_max"] = hourly_wind_speed_10m
    hourly_data["wind_direction_10m_dominant"] = hourly_wind_direction_10m

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    hourly_dataframe = hourly_dataframe.dropna()
    return hourly_dataframe

def get_historical_weather(city, df, today, feed_url, sensor_id, AQICN_API_KEY):
    # 1. Determine earliest AQ date
    start_dt = df["datetime"].min()
    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")

    # 2. Get coordinates
    latitude, longitude = get_sensor_coordinates(feed_url, sensor_id, AQICN_API_KEY)

    # 3. Call Open-Meteo DAILY archive API
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_mean,precipitation_sum,wind_speed_10m_max,wind_direction_10m_dominant",
        "timezone": "UTC"
    }

    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    daily = data.get("daily")
    if daily is None:
        print(f"No daily weather data for sensor {sensor_id}")
        return pd.DataFrame(), latitude, longitude

    weather_df = pd.DataFrame(daily)
    weather_df["datetime"] = pd.to_datetime(weather_df["time"]).dt.tz_localize(None)
    weather_df = weather_df.drop(columns=["time"])

    # Add metadata
    weather_df["sensor_id"] = sensor_id
    weather_df["city"] = city
    weather_df["latitude"] = latitude
    weather_df["longitude"] = longitude

    return weather_df, latitude, longitude

def get_latest_weather(latitude: float, longitude: float, since: datetime):
    """
    Fetch only new weather rows since the last datetime.
    """

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "start_date": since.strftime("%Y-%m-%d"),
        "end_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "timezone": "UTC"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # Convert to dataframe
    hourly = data["hourly"]
    df = pd.DataFrame(hourly)

    # Convert time → datetime
    df["datetime"] = pd.to_datetime(df["time"]).dt.tz_localize(None)
    df = df.drop(columns=["time"])

    # Keep only rows newer than "since"
    df = df[df["datetime"] > since]

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


def get_sensor_coordinates(feed_url, sensor_id, AQICN_API_KEY):
    response = requests.get(f"{feed_url}?token={AQICN_API_KEY}")
    data = response.json()
    latitude = data["data"]["city"]["geo"][0]
    longitude = data["data"]["city"]["geo"][1]
    return latitude, longitude
# def get_sensor_coordinates(feed_url, sensor_id, AQICN_API_KEY):
#     """
#     Given a sensor_id, return (latitude, longitude, feed_url).
#     Raises ValueError if coordinates cannot be extracted.
#     """
#     try:
#         response = requests.get(f"{feed_url}?token={AQICN_API_KEY}")
#         response.raise_for_status()
#         data = response.json()

#         if "data" not in data or "city" not in data["data"] or "geo" not in data["data"]["city"]:
#             raise ValueError(f"Invalid response structure for {feed_url}: {data}")

#         latitude = data["data"]["city"]["geo"][0]
#         longitude = data["data"]["city"]["geo"][1]
#         return latitude, longitude

#     except Exception as e:
#         raise ValueError(f"Failed to get coordinates from {feed_url}: {e}")
    

    
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

def fetch_latest_aq_data(sensor_id: str, feed_url: str, since: datetime):
    """
    Fetch only new AQ measurements for a sensor since the last datetime.
    """

    if since is None:
        since = pd.Timestamp.min

    response = requests.get(feed_url)
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
        "datetime": ts,
        "pm25": pm25,
        "aqicn_url": feed_url
    }])

    return df