import json
import os
import hopsworks
import pandas as pd

def handler(event, context):
    try:
        params = event.get("queryStringParameters", {}) or {}
        
        # Get API key from environment (set in Netlify)
        api_key = os.environ.get("HOPSWORKS_API_KEY")
        if not api_key:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "HOPSWORKS_API_KEY not configured"})
            }
        
        # Connect to Hopsworks
        project = hopsworks.login(api_key_value=api_key)
        fs = project.get_feature_store()
        
        if params.get("type") == "predictions":
            # Fetch latest predictions from monitoring feature group
            try:
                monitor_fg = fs.get_feature_group("aq_predictions", version=1)
                
                # Get D+1 predictions (most recent forecast)
                predictions_df = monitor_fg.filter(
                    monitor_fg.days_before_forecast_day == 1
                ).read()
                
                # Convert to JSON-serializable format
                predictions_df["date"] = predictions_df["date"].astype(str)
                predictions_data = predictions_df.to_dict(orient="records")
                
                return {
                    "statusCode": 200,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    },
                    "body": json.dumps(predictions_data)
                }
            except Exception as e:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "error": "Predictions not found",
                        "details": str(e)
                    })
                }
        
        if "sensor" in params:
            sensor_id = int(params["sensor"])
            try:
                # Fetch sensor-specific data
                monitor_fg = fs.get_feature_group("aq_predictions", version=1)
                air_quality_fg = fs.get_feature_group("air_quality", version=1)
                
                # Get predictions for this sensor
                sensor_predictions = monitor_fg.filter(
                    (monitor_fg.sensor_id == sensor_id) & 
                    (monitor_fg.days_before_forecast_day == 1)
                ).read()
                
                # Get historical data for this sensor
                sensor_history = air_quality_fg.filter(
                    air_quality_fg.sensor_id == sensor_id
                ).read()
                
                # Combine and format
                sensor_predictions["date"] = sensor_predictions["date"].astype(str)
                sensor_history["date"] = sensor_history["date"].astype(str)
                
                sensor_data = {
                    "sensor_id": sensor_id,
                    "predictions": sensor_predictions.to_dict(orient="records"),
                    "history": sensor_history.to_dict(orient="records")
                }
                
                return {
                    "statusCode": 200,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"
                    },
                    "body": json.dumps(sensor_data)
                }
            except Exception as e:
                return {
                    "statusCode": 404,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({
                        "error": f"Sensor {sensor_id} not found",
                        "details": str(e)
                    })
                }
        
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid request. Use ?type=predictions or ?sensor=<id>"})
        }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }