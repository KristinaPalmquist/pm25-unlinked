export async function loadCoordinates() {
  const response = await fetch('./utils/coordinates.json');
  const data = await response.json();
  return data;
}