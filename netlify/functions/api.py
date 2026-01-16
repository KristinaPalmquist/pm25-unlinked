import json
import hopsworks
from utils import cleaning, config, feature_engineering, fetchers, hopsworks_admin, incremental, metadata

def handler(event, context):
    # Login to Hopsworks
    settings = config.HopsworksSettings()
    HOPSWORKS_API_KEY = settings.HOPSWORKS_API_KEY.get_secret_value()
    project = hopsworks.login(api_key_value=HOPSWORKS_API_KEY)
    fs = project.get_feature_store()

    # Example: read a file or feature group
    # Replace this with your real logic
    result = {"message": "Backend is working!"}

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(result)
    }
