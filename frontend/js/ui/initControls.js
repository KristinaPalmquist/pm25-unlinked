import { state, ui } from './index.js';

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
  // Set weekday labels dynamically
  const today = new Date();
  const weekdays = [
    'Sunday',
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
  ];

  document.querySelectorAll('.weekday-label').forEach((label, index) => {
    const dayOffset = index + 2; // Start from day +2
    const futureDate = new Date(today);
    futureDate.setDate(today.getDate() + dayOffset);
    label.textContent = weekdays[futureDate.getDay()];
  });

  // Initialize day buttons
  ui.dayButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const day = Number(button.dataset.day);
      state.currentDay = day;

      // Update active state for all buttons
      ui.dayButtons.forEach((btn) => {
        const isActive = btn.dataset.day === String(day);
        btn.dataset.active = isActive ? 'true' : 'false';
      });

      // Only load raster if overlay is enabled
      if (ui.overlayToggle?.dataset.active === 'true') {
        loadRaster(map, config, day, state);
      }

      if (state.activeMarkerEl && ui.focusDetailsBtn?.dataset?.sensorId) {
        updateFocusPanelValue(ui.focusDetailsBtn.dataset.sensorId);
      }
    });
  });

  ui.overlayToggle?.addEventListener('click', () => {
    const isActive = ui.overlayToggle.dataset.active === 'true';
    const newActive = !isActive;
    ui.overlayToggle.dataset.active = String(newActive);

    if (newActive) {
      loadRaster(map, config, state.currentDay, state);
    } else {
      removeRasterLayer(map);
    }
  });

  ui.sensorToggle?.addEventListener('click', () => {
    const isActive = ui.sensorToggle.dataset.active === 'true';
    const newActive = !isActive;
    ui.sensorToggle.dataset.active = String(newActive);

    // Toggle marker visibility by changing display style
    state.markers.forEach((marker) => {
      const element = marker.getElement();
      if (element) {
        element.style.display = newActive ? 'block' : 'none';
      }
    });

    if (!newActive) clearFocus();
  });

  ui.focusDetailsBtn?.addEventListener('click', () => {
    if (ui.focusDetailsBtn.dataset.sensorId)
      openDetailsModal(ui.focusDetailsBtn.dataset.sensorId);
  });
  ui.imageModalClose?.addEventListener('click', closeImageModal);
  ui.imageModalBackdrop?.addEventListener('click', closeImageModal);
  ui.detailsModalClose?.addEventListener('click', closeDetailsModal);
  ui.detailsModalBackdrop?.addEventListener('click', closeDetailsModal);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (state.modals.image) closeImageModal();
      if (state.modals.details) closeDetailsModal();
    }
  });

  map.on('click', (e) => {
    if (!e.originalEvent?.target?.classList?.contains('sensor-marker'))
      clearFocus();
  });
}
