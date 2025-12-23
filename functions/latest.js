export async function onRequest(context) {
  const apiKey = context.env.HOPSWORKS_API_KEY;

//   const url = "https://c.app.hopsworks.ai/hopsworks-api/api/project/2172/featurestores/2121/featureviews/air_quality_complete_fv/versions/1/onlinefeatures";
// const url = "https://2172.eu-west.hopsworks.ai:4406/0.1.0/feature_store";
 const url = "https://c.app.hopsworks.ai/hopsworks-api/api/p/2172/fs/2121/fv/air_quality_complete_fv/version/1#overview";
//   const url = "https://c.app.hopsworks.ai/0.1.0/feature_store";
// const url = "https://eu-west.cloud.hopsworks.ai/hopsworks-api/api/project/2172/featurestore/2121/featurevector"
  const body = {
    featureStoreName: "new_featurestore",
    featureViewName: "air_quality_complete_fv",
    featureViewVersion: 1,
    entries: {
      sensor_id: 59893
    }
  };

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "X-API-KEY": apiKey,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });

  const data = await response.json();

  return new Response(JSON.stringify(data), {
    headers: { "Content-Type": "application/json" }
  });
}