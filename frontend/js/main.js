import { fetchPredictions, fetchLatestBatch, interpolationBase } from './frontend/api.js';
import { fetchPredictions } from './api/predictions.js';
import { loadCoordinates } from './utils/coordinates.js';
import { buildMapConfig } from './config/mapConfig.js';
import { initMap } from './ui/maps.js';
import { initControls, state } from './ui/initControls.js';
import { loadRaster, removeRasterLayer, loadMarkersFromBackend, updateFocusPanelValue, clearFocus, loadCsvMarkers } from './ui/layers.js';
import { formatDayLabel } from './utils/dateUtils.js';
import { createMarker } from './ui/layers.js';
import { handleMarkerClick } from './ui/initControls.js';
import { loadCsvMarkers } from './ui/layers.js';
import { updateUiAfterCsvLoad } from './ui/initControls.js';


async function main() {
  //  Fetch predictions and coordinates
  const [predictions, gridBounds] = await Promise.all([
    fetchPredictions(),
    loadCoordinates(),
  ]);

  // Build config
  const config = buildMapConfig(gridBounds, interpolationBase);

  state.currentDay = Number(ui.dayDropdown?.value ?? config.forecastDays[0])

  // Initialize map
  initMap({ predictions, config });

  // Initialize UI controls
  initControls(map, config, { 
    loadRaster, 
    removeRasterLayer, 
    updateFocusPanelValue, 
    clearFocus, 
    openDetailsModal, 
    closeImageModal, 
    closeDetailsModal, 
    formatDayLabel 
  });

  // Load initial raster and markers
  map.on('load', async () => {
    await loadRaster(state.currentDay);
    await loadMarkersFromBackend();
  });

  const marker = createMarker(entry, (sensorId, el) => {
    handleMarkerClick(sensorId, el, map);
  });
  marker.addTo(map);

  const rows = predictions;

  loadCsvMarkers(rows, state, ingestRow, createMarker);
  updateUiAfterCsvLoad(ui, state);

  console.log('PM2.5 Forecast Map initialized');
  console.log('Predictions loaded:', predictions.length);
}

main()

