import { ui } from './elements.js';
import { state } from './state.js';
import { getValueForDay } from '../utils/valueUtils.js';
import { openImageModal } from './modals.js';
import { getCardElements } from './elements.js';


export function showFocusPanel() {
    if (!ui.focusPanel) return;
    ui.focusPanel.style.display = 'flex';
    requestAnimationFrame(() => {
        ui.focusPanel.style.opacity = '1';
    });
}

export function hideFocusPanel() {
    if (!ui.focusPanel) return;
    ui.focusPanel.style.opacity = '0';
    setTimeout(() => {
        if (ui.focusPanel) {
        ui.focusPanel.style.display = 'none';
        if (ui.focusName) ui.focusName.textContent = '';
        if (ui.focusMeta) ui.focusMeta.textContent = '';
        if (ui.focusDetailsBtn) {
            ui.focusDetailsBtn.disabled = true;
            ui.focusDetailsBtn.dataset.sensorId = '';
        }
        hideFocusImage('forecast-card', 'focus-forecast-thumb');
        hideFocusImage('hindcast-card', 'focus-hindcast-thumb');
        }
    }, 100);
}

export function updateFocusPanelValue(sensorId) {
  const data = state.sensorData[sensorId];
  if (!data) return;
  
  const dayValue = getValueForDay(data, state.currentDay);
  const valueText = Number.isFinite(dayValue) ? `${dayValue.toFixed(1)} µg/m<sup>3</sup>` : 'No value';
  
  if (ui.focusName) {
    const parts = [data.street || '', data.city || ''].filter(Boolean);
    const name = parts.length ? parts.join(', ') : data.sensorId;
    ui.focusName.innerHTML = `${name}, ${valueText}`;
  }
  
  if (ui.focusMeta) {
    const lat = Number.isFinite(data.lat) ? data.lat.toFixed(4) : '—';
    const lon = Number.isFinite(data.lon) ? data.lon.toFixed(4) : '—';
    ui.focusMeta.textContent = `Lat ${lat}, Lon ${lon}, ID ${data.sensorId ?? '—'}`;
  }
}

export function updateFocusImage(cardId, thumbId, url) {
  const { cardEl, thumbEl } = getCardElements(cardId, thumbId);
  if (!cardEl || !thumbEl) return;

  fetch(url, { method: 'HEAD' })
    .then((response) => {
      if (response.ok) {
        thumbEl.src = url;
        thumbEl.classList.remove('hidden');
        cardEl.classList.remove('hidden');
        thumbEl.onclick = () => openImageModal(url);
      } else {
        hideFocusImage(cardId, thumbId);
      }
    })
    .catch(() => hideFocusImage(cardId, thumbId));
}

export function hideFocusImage(cardId, thumbId) {
  const { cardEl, thumbEl } = getCardElements(cardId, thumbId);
  if (!cardEl || !thumbEl) return;
  thumbEl.src = '';
  thumbEl.classList.add('hidden');
  cardEl.classList.add('hidden');
  thumbEl.onclick = null;
}

export function clearFocus() {
  if (state.activeMarkerEl) {
    state.activeMarkerEl.classList.remove('is-active');
    state.activeMarkerEl = null;
  }
  hideFocusPanel();
}

export function handleMarkerClick(sensorId, markerEl, map) {
  const data = state.sensorData[sensorId];
  if (!data) return;

  showFocusPanel();

  if (state.activeMarkerEl && state.activeMarkerEl !== markerEl)
    state.activeMarkerEl.classList.remove('is-active');

  state.activeMarkerEl = markerEl;
  markerEl.classList.add('is-active');

  updateFocusPanelValue(sensorId);

  ui.focusDetailsBtn.disabled = !(data.rows && data.rows.length);
  ui.focusDetailsBtn.dataset.sensorId = sensorId;

  updateFocusImage('forecast-card', 'focus-forecast-thumb', `./models/${sensorId}/images/forecast.png`);
  updateFocusImage('hindcast-card', 'focus-hindcast-thumb', `./models/${sensorId}/images/hindcast_prediction.png`);

  map.flyTo({
    center: [data.lon, data.lat],
    zoom: Math.max(map.getZoom(), 11),
    speed: 0.3
  });
}