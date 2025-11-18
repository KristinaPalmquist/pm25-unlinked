const FORECAST_DAYS = [0, 1, 2, 3, 4, 5, 6, 7];
const INTERPOLATION_BASE_URL = './models/interpolation';
const INTERPOLATION_TEMPLATE = 'forecast_interpolation_{day}d.png';
const PREDICTIONS_CSV_PATH = './models/predictions.csv';
const MAP_BOUNDS = [11.4, 57.15, 12.5, 58.25];
const MAP_CENTER = [11.9746, 57.7089];
const MAP_ZOOM = 11;

const daySlider = document.getElementById('forecast-slider');
const sliderValue = document.getElementById('slider-value');
const statusEl = document.getElementById('status');
const sensorToggle = document.getElementById('toggle-sensors');
const overlayToggle = document.getElementById('toggle-overlay');
const focusPanel = document.getElementById('focus-panel');
const focusNameEl = document.getElementById('focus-name');
const focusMetaEl = document.getElementById('focus-meta');
const focusDetailsBtn = document.getElementById('focus-details-btn');
const imageModal = document.getElementById('image-modal');
const imageModalImg = document.getElementById('image-modal-img');
const imageModalClose = document.getElementById('image-modal-close');
const imageModalBackdrop = document.getElementById('image-modal-backdrop');
const detailsModal = document.getElementById('details-modal');
const detailsModalTitle = document.getElementById('details-modal-title');
const detailsTableHead = document.getElementById('details-table-head');
const detailsTableBody = document.getElementById('details-table-body');
const detailsModalClose = document.getElementById('details-modal-close');
const detailsModalBackdrop = document.getElementById('details-modal-backdrop');

const state = {
  currentDay: Number(daySlider?.value || FORECAST_DAYS[0]),
  sensorData: {},
  csvHeaders: [],
  csvMarkers: [],
  activeMarkerEl: null,
  modalActive: false,
  detailsModalActive: false,
};

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
  center: MAP_CENTER,
  zoom: MAP_ZOOM,
  maxZoom: 14,

  maxBounds: [
    [MAP_BOUNDS[0], MAP_BOUNDS[1] + 0.3],
    [MAP_BOUNDS[2], MAP_BOUNDS[3] - 0.3],
  ],
});

map.addControl(new maplibregl.NavigationControl(), 'top-right');

const formatDayLabel = (day) => {
  if (day === 0) return 'Today';
  if (day === 1) return 'Tomorrow';
  return `Day ${day}`;
};

const setStatus = (message) => {
  if (statusEl) {
    statusEl.textContent = message;
  }
};

if (sliderValue) sliderValue.textContent = formatDayLabel(state.currentDay);
if (daySlider && !daySlider.value) daySlider.value = String(state.currentDay);
daySlider?.addEventListener('input', (event) => {
  const day = Number(event.target.value);
  sliderValue.textContent = formatDayLabel(day);
  loadRaster(day);
});
overlayToggle?.addEventListener('change', () => {
  if (overlayToggle.checked) {
    loadRaster(state.currentDay);
  } else {
    removeRasterLayer();
  }
});

const sourceId = 'pm25-interpolation';
const layerId = 'pm25-interpolation-layer';

const buildRasterUrl = (day) => {
  if (INTERPOLATION_TEMPLATE.includes('{day}')) {
    return `${INTERPOLATION_BASE_URL}/${INTERPOLATION_TEMPLATE.replace('{day}', day)}`;
  }
  return INTERPOLATION_TEMPLATE;
};

const waitForStyle = () =>
  new Promise((resolve) => {
    if (map.isStyleLoaded()) resolve();
    else map.once('styledata', resolve);
  });

const removeRasterLayer = () => {
  if (map.getLayer(layerId)) map.removeLayer(layerId);
  if (map.getSource(sourceId)) map.removeSource(sourceId);
};

async function loadRaster(day) {
  state.currentDay = day;
  if (overlayToggle && !overlayToggle.checked) {
    removeRasterLayer();
    return;
  }
  setStatus(`Loading D+${day} layer…`);
  await waitForStyle();

  removeRasterLayer();

  const rasterUrl = buildRasterUrl(day);

  map.addSource(sourceId, {
    type: 'image',
    url: rasterUrl,
    coordinates: [
      [MAP_BOUNDS[0], MAP_BOUNDS[3]],
      [MAP_BOUNDS[2], MAP_BOUNDS[3]],
      [MAP_BOUNDS[2], MAP_BOUNDS[1]],
      [MAP_BOUNDS[0], MAP_BOUNDS[1]],
    ],
  });

  map.addLayer({
    id: layerId,
    type: 'raster',
    source: sourceId,
    paint: {
      'raster-opacity': 0.75,
      'raster-resampling': 'linear',
    },
  });
  setStatus(`Showing D+${day} layer`);
}

async function loadCsvMarkers() {
  if (!PREDICTIONS_CSV_PATH) {
    setStatus('CSV path missing');
    return;
  }

  try {
    const response = await fetch(PREDICTIONS_CSV_PATH);
    if (!response.ok) throw new Error(`Failed to fetch CSV (${response.status})`);
    const text = await response.text();
    const rows = parseCsv(text);
    state.csvHeaders = rows.length ? Object.keys(rows[0]) : [];

    state.csvMarkers.forEach((marker) => marker.remove());
    state.csvMarkers = [];
    Object.keys(state.sensorData).forEach((key) => delete state.sensorData[key]);
    clearFocus();

    rows.forEach((row) => {
      const sensorId = row.sensor_id || row.sensorId;
      const lat = parseFloat(row.latitude || row.lat);
      const lon = parseFloat(row.longitude || row.lon || row.lng);
      if (!sensorId || Number.isNaN(lat) || Number.isNaN(lon)) return;

      if (!state.sensorData[sensorId]) {
        state.sensorData[sensorId] = {
          sensorId,
          lat,
          lon,
          city: row.city_y || '',
          street: row.street || '',
          latestValue: null,
          rows: [],
        };
      }

      const entry = state.sensorData[sensorId];
      const predicted = parseFloat(row.predicted_pm25 ?? row.predicted ?? 'NaN');
      const actual = parseFloat(row.pm25 ?? 'NaN');
      entry.rows.push(row);

      if (Number.isFinite(predicted)) {
        entry.latestValue = predicted;
      } else if (Number.isFinite(actual)) {
        entry.latestValue = actual;
      }
    });

    state.csvMarkers = Object.values(state.sensorData).map((entry) => {
      const displayValue = entry.latestValue;
      const markerEl = document.createElement('div');
      markerEl.className = 'sensor-marker';
      markerEl.style.background = getAQIColor(displayValue ?? 0);

      markerEl.addEventListener('click', (event) => {
        event.stopPropagation();
        focusOnSensor(entry.sensorId, markerEl);
      });

      const popup = new maplibregl.Popup({ closeButton: false, offset: 12 }).setHTML(
        buildPopupHtml(entry, displayValue),
      );

      const marker = new maplibregl.Marker({ element: markerEl })
        .setLngLat([entry.lon, entry.lat])
        .setPopup(popup);

      if (sensorToggle.checked) marker.addTo(map);
      return marker;
    });

    setStatus(`Loaded ${state.csvMarkers.length} sensors`);
  } catch (error) {
    console.error('Failed to load predictions CSV', error);
    setStatus('CSV fetch failed');
  }
}

function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  if (!lines.length) return [];
  const headers = splitCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const cells = splitCsvLine(line);
    const obj = {};
    headers.forEach((key, idx) => {
      obj[key] = cells[idx] ?? '';
    });
    return obj;
  });
}

function splitCsvLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current);
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current);
  return result.map((cell) => cell.replace(/^"|"$/g, '').trim());
}

function getAQIColor(aqi) {
  if (aqi <= 50) return '#00e400';
  if (aqi <= 100) return '#ffff00';
  if (aqi <= 150) return '#ff7e00';
  if (aqi <= 200) return '#ff0000';
  return '#8f3f97';
}

const buildPopupHtml = (entry, value) => {
  const name = entry.street || entry.sensorId;
  const location = entry.city ? `${entry.city}<br/>` : '';
  const reading = Number.isFinite(value) ? `PM2.5: ${value.toFixed(2)}` : 'No recent value';
  return `<strong>${name}</strong><br/>${location}${reading}`;
};

function focusOnSensor(sensorId, markerEl) {
  const data = state.sensorData[sensorId];
  if (!data) return;

  if (state.activeMarkerEl && state.activeMarkerEl !== markerEl) {
    state.activeMarkerEl.classList.remove('is-active');
  }
  state.activeMarkerEl = markerEl;
  markerEl.classList.add('is-active');

  if (focusPanel) focusPanel.style.display = 'flex';
  if (focusNameEl) {
    const name = data.street || '';
    const location = data.city ? `${data.city}` : '';
    focusNameEl.textContent = [name, location].filter(Boolean).join(', ') || data.sensorId;
  }
  if (focusMetaEl) {
    const latLabel = Number.isFinite(data.lat) ? data.lat.toFixed(4) : '—';
    const lonLabel = Number.isFinite(data.lon) ? data.lon.toFixed(4) : '—';
    focusMetaEl.textContent = `Lat ${latLabel}, Lon ${lonLabel}, ID ${data.sensorId ?? '—'}`;
  }
  if (focusDetailsBtn) {
    focusDetailsBtn.disabled = !(data.rows && data.rows.length);
    focusDetailsBtn.dataset.sensorId = data.sensorId;
  }

  updateFocusImage('forecast-card', 'focus-forecast-thumb', `./models/${sensorId}/images/forecast.png`);
  updateFocusImage(
    'hindcast-card',
    'focus-hindcast-thumb',
    `./models/${sensorId}/images/hindcast_prediction.png`,
  );

  map.flyTo({
    center: [data.lon, data.lat],
    zoom: Math.max(map.getZoom(), 11),
    speed: 0.3,
  });
}

function clearFocus() {
  if (state.activeMarkerEl) {
    state.activeMarkerEl.classList.remove('is-active');
    state.activeMarkerEl = null;
  }
  if (focusPanel) focusPanel.style.display = 'none';
  if (focusNameEl) focusNameEl.textContent = '';
  if (focusMetaEl) focusMetaEl.textContent = '';
  if (focusDetailsBtn) {
    focusDetailsBtn.disabled = true;
    focusDetailsBtn.dataset.sensorId = '';
  }
  hideFocusImage('forecast-card', 'focus-forecast-thumb');
  hideFocusImage('hindcast-card', 'focus-hindcast-thumb');
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

function openDetailsModal(sensorId) {
  if (!detailsModal) return;
  const entry = state.sensorData[sensorId];
  if (!entry || !entry.rows.length) return;

  const titleParts = [entry.street, entry.city].filter(Boolean);
  if (detailsModalTitle) {
    detailsModalTitle.textContent = titleParts.length ? titleParts.join(', ') : entry.sensorId;
  }

  renderDetailsTable(entry);
  detailsModal.classList.remove('hidden');
  state.detailsModalActive = true;
}

function closeDetailsModal() {
  if (!detailsModal) return;
  detailsModal.classList.add('hidden');
  state.detailsModalActive = false;
}

function renderDetailsTable(entry) {
  if (!detailsTableHead || !detailsTableBody) return;
  const hiddenColumns = new Set(['longitude', 'latitude', 'sensor_id', 'city_y', 'street', 'country', 'feed_url']);
  const headers = (state.csvHeaders.length ? state.csvHeaders : Object.keys(entry.rows[0] || {})).filter(
    (header) => !hiddenColumns.has(header),
  );

  detailsTableHead.innerHTML = '';
  detailsTableBody.innerHTML = '';

  if (!headers.length) return;

  const headRow = document.createElement('tr');
  headers.forEach((header) => {
    const th = document.createElement('th');
    th.textContent = header;
    headRow.appendChild(th);
  });
  detailsTableHead.appendChild(headRow);

  entry.rows.forEach((row) => {
    const tr = document.createElement('tr');
    headers.forEach((header) => {
      const td = document.createElement('td');
      td.textContent = row[header] ?? '';
      tr.appendChild(td);
    });
    detailsTableBody.appendChild(tr);
  });
}

function openImageModal(src) {
  if (!imageModal || !imageModalImg) return;
  imageModalImg.src = src;
  imageModal.classList.remove('hidden');
  state.modalActive = true;
}

function closeImageModal() {
  if (!imageModal || !imageModalImg) return;
  imageModal.classList.add('hidden');
  imageModalImg.src = '';
  state.modalActive = false;
}

imageModalClose?.addEventListener('click', closeImageModal);
imageModalBackdrop?.addEventListener('click', closeImageModal);
detailsModalClose?.addEventListener('click', closeDetailsModal);
detailsModalBackdrop?.addEventListener('click', closeDetailsModal);
focusDetailsBtn?.addEventListener('click', () => {
  if (!focusDetailsBtn?.dataset.sensorId) return;
  openDetailsModal(focusDetailsBtn.dataset.sensorId);
});
document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  if (state.modalActive) closeImageModal();
  if (state.detailsModalActive) closeDetailsModal();
});

sensorToggle.addEventListener('change', () => {
  state.csvMarkers.forEach((marker) => {
    if (sensorToggle.checked) marker.addTo(map);
    else marker.remove();
  });
  if (!sensorToggle.checked) {
    clearFocus();
  }
});

map.on('load', async () => {
  await loadRaster(state.currentDay);
  await loadCsvMarkers();
});

map.on('click', () => {
  clearFocus();
});

