from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import hopsworks
from dotenv import load_dotenv
import os
import math
import pandas as pd

app = FastAPI()

# Allow Netlify frontend to call this backend
origins = [
    "https://pm25-sweden.netlify.app",  # production frontend
    "http://localhost:5501",            # local dev
    "http://127.0.0.1:8000"             # local backend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],            # allow all HTTP methods
    allow_headers=["*"],            # allow all headers
)


env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)
api_key=os.environ["HOPSWORKS_API_KEY"]

@app.get("/predictions")
def get_predictions():
    df = pd.read_csv("models/predictions.csv")
    return df.to_dict(orient="records")


@app.get("/latest")
def latest():
    try:
        project = hopsworks.login()
        fs = project.get_feature_store()
        fv = fs.get_feature_view("air_quality_complete_fv", version=1)
        df = fv.get_batch_data()

        if df.empty:
            raise HTTPException(status_code=404, detail="No data found in feature view")

        rows = df.to_dict(orient="records")
        return rows

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def load_feature_view():
    
    project = hopsworks.login()
    fs = project.get_feature_store()
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
