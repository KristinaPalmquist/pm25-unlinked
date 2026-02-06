import { fetchPredictions, interpolationBase } from './api.js';
import { buildMapConfig } from './config/mapConfig.js';
import {
  buildRasterUrl,
  clearFocus,
  closeDetailsModal,
  closeImageModal,
  initControls,
  initMap,
  loadCsvMarkers,
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

  // Set region name from config
  const regionNameEl = document.getElementById('region-name');
  if (regionNameEl && gridBounds.REGION_NAME) {
    regionNameEl.textContent = ' – ' + gridBounds.REGION_NAME;
  }

  // Build config
  const config = buildMapConfig(gridBounds, interpolationBase);

  state.currentDay = 0; // Default to today

  // Initialize map
  const map = initMap(config);

  // Store predictions in state
  state.predictions = predictions;

  // Load initial raster and markers
  map.on('load', async () => {
    // Only try to load overlay if there are predictions (API is working)
    if (predictions && predictions.length > 0) {
      // Load sensor markers from predictions
      loadCsvMarkers(predictions, state, (sensorId, markerElement) => {
        openDetailsModal(sensorId, markerElement, map, state);
      });

      // Add markers to map and set initial visibility based on toggle state
      const showMarkers =
        ui.sensorToggle && ui.sensorToggle.dataset.active === 'true';

      state.markers.forEach((marker) => {
        marker.addTo(map);
        const element = marker.getElement();
        if (element) {
          element.style.display = showMarkers ? 'block' : 'none';
        }
      });

      console.log(`✅ Sensor markers loaded: ${state.markers.length}`);

      // Initialize UI controls after markers are loaded
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

      if (config.forecastDays && config.forecastDays.length > 0) {
        // Check if overlay toggle is active
        const overlayActive =
          ui.overlayToggle && ui.overlayToggle.dataset.active === 'true';

        if (overlayActive) {
          // Add heatmap-active class for opaque UI backgrounds
          document.body.classList.add('heatmap-active');

          try {
            await loadRaster(map, config, state.currentDay, state);
          } catch (err) {
            console.error(
              `❌ Could not load interpolation overlay for day ${state.currentDay}:`,
              err,
            );
            console.error(
              '   Image URL:',
              buildRasterUrl(state.currentDay, config),
            );
            // Don't disable the toggle - user might want to try other days
            document.body.classList.remove('heatmap-active');
          }
        }
      }
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

      // Initialize controls even without predictions
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
    }
  });

  console.log('PM2.5 Forecast Map initialized!');
  console.log('✅ Predictions loaded:', predictions.length);
}

main();
