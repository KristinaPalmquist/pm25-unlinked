import { getAQIColor } from '../config/mapConfig.js';
import { deriveDayDates } from '../utils/index.js';

export const sourceId = 'pm25-interpolation';
export const layerId = 'pm25-interpolation-layer';

export async function loadMarkersFromBackend(map, state, onClick) {
  const rows = await fetchLatestBatch();
  rows.forEach((row) => ingestRow(row, state));
  Object.values(state.sensorData).forEach((entry) => {
    const marker = createMarker(entry, onClick);
    marker.addTo(map);
  });
}

export async function loadRaster(map, config, day, state) {
  state.currentDay = day;

  await waitForStyle(map);
  removeRasterLayer(map);

  map.addSource(sourceId, {
    type: 'image',
    url: buildRasterUrl(day, config),
    coordinates: [
      [config.mapBounds[0], config.mapBounds[3]],
      [config.mapBounds[2], config.mapBounds[3]],
      [config.mapBounds[2], config.mapBounds[1]],
      [config.mapBounds[0], config.mapBounds[1]],
    ],
  });

  map.addLayer({
    id: layerId,
    type: 'raster',
    source: sourceId,
    paint: { 'raster-opacity': 0.75, 'raster-resampling': 'linear' },
  });
}

export function removeRasterLayer(map) {
  if (map.getLayer(layerId)) map.removeLayer(layerId);
  if (map.getSource(sourceId)) map.removeSource(sourceId);
}

export function buildRasterUrl(day, config) {
  return `${config.interpolationBase}/${config.interpolationTemplate.replace('{day}', day)}`;
}

export function waitForStyle(map) {
  return new Promise((resolve) =>
    map.isStyleLoaded() ? resolve() : map.once('styledata', resolve),
  );
}

export function loadCsvMarkers(rows, state, onClick) {
  state.csvHeaders = rows.length ? Object.keys(rows[0]) : [];
  state.dayDates = deriveDayDates(rows);

  state.markers.forEach((m) => m.remove());
  state.markers = [];
  state.sensorData = {};

  rows.forEach((row) => ingestRow(row, state));

  state.markers = Object.values(state.sensorData).map((entry) =>
    createMarker(entry, onClick),
  );
}

export function ingestRow(row, state) {
  const sensorId = row.sensor_id || row.sensorId;
  const lat = parseFloat(row.latitude ?? row.lat);
  const lon = parseFloat(row.longitude ?? row.lon ?? row.lng);

  if (!sensorId || Number.isNaN(lat) || Number.isNaN(lon)) return;

  const street = row.street || row.location || '';
  const city = row.city_y || row.city_x || '';

  if (!state.sensorData[sensorId]) {
    state.sensorData[sensorId] = {
      sensorId,
      lat,
      lon,
      city,
      street,
      latestValue: null,
      rows: [],
    };
  }

  const entry = state.sensorData[sensorId];
  if (!Number.isFinite(entry.lat) || !Number.isFinite(entry.lon)) {
    entry.lat = lat;
    entry.lon = lon;
  }
  if (!entry.street && street) entry.street = street;
  if (!entry.city && city) entry.city = city;
  entry.rows.push(row);

  const predicted = parseFloat(row.predicted_pm25 ?? row.predicted ?? 'NaN');
  const actual = parseFloat(row.pm25 ?? 'NaN');
  if (Number.isFinite(predicted)) entry.latestValue = predicted;
  else if (Number.isFinite(actual)) entry.latestValue = actual;
}

export function buildPopupHtml(entry) {
  const name = entry.street || entry.sensorId;
  const location = entry.city ? `${entry.city}<br/>` : '';
  const reading = Number.isFinite(entry.latestValue)
    ? `PM2.5: ${entry.latestValue.toFixed(1)}`
    : 'No recent value';
  return `<strong>${name}</strong><br/>${location}${reading}`;
}

export function createMarker(entry, onClick) {
  const element = document.createElement('div');
  element.className = 'sensor-marker';
  element.style.background = getAQIColor(entry.latestValue ?? 0);
  element.addEventListener('click', (e) => {
    e.stopPropagation();
    onClick(entry.sensorId, element);
  });

  return new maplibregl.Marker({ element })
    .setLngLat([entry.lon, entry.lat])
    .setPopup(
      new maplibregl.Popup({ closeButton: false, offset: 12 }).setHTML(
        buildPopupHtml(entry),
      ),
    );
}
