export async function loadCoordinates() {
  const response = await fetch('./coordinates.json');
  const data = await response.json();
  return data;
}
