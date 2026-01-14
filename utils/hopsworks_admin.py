import os
import time
from pathlib import Path
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


def clone_or_update_repo(username: str):
    repo_name = "pm25-forecast-openmeteo-aqicn"

    # 1. Detect if already inside the repo
    cwd = Path().absolute()
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".git").exists() and parent.name == repo_name:
            print(f"Already in repo at {parent}")
            return parent

    # 2. Detect if the repo exists in the current directory
    repo_dir = Path(repo_name)
    if repo_dir.exists():
        print(f"Repository exists at {repo_dir.absolute()}")
        os.system(f"git -C {repo_dir} pull")
        return repo_dir

    # 3. Otherwise clone it
    print("Cloning repository...")
    url = f"https://github.com/{username}/{repo_name}.git"
    exit_code = os.system(f"git clone {url}")

    if exit_code != 0:
        raise RuntimeError("Git clone failed.")

    print("Clone successful.")
    return repo_dir


def create_feature_groups(fs, max_retries=5):
    for attempt in range(max_retries):
        try:
            air_quality_fg = fs.get_or_create_feature_group(
                name="air_quality",
                description="Air Quality characteristics of each day for all sensors",
                version=1,
                primary_key=["sensor_id", "date"],
                event_time="date",
                expectation_suite=None,
                features=[
                    Feature("sensor_id", type="int"),
                    Feature("location_id", type="int"),
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
        except (hopsworks.client.exceptions.RestAPIError, ProtocolError, ConnectionError, Timeout) as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Could not create feature groups.")
                raise
    


def update_air_quality_description(air_quality_fg):
    air_quality_fg.update_feature_description("date", "Date and time of measurement of air quality")
    air_quality_fg.update_feature_description("sensor_id", "AQICN sensor identifier (e.g., 59893)")
    air_quality_fg.update_feature_description("location_id", "Geographic location identifier shared with weather data (multiple sensors can share same location)")
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
    air_quality_fg.update_feature_description("pm25_nearby_avg", "Average PM2.5 from 3 nearest sensors on same day")


def update_weather_description(weather_fg):
    weather_fg.update_feature_description("date", "Date and time of weather measurement")
    weather_fg.update_feature_description("location_id", "Geographic location identifier (multiple sensors can share same location)")
    weather_fg.update_feature_description("temperature_2m_mean", "Daily mean temperature at 2m above ground in Celsius")
    weather_fg.update_feature_description("precipitation_sum", "Daily total precipitation (rain/snow) in mm")
    weather_fg.update_feature_description("wind_speed_10m_max", "Maximum wind speed at 10m above ground in km/h")
    weather_fg.update_feature_description("wind_direction_10m_dominant", "Dominant wind direction over the day in degrees (0-360)")


def read_data(fg, max_retries=5):
    for attempt in range(max_retries):
        try:
            return fg.read()
        except Exception as e:
            if "flight" in str(e).lower() or "query service" in str(e).lower():
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)  # 10s, 20s, 30s, 40s, 50s
                    print(f"⚠️  Hopsworks query service error (attempt {attempt+1}/{max_retries})")
                    print(f"   Error: {str(e)[:100]}...")
                    print(f"   Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Failed to read after {max_retries} attempts")
                    raise
            else:
                raise


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