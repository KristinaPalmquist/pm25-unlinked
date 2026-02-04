// Fetch predictions from static file (committed by Hopsworks job)
export async function fetchPredictions() {
  try {
    const res = await fetch('/predictions.json');
    if (!res.ok) {
      console.warn(
        'Predictions not available.',
        '\nMake sure notebook 4 batch job has run and committed predictions.json',
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
