import hopsworks
import hsfs
from hsfs.feature import Feature



def delete_feature_groups(fs, name):
    try:
        for fg in fs.get_feature_groups(name):
            fg.delete()
            print(f"Deleted {fg.name}/{fg.version}")
    except hsfs.client.exceptions.RestAPIError:
        print(f"No {name} feature group found")


def delete_feature_views(fs, name):
    try:
        for fv in fs.get_feature_views(name):
            fv.delete()
            print(f"Deleted {fv.name}/{fv.version}")
    except hsfs.client.exceptions.RestAPIError:
        print(f"No {name} feature view found")


def delete_models(mr, name):
    models = mr.get_models(name)
    if not models:
        print(f"No {name} model found")
    for model in models:
        model.delete()
        print(f"Deleted model {model.name}/{model.version}")


def delete_secrets(proj, name):
    secrets = secrets_api(proj.name)
    try:
        secret = secrets.get_secret(name)
        secret.delete()
        print(f"Deleted secret {name}")
    except hopsworks.client.exceptions.RestAPIError:
        print(f"No {name} secret found")


# # WARNING - this will wipe out all your feature data and models
# def purge_project(proj):
#     fs = proj.get_feature_store()
#     mr = proj.get_model_registry()

#     # Delete Feature Views before deleting the feature groups
#     delete_feature_views(fs, "air_quality_fv")

#     # Delete ALL Feature Groups
#     delete_feature_groups(fs, "air_quality")
#     delete_feature_groups(fs, "weather")
#     delete_feature_groups(fs, "aq_predictions")

#     # Delete all Models
#     delete_models(mr, "air_quality_xgboost_model")
#     delete_secrets(proj, "SENSOR_LOCATION_JSON")


def create_feature_groups(fs):
    air_quality_fg = fs.get_or_create_feature_group(
        name="air_quality",
        description="Air Quality characteristics of each day for all sensors",
        version=1,
        primary_key=["sensor_id", "date"],
        event_time="date",
        expectation_suite=None,
        features=[
            Feature("sensor_id", type="int"),
            Feature("date", type="timestamp"),
            Feature("pm25", type="double"),
            Feature("pm25_lag_1d", type="double"),
            Feature("pm25_lag_2d", type="double"),
            Feature("pm25_lag_3d", type="double"),
            Feature("pm25_rolling_3d", type="double"),
            Feature("pm25_nearby_avg", type="double"),
        ],
    )

    sensor_metadata_fg = fs.get_or_create_feature_group(
        name="sensor_metadata",
        description="Metadata for each air quality sensor",
        version=1,
        primary_key=["sensor_id"],
        expectation_suite=None,
        features=[
            Feature("sensor_id", type="int"),
            Feature("location_id", type="int"),
            Feature("city", type="string"),
            Feature("street", type="string"),
            Feature("country", type="string"),
            Feature("aqicn_url", type="string"),
            Feature("latitude", type="double"),
            Feature("longitude", type="double"),
        ],
    )

    weather_fg = fs.get_or_create_feature_group(
        name="weather",
        description="Weather characteristics of each day for all locations",
        version=1,
        primary_key=["location_id", "date"],
        event_time="date",
        expectation_suite=None,
        features=[
            Feature("date", "timestamp"),
            Feature("location_id", "int"),
            Feature("temperature_2m_mean", "double"),
            Feature("precipitation_sum", "double"),
            Feature("wind_speed_10m_max", "double"),
            Feature("wind_direction_10m_dominant", "double"),
        ]
    )

    return air_quality_fg, sensor_metadata_fg, weather_fg


def update_air_quality_description(air_quality_fg):
    air_quality_fg.update_feature_description("date", "Date and time of measurement of air quality")
    air_quality_fg.update_feature_description("sensor_id", "AQICN sensor identifier (e.g., 59893)")
    air_quality_fg.update_feature_description(
        "pm25",
        "Particles less than 2.5 micrometers in diameter (fine particles) pose health risk",
    )
    air_quality_fg.update_feature_description(
        "pm25_rolling_3d",
        "3-day rolling mean of PM2.5 from previous days (lagged by 1 day for point-in-time correctness).",
    )
    air_quality_fg.update_feature_description("pm25_lag_1d", "PM2.5 value from 1 day ago.")
    air_quality_fg.update_feature_description("pm25_lag_2d", "PM2.5 value from 2 days ago.")
    air_quality_fg.update_feature_description("pm25_lag_3d", "PM2.5 value from 3 days ago.")


def update_sensor_metadata_description(sensor_metadata_fg):
    sensor_metadata_fg.update_feature_description("sensor_id", "AQICN sensor identifier (e.g., 59893)")
    sensor_metadata_fg.update_feature_description("city", "City where the air quality was measured")
    sensor_metadata_fg.update_feature_description("street", "Street in the city where the air quality was measured")
    sensor_metadata_fg.update_feature_description(
        "country",
        "Country where the air quality was measured (sometimes a city in aqicn.org)",
    )
    sensor_metadata_fg.update_feature_description("aqicn_url", "URL to the AQICN feed for this sensor")
    sensor_metadata_fg.update_feature_description("latitude", "Latitude of the sensor location")
    sensor_metadata_fg.update_feature_description("longitude", "Longitude of the sensor location")


def update_weather_description(weather_fg):
    weather_fg.update_feature_description("date", "Date and time of measurement of weather")
    weather_fg.update_feature_description("sensor_id", "AQICN sensor identifier (e.g., 59893)")
    weather_fg.update_feature_description("city", "City where weather is measured/forecast for")
    weather_fg.update_feature_description("temperature_2m_mean", "Temperature in Celsius")
    weather_fg.update_feature_description("precipitation_sum", "Precipitation (rain/snow) in mm")
    weather_fg.update_feature_description("wind_speed_10m_max", "Wind speed at 10m above ground")
    weather_fg.update_feature_description("wind_direction_10m_dominant", "Dominant wind direction over the day")
    weather_fg.update_feature_description("latitude", "Latitude of sensor location used for weather retrieval")
    weather_fg.update_feature_description("longitude", "Longitude of sensor location used for weather retrieval")


def save_or_replace_expectation_suite(fg, suite):
    """
    Ensures the feature group ends up with the given expectation suite.
    If a suite already exists, delete it first, then save the new one.
    """
    # Try deleting existing suite
    try:
        fg.delete_expectation_suite()
        print(f"Deleted existing expectation suite for FG '{fg.name}'.")
    except Exception:
        # No suite existed — that's fine
        pass

    # Now save the new suite
    fg.save_expectation_suite(suite)
    print(f"Saved expectation suite for FG '{fg.name}'.")