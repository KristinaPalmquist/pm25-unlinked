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
    formatDayLabel,
  });

  // Load initial raster and markers
  map.on("load", async () => {
    await loadRaster(state.currentDay);
    await loadMarkersFromBackend();
  });

  const marker = createMarker(entry, (sensorId, el) => {
    handleMarkerClick(sensorId, el, map);
  });
  marker.addTo(map);

  const rows = predictions;

  loadCsvMarkers(rows, state, ingestRow, createMarker);

  console.log("PM2.5 Forecast Map initialized");
  console.log("Predictions loaded:", predictions.length);
}

main();
