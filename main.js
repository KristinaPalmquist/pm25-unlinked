import {fetchPredictions, fetchLatestBatc, interpolationBase} from './frontend/api.js';

const predictions = await fetchPredictions();

async function loadMarkersFromBackend() {
  const rows = await fetchLatestBatch();
  rows.forEach(row => ingestRow(row)); // reuse your existing ingestRow logic
  Object.values(state.sensorData).forEach(entry => {
    const marker = createMarker(entry);
    marker.addTo(map);
  });
}

fetch('./utils/coordinates.json')
  .then(response => response.json())
  .then(gridBounds => {
    // Use gridBounds here to set up your config
    const config = {
      forecastDays: [0, 1, 2, 3, 4, 5, 6],
      interpolationBase: interpolationBase,
      interpolationTemplate: 'forecast_interpolation_{day}d.png',
      // interpolationBase: './models/interpolation',
      // interpolationTemplate: 'forecast_interpolation_{day}d.png',
      predictionsCsv: './models/predictions.csv',
      mapBounds: [
        gridBounds.MIN_LONGITUDE,
        gridBounds.MIN_LATITUDE,
        gridBounds.MAX_LONGITUDE,
        gridBounds.MAX_LATITUDE
      ],
      mapCenter: [gridBounds.CENTER_LONGITUDE, gridBounds.CENTER_LATITUDE],
      mapZoom: 3,
    };
    
  const AQI_COLORS = ['#00e400', '#ffff00', '#ff7e00', '#ff0000'];
  const AQI_THRESHOLDS = [50, 100, 150];

  const ui = {
    dayDropdown: document.getElementById('forecast-dropdown'),
    sensorToggle: document.getElementById('toggle-sensors'),
    overlayToggle: document.getElementById('toggle-overlay'),
    focusPanel: document.getElementById('focus-panel'),
    focusName: document.getElementById('focus-name'),
    focusMeta: document.getElementById('focus-meta'),
    focusDetailsBtn: document.getElementById('focus-details-btn'),
    imageModal: document.getElementById('image-modal'),
    imageModalImg: document.getElementById('image-modal-img'),
    imageModalClose: document.getElementById('image-modal-close'),
    imageModalBackdrop: document.getElementById('image-modal-backdrop'),
    detailsModal: document.getElementById('details-modal'),
    detailsModalTitle: document.getElementById('details-modal-title'),
    detailsModalClose: document.getElementById('details-modal-close'),
    detailsModalBackdrop: document.getElementById('details-modal-backdrop'),
    detailsTableHead: document.getElementById('details-table-head'),
    detailsTableBody: document.getElementById('details-table-body'),
  };

  const state = {
    currentDay: Number(ui.dayDropdown?.value ?? config.forecastDays[0]),
    sensorData: {},
    csvHeaders: [],
    markers: [],
    activeMarkerEl: null,
    modals: { image: false, details: false },
    dayDates: {},
  };

  const hiddenColumns = new Set(['longitude', 'latitude', 'sensor_id', 'city_y', 'city_x', 'street', 'country', 'feed_url']);
  const sourceId = 'pm25-interpolation';
  const layerId = 'pm25-interpolation-layer';

  const map = new maplibregl.Map({
    container: 'map',
    style: {
      version: 8,
      sources: {
        osm: {
          type: 'raster',
          tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
          tileSize: 256,
          attribution: '© OpenStreetMap',
        },
      },
      layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
    },
    center: config.mapCenter,
    zoom: config.mapZoom,
    maxZoom: 14,
    maxBounds: [
      [config.mapBounds[0], config.mapBounds[1]],
      [config.mapBounds[2], config.mapBounds[3]],
    ],
  });


  map.on('load', async () => {
    await loadRaster(state.currentDay);
    await loadMarkersFromBackend();
  });

  map.addControl(new maplibregl.NavigationControl(), 'top-right');

  function init() {
    populateDropdown();
    if (ui.dayDropdown) ui.dayDropdown.value = String(state.currentDay);

    ui.dayDropdown?.addEventListener('change', (e) => {
      const day = Number(e.target.value);
      state.currentDay = day;
      loadRaster(day);
      if (state.activeMarkerEl && ui.focusDetailsBtn?.dataset?.sensorId) {
        updateFocusPanelValue(ui.focusDetailsBtn.dataset.sensorId);
      }
    });

    ui.overlayToggle?.addEventListener('change', () => {
      ui.overlayToggle.checked ? loadRaster(state.currentDay) : removeRasterLayer();
    });

    ui.sensorToggle?.addEventListener('change', () => {
      state.markers.forEach((m) => (ui.sensorToggle.checked ? m.addTo(map) : m.remove()));
      if (!ui.sensorToggle.checked) clearFocus();
    });

    ui.focusDetailsBtn?.addEventListener('click', () => {
      if (ui.focusDetailsBtn.dataset.sensorId) openDetailsModal(ui.focusDetailsBtn.dataset.sensorId);
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

    map.on('load', async () => {
      await loadRaster(state.currentDay);
      await loadCsvMarkers();
    });

    map.on('click', (e) => {
      if (!e.originalEvent?.target?.classList?.contains('sensor-marker')) clearFocus();
    });
  }

  function formatDateLabel(dateStr) {
    if (!dateStr) return null;
    const date = new Date(`${dateStr}`);
    return Number.isNaN(date.getTime()) ? null : date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
  }

  function formatDayLabel(day) {
    const formatted = formatDateLabel(state.dayDates?.[day]);
    if (formatted) return day === 0 ? `Observed ${formatted}` : `Forecast ${formatted}`;
    return `Day ${day}`;
  }

  function populateDropdown() {
    if (!ui.dayDropdown) return;
    ui.dayDropdown.innerHTML = '';
    config.forecastDays.forEach((day) => {
      if (day === 0 || state.dayDates[day]) {
        const option = document.createElement('option');
        option.value = String(day);
        option.textContent = formatDayLabel(day);
        ui.dayDropdown.appendChild(option);
      }
    });
  }

  function deriveDayDates(rows) {
    const dayDates = {};
    
    // Look for actual measurements first, then fall back to using today's date
    const actualDates = rows
      .filter((r) => r.date && Number.isFinite(Number.parseFloat(r.pm25 ?? '')))
      .map((r) => r.date)
      .sort();
    
    // For day 0, use the latest actual measurement date, or today's date if no actuals
    let baseDate;
    if (actualDates.length) {
      baseDate = new Date(actualDates[actualDates.length - 1]);
      dayDates[0] = baseDate.toISOString().split('T')[0];
    } else {
      baseDate = new Date();
      dayDates[0] = baseDate.toISOString().split('T')[0];
    }

    rows.forEach((row) => {
      const offset = Number(row.days_before_forecast_day);
      if (!row.date) return;
      if (Number.isFinite(offset) && offset >= 1 && !dayDates[offset]) {
        const d = new Date(baseDate);
        d.setDate(baseDate.getDate() + offset);
        dayDates[offset] = d.toISOString().split('T')[0];
      }
  });
    return dayDates;
  }

  function buildRasterUrl(day) {
    return `${config.interpolationBase}/${config.interpolationTemplate.replace('{day}', day)}`;
  }

  function waitForStyle() {
    return new Promise((resolve) => (map.isStyleLoaded() ? resolve() : map.once('styledata', resolve)));
  }

  function removeRasterLayer() {
    if (map.getLayer(layerId)) map.removeLayer(layerId);
    if (map.getSource(sourceId)) map.removeSource(sourceId);
  }

  async function loadRaster(day) {
    state.currentDay = day;
    if (ui.dayDropdown) ui.dayDropdown.value = String(day);
    if (ui.overlayToggle && !ui.overlayToggle.checked) {
      removeRasterLayer();
      return;
    }

    await waitForStyle();
    removeRasterLayer();

    map.addSource(sourceId, {
      type: 'image',
      url: buildRasterUrl(day),
      coordinates: [
        [config.mapBounds[0], config.mapBounds[3]],
        [config.mapBounds[2], config.mapBounds[3]],
        [config.mapBounds[2], config.mapBounds[1]],
        [config.mapBounds[0], config.mapBounds[1]],
      ],
    });

    map.addLayer({
      id: layerId,
      type: 'raster',
      source: sourceId,
      paint: { 'raster-opacity': 0.75, 'raster-resampling': 'linear' },
    });
  }

  function splitCsvLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i += 1) {
      const char = line[i];
      if (char === '"') inQuotes = !inQuotes;
      else if (char === ',' && !inQuotes) {
        result.push(current);
        current = '';
      } else current += char;
    }
    result.push(current);
    return result.map((cell) => cell.replace(/^"|"$/g, '').trim());
  }

  function parseCsv(text) {
    const lines = text.trim().split(/\r?\n/);
    if (!lines.length) return [];
    const headers = splitCsvLine(lines[0]);
    return lines.slice(1).map((line) => {
      const cells = splitCsvLine(line);
      return headers.reduce((acc, key, idx) => {
        acc[key] = cells[idx] ?? '';
        return acc;
      }, {});
    });
  }

  async function loadCsvMarkers() {
  if (!predictions.length) return; // nothing loaded yet

  try {
    const rows = predictions; // already JSON objects from backend

    state.csvHeaders = rows.length ? Object.keys(rows[0]) : [];
    state.dayDates = deriveDayDates(rows);
    state.markers.forEach((m) => m.remove());
    state.markers = [];
    state.sensorData = {};
    clearFocus();

    rows.forEach((row) => ingestRow(row));
    state.markers = Object.values(state.sensorData).map(createMarker);

    populateDropdown();
    if (ui.dayDropdown) ui.dayDropdown.value = String(state.currentDay);
    } catch (error) {
      console.error("Failed to load predictions", error);
    }
  }

  // async function loadCsvMarkers() {
  //   if (!config.predictionsCsv) return;
  //   try {
  //     const response = await fetch(config.predictionsCsv);
  //     if (!response.ok) throw new Error(`Failed to fetch CSV (${response.status})`);
  //     const rows = parseCsv(await response.text());
  //     state.csvHeaders = rows.length ? Object.keys(rows[0]) : [];
  //     state.dayDates = deriveDayDates(rows);
  //     state.markers.forEach((m) => m.remove());
  //     state.markers = [];
  //     state.sensorData = {};
  //     clearFocus();
      
  //     rows.forEach((row) => ingestRow(row));
  //     state.markers = Object.values(state.sensorData).map(createMarker);
      
  //     populateDropdown();
  //     if (ui.dayDropdown) ui.dayDropdown.value = String(state.currentDay);
  //   } catch (error) {
  //     console.error('Failed to load predictions CSV', error);
  //   }
  // }

  function ingestRow(row) {
    const sensorId = row.sensor_id || row.sensorId;
    const lat = parseFloat(row.latitude ?? row.lat);
    const lon = parseFloat(row.longitude ?? row.lon ?? row.lng);
    
    if (!sensorId || Number.isNaN(lat) || Number.isNaN(lon)) return;

    const street = row.street || row.location || '';
    const city = row.city_y || row.city_x || '';

    if (!state.sensorData[sensorId]) {
      state.sensorData[sensorId] = { sensorId, lat, lon, city, street, latestValue: null, rows: [] };
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

  function getAQIColor(aqi) {
    for (let i = 0; i < AQI_THRESHOLDS.length; i += 1) {
      if (aqi < AQI_THRESHOLDS[i]) return AQI_COLORS[i];
    }
    return AQI_COLORS[AQI_COLORS.length - 1];
  }

  function buildPopupHtml(entry) {
    const name = entry.street || entry.sensorId;
    const location = entry.city ? `${entry.city}<br/>` : '';
    const reading = Number.isFinite(entry.latestValue) ? `PM2.5: ${entry.latestValue.toFixed(1)}` : 'No recent value';
    return `<strong>${name}</strong><br/>${location}${reading}`;
  }

  function createMarker(entry) {
    const element = document.createElement('div');
    element.className = 'sensor-marker';
    element.style.background = getAQIColor(entry.latestValue ?? 0);
    element.addEventListener('click', (e) => {
      e.stopPropagation();
      focusOnSensor(entry.sensorId, element);
    });

    const marker = new maplibregl.Marker({ element })
      .setLngLat([entry.lon, entry.lat])
      .setPopup(new maplibregl.Popup({ closeButton: false, offset: 12 }).setHTML(buildPopupHtml(entry)));

    if (ui.sensorToggle?.checked ?? true) marker.addTo(map);
    return marker;
  }

  function showFocusPanel() {
    if (!ui.focusPanel) return;
    ui.focusPanel.style.display = 'flex';
    requestAnimationFrame(() => {
      ui.focusPanel.style.opacity = '1';
    });
  }

  function hideFocusPanel() {
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

  function getValueForDay(data, day) {
    if (!data.rows?.length) return null;
    
    const row = day === 0
      ? data.rows.find((r) => r.date === state.dayDates[0])
      : data.rows.find((r) => Number(r.days_before_forecast_day ?? r.daysBeforeForecastDay ?? 'NaN') === day);
    
    if (!row) return null;
    
    const value = day === 0
      ? parseFloat(row.pm25 ?? 'NaN')
      : parseFloat(row.predicted_pm25 ?? row.predicted ?? 'NaN');
    
    return Number.isFinite(value) ? value : null;
  }

  function updateFocusPanelValue(sensorId) {
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

  function focusOnSensor(sensorId, markerEl) {
    const data = state.sensorData[sensorId];
    if (!data) return;

    showFocusPanel();

    if (state.activeMarkerEl && state.activeMarkerEl !== markerEl) state.activeMarkerEl.classList.remove('is-active');
    state.activeMarkerEl = markerEl;
    markerEl.classList.add('is-active');

    updateFocusPanelValue(sensorId);
    
    if (ui.focusDetailsBtn) {
      ui.focusDetailsBtn.disabled = !(data.rows && data.rows.length);
      ui.focusDetailsBtn.dataset.sensorId = data.sensorId;
    }

    updateFocusImage('forecast-card', 'focus-forecast-thumb', `./models/${sensorId}/images/forecast.png`);
    updateFocusImage('hindcast-card', 'focus-hindcast-thumb', `./models/${sensorId}/images/hindcast_prediction.png`);

    map.flyTo({ center: [data.lon, data.lat], zoom: Math.max(map.getZoom(), 11), speed: 0.3 });
  }

  function clearFocus() {
    if (state.activeMarkerEl) {
      state.activeMarkerEl.classList.remove('is-active');
      state.activeMarkerEl = null;
    }
    hideFocusPanel();
  }

  function updateFocusImage(cardId, thumbId, url) {
    const cardEl = document.getElementById(cardId);
    const thumbEl = document.getElementById(thumbId);
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

  function hideFocusImage(cardId, thumbId) {
    const cardEl = document.getElementById(cardId);
    const thumbEl = document.getElementById(thumbId);
    if (!cardEl || !thumbEl) return;
    thumbEl.src = '';
    thumbEl.classList.add('hidden');
    cardEl.classList.add('hidden');
    thumbEl.onclick = null;
  }

  function openImageModal(src) {
    if (!ui.imageModal || !ui.imageModalImg) return;
    ui.imageModalImg.src = src;
    ui.imageModal.classList.remove('hidden');
    state.modals.image = true;
  }

  function closeImageModal() {
    if (!ui.imageModal || !ui.imageModalImg) return;
    ui.imageModal.classList.add('hidden');
    ui.imageModalImg.src = '';
    state.modals.image = false;
  }

  function openDetailsModal(sensorId) {
    if (!ui.detailsModal) return;
    const entry = state.sensorData[sensorId];
    if (!entry || !entry.rows.length) return;

    if (ui.detailsModalTitle) {
      const parts = [entry.street, entry.city].filter(Boolean);
      ui.detailsModalTitle.textContent = parts.length ? parts.join(', ') : entry.sensorId;
    }

    renderDetailsTable(entry);
    ui.detailsModal.classList.remove('hidden');
    state.modals.details = true;
  }

  function closeDetailsModal() {
    if (!ui.detailsModal) return;
    ui.detailsModal.classList.add('hidden');
    state.modals.details = false;
  }

  function renderDetailsTable(entry) {
    if (!ui.detailsTableHead || !ui.detailsTableBody) return;
    const headers = (state.csvHeaders.length ? state.csvHeaders : Object.keys(entry.rows[0] || {})).filter((h) => !hiddenColumns.has(h));
    if (!headers.length) return;

    ui.detailsTableHead.innerHTML = '';
    ui.detailsTableBody.innerHTML = '';

    const headRow = document.createElement('tr');
    headers.forEach((h) => {
      const th = document.createElement('th');
      th.textContent = h;
      headRow.appendChild(th);
    });
    ui.detailsTableHead.appendChild(headRow);

    entry.rows.forEach((row) => {
      const tr = document.createElement('tr');
      headers.forEach((h) => {
        const td = document.createElement('td');
        const value = row[h] ?? '';
        const isDateColumn = h.toLowerCase() === 'date';
        const numValue = parseFloat(value);
        td.textContent = !isDateColumn && Number.isFinite(numValue) ? numValue.toFixed(3) : value;
        tr.appendChild(td);
      });
      ui.detailsTableBody.appendChild(tr);
    });
  }

  init();

  });


  console.log('PM2.5 Forecast Map initialized');
  console.log('Predictions loaded:', predictions.length);