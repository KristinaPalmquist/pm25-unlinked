// Fetch predictions from Netlify function (which fetches from Hopsworks)
export const interpolationBase = '/.netlify/functions/api?type=interpolation';

export async function fetchPredictions() {
  try {
    const res = await fetch('/.netlify/functions/api?type=predictions');
    if (!res.ok) {
      console.warn(
        'Predictions not available. Make sure:',
        '\n1. HOPSWORKS_API_KEY is set in Netlify environment variables',
        '\n2. Notebook 4 batch job has run to upload predictions.json to Hopsworks',
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
