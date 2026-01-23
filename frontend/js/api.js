// Fetch predictions and sensor data from Netlify function (backed by Hopsworks)
export const interpolationBase = '/models/interpolation';

export async function fetchPredictions() {
  try {
    const res = await fetch('/.netlify/functions/api?type=predictions');
    if (!res.ok) {
      console.warn('Predictions API not available (404). Make sure:', 
        '\n1. HOPSWORKS_API_KEY is set in Netlify environment variables',
        '\n2. Notebook 4 has been run to create aq_predictions feature group');
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
