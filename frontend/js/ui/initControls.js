import { populateDropdown } from "./dropdown.js";
import { ui } from "./elements.js";
import { state } from "./state.js";

export function initControls(
  map,
  config,
  {
    loadRaster,
    removeRasterLayer,
    updateFocusPanelValue,
    clearFocus,
    openDetailsModal,
    closeImageModal,
    closeDetailsModal,
    formatDayLabel,
  },
) {
  populateDropdown(config, (day) => formatDayLabel(day, state.dayDates));

  ui.dayDropdown.value = String(state.currentDay);

  ui.dayDropdown?.addEventListener("change", (e) => {
    const day = Number(e.target.value);
    state.currentDay = day;
    loadRaster(day);

    if (state.activeMarkerEl && ui.focusDetailsBtn?.dataset?.sensorId) {
      updateFocusPanelValue(ui.focusDetailsBtn.dataset.sensorId);
    }
  });

  ui.overlayToggle?.addEventListener("change", () => {
    ui.overlayToggle.checked
      ? loadRaster(state.currentDay)
      : removeRasterLayer();
  });

  ui.sensorToggle?.addEventListener("change", () => {
    state.markers.forEach((m) =>
      ui.sensorToggle.checked ? m.addTo(map) : m.remove(),
    );
    if (!ui.sensorToggle.checked) clearFocus();
  });

  ui.focusDetailsBtn?.addEventListener("click", () => {
    if (ui.focusDetailsBtn.dataset.sensorId)
      openDetailsModal(ui.focusDetailsBtn.dataset.sensorId);
  });
  ui.imageModalClose?.addEventListener("click", closeImageModal);
  ui.imageModalBackdrop?.addEventListener("click", closeImageModal);
  ui.detailsModalClose?.addEventListener("click", closeDetailsModal);
  ui.detailsModalBackdrop?.addEventListener("click", closeDetailsModal);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (state.modals.image) closeImageModal();
      if (state.modals.details) closeDetailsModal();
    }
  });

  map.on("click", (e) => {
    if (!e.originalEvent?.target?.classList?.contains("sensor-marker"))
      clearFocus();
  });
}
