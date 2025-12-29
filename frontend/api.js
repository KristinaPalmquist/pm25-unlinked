const API_URL =
  window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : "https://hospitable-bravery-production-e171.up.railway.app";

// Fetch all sensor rows from backend
export async function fetchLatestBatch() {
  try {
    const response = await fetch(`${API_URL}/latest`);
    if (!response.ok) {
      throw new Error("Failed to fetch latest data");
    }
    const rows = await response.json(); // this will be an array
    console.log("Fetched batch:", rows.length, "rows");
    return rows;
  } catch (err) {
    console.error("Error fetching data:", err);
    return [];
  }
}