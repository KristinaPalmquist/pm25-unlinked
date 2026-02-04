// Fetch predictions and images from Hopsworks public storage (runtime)
// Update PROJECT_ID with your Hopsworks project ID
const HOPSWORKS_PROJECT_ID = '271255'; // Replace with actual project ID
const HOPSWORKS_BASE = `https://c.app.hopsworks.ai/p/${HOPSWORKS_PROJECT_ID}/fs/Resources/airquality`;

export const interpolationBase = `${HOPSWORKS_BASE}/forecast_interpolation`;

export async function fetchPredictions() {
  try {
    const res = await fetch(`${HOPSWORKS_BASE}/predictions.json`);
    if (!res.ok) {
      console.warn(
        'Predictions not available from Hopsworks.',
        '\nMake sure notebook 4 batch job has uploaded predictions.json',
      );
      return [];
    }
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('Predictions fetch failed:', err.message);
    return [];
  }
}

export async function fetchSensorData(sensorId) {
  try {
    const res = await fetch(`/.netlify/functions/api?sensor=${sensorId}`);
    if (!res.ok) {
      throw new Error('Failed to fetch sensor data');
    }
    return await res.json();
  } catch (err) {
    console.error(`Error fetching sensor ${sensorId}:`, err);
    return null;
  }
}
