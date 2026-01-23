export const interpolationBase = '/.netlify/functions/api';

export async function fetchPredictions() {
  try {
    const res = await fetch('/.netlify/functions/api?type=predictions');
    if (!res.ok) {
      throw new Error('Failed to fetch predictions');
    }
    return await res.json();
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

// const URL = "https://hospitable-bravery-production-e171.up.railway.app";

// const API_URL =
//   window.location.hostname === "127.0.0.1" ||
//   window.location.hostname === "localhost"
//     ? "http://127.0.0.1:8000"
//     : URL;

// export const interpolationBase = `${API_URL}/models/interpolation`;

// // Fetch predictions
// export async function fetchPredictions() {
//   try {
//     const response = await fetch(`${API_URL}/predictions`);
//     if (!response.ok) {
//       throw new Error("Failed to fetch predictions");
//     }
//     return await response.json(); // returns array of objects
//   } catch (err) {
//     console.error("Error fetching predictions:", err);
//     return [];
//   }
// }

// // Fetch latest batch from feature view
// export async function fetchLatestBatch() {
//   try {
//     const response = await fetch(`${API_URL}/latest`);
//     if (!response.ok) {
//       throw new Error("Failed to fetch latest data");
//     }
//     return await response.json();
//   } catch (err) {
//     console.error("Error fetching latest batch:", err);
//     return [];
//   }
// }
