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
            # Serve predictions from Hopsworks dataset storage (uploaded by batch job)
            try:
                dataset_api = project.get_dataset_api()
                
                # Download predictions.json from Hopsworks
                local_path = dataset_api.download("Resources/airquality/predictions.json", overwrite=True)
                
                with open(local_path, 'r') as f:
                    predictions_data = json.load(f)
                
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
                        "error": "Predictions not found in Hopsworks storage",
                        "details": str(e)
                    })
                }
        
        if params.get("type") == "interpolation":
            # Serve interpolation heatmap images from Hopsworks
            day = params.get("day", "0")
            try:
                dataset_api = project.get_dataset_api()
                
                # List available interpolation images
                try:
                    files = dataset_api.list("Resources/airquality", recursive=False)
                    interpolation_files = [
                        f for f in files 
                        if "interpolation_" in f and f.endswith(".png")
                    ]
                    
                    # Find the most recent interpolation for this day offset
                    # Format: interpolation_YYYY-MM-DD_YYYY-MM-DD.png (today_forecast)
                    target_files = [
                        f for f in interpolation_files
                        if f.endswith(f"_{day}d.png") or f"interpolation_{day}d" in f
                    ]
                    
                    if target_files:
                        # Get the most recent file
                        latest_file = sorted(target_files)[-1]
                        file_path = f"Resources/airquality/{latest_file}"
                        
                        # Download and return the image
                        local_path = dataset_api.download(file_path, overwrite=True)
                        
                        with open(local_path, 'rb') as img_file:
                            import base64
                            img_data = base64.b64encode(img_file.read()).decode('utf-8')
                        
                        return {
                            "statusCode": 200,
                            "headers": {
                                "Content-Type": "image/png",
                                "Access-Control-Allow-Origin": "*"
                            },
                            "body": img_data,
                            "isBase64Encoded": True
                        }
                    else:
                        return {
                            "statusCode": 404,
                            "headers": {"Content-Type": "application/json"},
                            "body": json.dumps({"error": f"No interpolation image found for day {day}"})
                        }
                except Exception as e:
                    return {
                        "statusCode": 404,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "Interpolation images not found in Hopsworks", "details": str(e)})
                    }
            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": str(e)})
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