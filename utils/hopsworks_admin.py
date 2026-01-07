import hopsworks
import hsfs
# from hopsworks.secrets import secrets_api



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