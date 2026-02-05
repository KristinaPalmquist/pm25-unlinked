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
  console.log(`Loading interpolation overlay: ${url}`);
  console.log(`   Coordinates:`, {
    topLeft: [config.mapBounds[0], config.mapBounds[3]],
    topRight: [config.mapBounds[2], config.mapBounds[3]],
    bottomRight: [config.mapBounds[2], config.mapBounds[1]],
    bottomLeft: [config.mapBounds[0], config.mapBounds[1]],
  });

  // Add error handling for source loading
  const handleSourceError = (e) => {
    if (e.sourceId === sourceId) {
      console.error(`❌ Failed to load raster image: ${url}`, e.error);
      map.off('error', handleSourceError);
    }
  };

  const handleSourceData = (e) => {
    if (e.sourceId === sourceId && e.isSourceLoaded) {
      console.log(`✅ Raster image loaded successfully: ${url}`);
      map.off('sourcedata', handleSourceData);
    }
  };

  map.on('error', handleSourceError);
  map.on('sourcedata', handleSourceData);

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

  console.log(
    `✅ Interpolation overlay layer added for day ${day}${firstSymbolId ? ' (below labels)' : ' (on top)'}`,
  );
  console.log(`   Layer ID: ${layerId}, Opacity: 0.75`);

  // Debug: Check layer visibility
  setTimeout(() => {
    const layer = map.getLayer(layerId);
    const source = map.getSource(sourceId);
    const paint = map.getPaintProperty(layerId, 'raster-opacity');
    const visibility = map.getLayoutProperty(layerId, 'visibility');
    console.log(`🔍 Layer debug:`, {
      layerExists: !!layer,
      sourceExists: !!source,
      opacity: paint,
      visibility: visibility || 'visible',
      layerType: layer?.type,
    });

    // Check all layers to see position
    const allLayers = map.getStyle().layers;
    const layerIndex = allLayers.findIndex((l) => l.id === layerId);
    console.log(
      `   Layer position: ${layerIndex} of ${allLayers.length} layers`,
    );
    console.log(
      `   Layers around it:`,
      allLayers
        .slice(Math.max(0, layerIndex - 2), layerIndex + 3)
        .map((l) => `${l.id} (${l.type})`),
    );
  }, 500);
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
  console.log('Sample row full data:', JSON.stringify(rows[0], null, 2));

  state.csvHeaders = rows.length ? Object.keys(rows[0]) : [];
  state.dayDates = deriveDayDates(rows);

  state.markers.forEach((m) => m.remove());
  state.markers = [];
  state.sensorData = {};

  console.log('loadCsvMarkers: Processing', rows.length, 'rows');
  if (rows.length > 0) {
    console.log('Sample row keys:', Object.keys(rows[0]));
    console.log('Sample row full data:', JSON.stringify(rows[0], null, 2));
    console.log('Checking fields:', {
      sensor_id: rows[0].sensor_id,
      latitude: rows[0].latitude,
      longitude: rows[0].longitude,
      hasLatitude: 'latitude' in rows[0],
      hasLongitude: 'longitude' in rows[0],
    });
  }

  rows.forEach((row) => ingestRow(row, state));

  console.log('Unique sensors found:', Object.keys(state.sensorData).length);

  state.markers = Object.values(state.sensorData).map((entry) =>
    createMarker(entry, onClick),
  );

  console.log('Markers created:', state.markers.length);
}

export function ingestRow(row, state) {
  const sensorId = row.sensor_id || row.sensorId;
  const lat = parseFloat(row.latitude ?? row.lat);
  const lon = parseFloat(row.longitude ?? row.lon ?? row.lng);

  if (!sensorId || Number.isNaN(lat) || Number.isNaN(lon)) {
    console.warn('Skipping row - missing data:', {
      sensorId,
      lat,
      lon,
      hasLatitude: 'latitude' in row,
      hasLat: 'lat' in row,
      hasLongitude: 'longitude' in row,
      hasLon: 'lon' in row,
    });
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
