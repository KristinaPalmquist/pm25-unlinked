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

  const url = buildRasterUrl(day, config);
  console.log(`Loading raster for day ${day}: ${url}`);

  map.addSource(sourceId, {
    type: 'image',
    url: url,
    coordinates: [
      [config.mapBounds[0], config.mapBounds[3]],
      [config.mapBounds[2], config.mapBounds[3]],
      [config.mapBounds[2], config.mapBounds[1]],
      [config.mapBounds[0], config.mapBounds[1]],
    ],
  });

  // Add raster layer on top of base map but below labels
  // Find the first label or symbol layer to insert before it
  const layers = map.getStyle().layers;
  const firstSymbolId = layers.find((layer) => layer.type === 'symbol')?.id;

  map.addLayer(
    {
      id: layerId,
      type: 'raster',
      source: sourceId,
      paint: { 'raster-opacity': 0.75, 'raster-resampling': 'linear' },
    },
    firstSymbolId, // Insert before labels, or on top if no labels found
  );

  console.log(`✅ Raster layer added for day ${day}`);
}

export function removeRasterLayer(map) {
  if (map.getLayer(layerId)) map.removeLayer(layerId);
  if (map.getSource(sourceId)) map.removeSource(sourceId);
}

export function buildRasterUrl(day, config) {
  // config.interpolationBase points to Hopsworks storage
  // Returns: https://c.app.hopsworks.ai/p/{id}/fs/Resources/airquality/forecast_interpolation_0d.png
  return `${config.interpolationBase}_${day}d.png`;
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

  if (!sensorId || Number.isNaN(lat) || Number.isNaN(lon)) {
    return;
  }

  const street = row.street || row.location || '';
  const city = row.city_y || row.city_x || row.city || '';

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
  const sensorId = `Sensor ID: ${entry.sensorId}`;
  const street = entry.street ? `<br/>${entry.street}` : '';
  const city = entry.city ? `<br/>${entry.city}` : '';
  const reading = Number.isFinite(entry.latestValue)
    ? `<br/>PM2.5: ${entry.latestValue.toFixed(1)}`
    : '<br/>No recent value';
  return `<strong>${sensorId}</strong>${street}${city}${reading}`;
}

export function createMarker(entry, onClick) {
  const element = document.createElement('div');
  element.className = 'sensor-marker';
  element.style.background = getAQIColor(entry.latestValue ?? 0);
  element.style.cursor = 'pointer';
  element.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.2)';
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
