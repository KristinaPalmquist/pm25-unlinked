import { fetchPredictions, interpolationBase } from './api.js';
import { buildMapConfig } from './config/mapConfig.js';
import {
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
    console.log('Map loaded state at script start:', map.loaded());

    console.log('🗺️ Map load event fired');
    console.log('Predictions array:', predictions);
    console.log('Predictions length:', predictions?.length);
    console.log('Predictions check:', predictions && predictions.length > 0);

    // Only try to load overlay if we have predictions (API is working)
    if (predictions && predictions.length > 0) {
      console.log(
        '🔵 About to call loadCsvMarkers with',
        predictions.length,
        'rows',
      );

      // Load sensor markers from predictions FIRST
      loadCsvMarkers(predictions, state, (sensorId, markerElement) => {
        console.log(`Marker clicked: Sensor ID ${sensorId}`);
        openDetailsModal(sensorId, markerElement, map, state);
      });

      console.log('🔵 After loadCsvMarkers call');
      console.log('State.markers:', state.markers);
      console.log(
        'State.sensorData:',
        Object.keys(state.sensorData || {}).length,
        'sensors',
      );

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

      console.log(`✅ Loaded ${state.markers.length} sensor markers`);

      // NOW initialize UI controls after markers are loaded
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
            console.error('Could not load interpolation overlay:', err);
            // Disable overlay toggle since it won't work
            if (ui.overlayToggle) {
              ui.overlayToggle.dataset.active = 'false';
              ui.overlayToggle.disabled = true;
              document.body.classList.remove('heatmap-active');
            }
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

      // Initialize controls even without predictions (for day selector, etc.)
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

  console.log('PM2.5 Forecast Map initialized');
  console.log('Predictions loaded:', predictions.length);
}

main();
