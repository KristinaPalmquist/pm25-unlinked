from fastapi import FastAPI
import hopsworks

app = FastAPI()

@app.get("/latest")
def latest():
    project = hopsworks.login(api_key=os.environ["HOPSWORKS_API_KEY"])
    fs = project.get_feature_store(name="new_featurestore")
    fv = fs.get_feature_view("air_quality_complete_fv", version=1)

    df = fv.get_batch_data()  # or fv.get_serving_vector() if you have serving keys
    return df.tail(1).to_dict(orient="records")[0]