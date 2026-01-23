// Fetch predictions and sensor data from Netlify function (backed by Hopsworks)
export const interpolationBase = '/models/interpolation';

export async function fetchPredictions() {
  try {
    const res = await fetch('/.netlify/functions/api?type=predictions');
    if (!res.ok) {
      throw new Error('Failed to fetch predictions');
    }
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (err) {
    console.error('Error fetching predictions:', err);
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
