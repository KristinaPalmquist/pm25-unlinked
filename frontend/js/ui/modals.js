import { HIDDEN_COLUMNS } from '../config/mapConfig.js';
import { state, ui } from './index.js';

// Global date string for forecast/hindcast filenames
const today_short = new Date().toISOString().slice(0, 10).replace(/-/g, '');

function ensureDetailsPlotsContainer() {
  if (!ui.detailsModal) return null;
  const content = ui.detailsModal.querySelector('.details-modal-content');
  if (!content) return null;

  let plotRow = content.querySelector('.details-plot-row');
  if (!plotRow) {
    plotRow = document.createElement('div');
    plotRow.className = 'details-plot-row flex gap-3';
    plotRow.innerHTML = `
      <div id="details-forecast-card" class="focus-image-card hidden">
        <p class="text-sm text-gray-700 font-semibold">Forecast</p>
        <img
          id="details-forecast-thumb"
          class="focus-thumb hidden"
          alt="Forecast plot"
        />
      </div>
      <div id="details-hindcast-card" class="focus-image-card hidden">
        <p class="text-sm text-gray-700 font-semibold">Hindcast</p>
        <img
          id="details-hindcast-thumb"
          class="focus-thumb hidden"
          alt="Hindcast plot"
        />
      </div>
    `;

    const tableWrapper = content.querySelector('.details-table-wrapper');
    if (tableWrapper) {
      content.insertBefore(plotRow, tableWrapper);
    } else {
      content.appendChild(plotRow);
    }
  }

  return plotRow;
}

function updateDetailsImage(cardId, thumbId, url) {
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
        hideDetailsImage(cardId, thumbId);
      }
    })
    .catch(() => hideDetailsImage(cardId, thumbId));
}

function hideDetailsImage(cardId, thumbId) {
  const cardEl = document.getElementById(cardId);
  const thumbEl = document.getElementById(thumbId);
  if (!cardEl || !thumbEl) return;
  thumbEl.src = '';
  thumbEl.classList.add('hidden');
  cardEl.classList.add('hidden');
  thumbEl.onclick = null;
}

export function openImageModal(src) {
  if (!ui.imageModal || !ui.imageModalImg) return;
  ui.imageModalImg.src = src;
  ui.imageModal.classList.remove('hidden');
  state.modals.image = true;
}

export function closeImageModal() {
  if (!ui.imageModal || !ui.imageModalImg) return;
  ui.imageModal.classList.add('hidden');
  ui.imageModalImg.src = '';
  state.modals.image = false;
}

export function openDetailsModal(sensorId) {
  if (!ui.detailsModal) return;

  const entry = state.sensorData[sensorId];
  if (!entry || !entry.rows.length) return;

  // Title
  if (ui.detailsModalTitle) {
    const id = entry.sensorId;
    const street = entry.street || '';
    const city = entry.city || '';
    const lat = entry.lat;
    const lon = entry.lon;

    const capitalize = (str) =>
      !str ? '' : str.charAt(0).toUpperCase() + str.slice(1);

    ui.detailsModalTitle.innerHTML = `
      <h3 class="font-semibold text-lg">
        Sensor id: ${id}, Location: ${capitalize(street)}, ${capitalize(city)}
      </h3>
      <p class="text-sm text-gray-700">Latitude: ${lat}, Longitude: ${lon}</p>
    `;
  }

  // Forecast + Hindcast Images (conditionally shown)
  ensureDetailsPlotsContainer();

  const forecastPath = `./frontend/sensor_images/${sensorId}/${sensorId}_${today_short}_forecast.png`;
  const hindcastPath = `./frontend/sensor_images/${sensorId}/${sensorId}_${today_short}_hindcast.png`;

  // Helper: check if image exists
  function imageExists(url) {
    const xhr = new XMLHttpRequest();
    xhr.open('HEAD', url, false);
    xhr.send();
    return xhr.status >= 200 && xhr.status < 300;
  }

  const hasForecast = imageExists(forecastPath);
  const hasHindcast = imageExists(hindcastPath);

  // Update UI based on availability
  if (hasForecast) {
    updateDetailsImage(
      'details-forecast-card',
      'details-forecast-thumb',
      forecastPath,
    );
    document.getElementById('details-forecast-card').classList.remove('hidden');
  } else {
    document.getElementById('details-forecast-card').classList.add('hidden');
  }

  if (hasHindcast) {
    updateDetailsImage(
      'details-hindcast-card',
      'details-hindcast-thumb',
      hindcastPath,
    );
    document.getElementById('details-hindcast-card').classList.remove('hidden');
  } else {
    document.getElementById('details-hindcast-card').classList.add('hidden');
  }

  // If neither image exists → hide both cards entirely
  if (!hasForecast && !hasHindcast) {
    document.getElementById('details-forecast-card').classList.add('hidden');
    document.getElementById('details-hindcast-card').classList.add('hidden');
  }

  // Table
  renderDetailsTable(entry);

  // Show modal
  ui.detailsModal.classList.remove('hidden');
  state.modals.details = true;
}

// export function openDetailsModal(sensorId) {
//   if (!ui.detailsModal) return;
//   const entry = state.sensorData[sensorId];
//   if (!entry || !entry.rows.length) return;

//   if (ui.detailsModalTitle) {
//     const id = entry.sensorId;
//     const street = entry.street || '';
//     const city = entry.city || '';
//     const lat = entry.lat;
//     const lon = entry.lon;

//     function capitalize(str) {
//       if (!str) return '';
//       return str.charAt(0).toUpperCase() + str.slice(1);
//     }

//     ui.detailsModalTitle.innerHTML = `
//       <h3 class="font-semibold text-lg">Sensor id: ${id}, Location: ${capitalize(street)}, ${capitalize(city)}</h3>
//       <p class="text-sm text-gray-700">Latitude: ${lat}, Longitude ${lon}</p>
//     `;
//   }

//   /// Forecast + Hindcast Plots
//   ensureDetailsPlotsContainer();
//   updateDetailsImage(
//     'details-forecast-card',
//     'details-forecast-thumb',
//     `./frontend/sensor_images/${sensorId}/${sensorId}_${today_short}_forecast.png`,
//   );
//   updateDetailsImage(
//     'details-hindcast-card',
//     'details-hindcast-thumb',
//     `./frontend/sensor_images/${sensorId}/${sensorId}_${today_short}_hindcast.png`,
//   );

//   renderDetailsTable(entry);
//   ui.detailsModal.classList.remove('hidden');
//   state.modals.details = true;
// }

export function closeDetailsModal() {
  if (!ui.detailsModal) return;
  ui.detailsModal.classList.add('hidden');
  state.modals.details = false;
  hideDetailsImage('details-forecast-card', 'details-forecast-thumb');
  hideDetailsImage('details-hindcast-card', 'details-hindcast-thumb');
}

export function renderDetailsTable(entry) {
  if (!ui.detailsTableHead || !ui.detailsTableBody) return;
  if (!entry.rows || entry.rows.length === 0) return;
  const headers = (
    state.csvHeaders.length
      ? state.csvHeaders
      : Object.keys(entry.rows[0] || {})
  ).filter((h) => !HIDDEN_COLUMNS.has(h));
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
      td.textContent =
        !isDateColumn && Number.isFinite(numValue)
          ? numValue.toFixed(3)
          : value;
      tr.appendChild(td);
    });
    ui.detailsTableBody.appendChild(tr);
  });
}
