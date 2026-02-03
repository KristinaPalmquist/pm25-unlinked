import { fetchPredictions, interpolationBase } from './api.js';
import { buildMapConfig } from './config/mapConfig.js';
import {
  clearFocus,
  closeDetailsModal,
  closeImageModal,
  createMarker,
  handleMarkerClick,
  initControls,
  initMap,
  loadCsvMarkers,
  loadMarkersFromBackend,
  loadRaster,
  openDetailsModal,
  removeRasterLayer,
  state,
  ui,
  updateFocusPanelValue,
} from './ui/index.js';
import { formatDayLabel, loadCoordinates } from './utils/index.js';

async function main() {
  //  Fetch predictions and coordinates
  const [predictions, gridBounds] = await Promise.all([
    fetchPredictions(),
    loadCoordinates(),
  ]);

  // Build config
  const config = buildMapConfig(gridBounds, interpolationBase);

  state.currentDay = 0; // Default to today

  // Initialize map
  const map = initMap(config);

  // Store predictions in state
  state.predictions = predictions;

  // Initialize UI controls
  initControls(map, config, {
    loadRaster,
    removeRasterLayer,
    updateFocusPanelValue,
    clearFocus,
    openDetailsModal,
    closeImageModal,
    closeDetailsModal,
    formatDayLabel,
  });

  // Load initial raster and markers
  map.on('load', async () => {
    // Only try to load overlay if we have predictions (API is working)
    if (predictions && predictions.length > 0) {
      console.log('Loading markers from predictions:', predictions.length);

      if (config.forecastDays && config.forecastDays.length > 0) {
        try {
          await loadRaster(map, config, state.currentDay, state);
        } catch (err) {
          console.warn('Could not load interpolation overlay:', err.message);
          // Disable overlay toggle since it won't work
          if (ui.overlayToggle) {
            ui.overlayToggle.dataset.active = 'false';
            ui.overlayToggle.disabled = true;
          }
        }
      }
      // TODO: Implement marker loading from predictions
    } else {
      console.info('📍 No predictions available yet.');
      console.info('ℹ️  To enable the map overlay and sensors:');
      console.info(
        '   1. Set HOPSWORKS_API_KEY in Netlify environment variables',
      );
      console.info(
        '   2. Run notebook 4 (batch inference) to generate predictions',
      );
      console.info('   3. Redeploy the site');

      // Disable overlay and sensor toggles
      if (ui.overlayToggle) {
        ui.overlayToggle.dataset.active = 'false';
        ui.overlayToggle.disabled = true;
      }
      if (ui.sensorToggle) {
        ui.sensorToggle.dataset.active = 'false';
        ui.sensorToggle.disabled = true;
      }
    }
  });

  console.log('PM2.5 Forecast Map initialized');
  console.log('Predictions loaded:', predictions.length);
}

main();
