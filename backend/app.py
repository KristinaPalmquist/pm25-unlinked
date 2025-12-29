from fastapi import FastAPI, HTTPException
import hopsworks
# import pandas as pd
from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

app = FastAPI()


@app.get("/latest")
def latest():
    try:
        api_key = os.environ.get("HOPSWORKS_API_KEY")
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing HOPSWORKS_API_KEY environment variable")

        try:
            project = hopsworks.login(api_key=api_key)
        except Exception as e:
            raise HTTPException(status_code=403, detail=f"Hopsworks login failed: {str(e)}")

        try:
            fs = project.get_feature_store(name="new_featurestore")
            fv = fs.get_feature_view("air_quality_complete_fv", version=1)
            df = fv.get_batch_data()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")

        if df.empty:
            raise HTTPException(status_code=404, detail="No data found in feature view")

        latest_row = df.tail(1).to_dict(orient="records")[0]
        return latest_row

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def load_feature_view():
    project = hopsworks.login(api_key=os.environ["HOPSWORKS_API_KEY"])
    fs = project.get_feature_store(name="new_featurestore")
    return fs.get_feature_view("air_quality_complete_fv", version=1)


@app.get("/prediction/{sensor_id}")
def prediction_for_sensor(sensor_id: str):
    fv = load_feature_view()

    # Load the full prediction dataset
    df = fv.get_batch_data()

    # Ensure sensor_id exists
    if "sensor_id" not in df.columns:
        raise HTTPException(status_code=500, detail="Feature View missing 'sensor_id' column")

    # Filter for this sensor
    df_sensor = df[df["sensor_id"] == sensor_id]

    if df_sensor.empty:
        raise HTTPException(status_code=404, detail=f"No predictions found for sensor {sensor_id}")

    # Return the latest prediction row
    latest = df_sensor.sort_values("datetime").tail(1).to_dict(orient="records")[0]
    return latest

# # example call
# GET https://your-backend.up.railway.app/prediction/59893


# Return all predictions for a sensor
@app.get("/prediction/{sensor_id}/history")
def prediction_history(sensor_id: str):
    fv = load_feature_view()
    df = fv.get_batch_data()
    df_sensor = df[df["sensor_id"] == sensor_id]

    if df_sensor.empty:
        raise HTTPException(status_code=404, detail=f"No predictions found for sensor {sensor_id}")

    return df_sensor.sort_values("datetime").to_dict(orient="records")

# return predictions for all sensors
@app.get("/predictions")
def all_predictions():
    fv = load_feature_view()
    df = fv.get_batch_data()

    latest_per_sensor = (
        df.sort_values("datetime")
          .groupby("sensor_id")
          .tail(1)
          .to_dict(orient="records")
    )

    return latest_per_sensor
