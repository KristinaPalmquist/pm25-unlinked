import { fetchPredictions, interpolationBase } from "./api.js";
import { buildMapConfig } from "./config/mapConfig.js";
import {
  clearFocus,
  createMarker,
  handleMarkerClick,
  initControls,
  initMap,
  loadCsvMarkers,
  loadMarkersFromBackend,
  loadRaster,
  removeRasterLayer,
  state,
  ui,
  updateFocusPanelValue,
} from "./ui/index.js";
import { formatDayLabel, loadCoordinates } from "./utils/index.js";

async function main() {
  //  Fetch predictions and coordinates
  const [predictions, gridBounds] = await Promise.all([
    fetchPredictions(),
    loadCoordinates(),
  ]);

  // Build config
  const config = buildMapConfig(gridBounds, interpolationBase);

  state.currentDay = Number(ui.dayDropdown?.value ?? config.forecastDays[0]);

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
  map.on("load", async () => {
    if (config.forecastDays && config.forecastDays.length > 0) {
      await loadRaster(map, config, state.currentDay, state);
    }
    
    // Load markers from predictions if available
    if (predictions && predictions.length > 0) {
      console.log('Loading markers from predictions:', predictions.length);
      // TODO: Implement marker loading from predictions
    }
  });

  console.log("PM2.5 Forecast Map initialized");
  console.log("Predictions loaded:", predictions.length);
}

main();
