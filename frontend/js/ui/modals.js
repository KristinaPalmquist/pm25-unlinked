import { HIDDEN_COLUMNS } from '../config/mapConfig.js';
import { state, ui } from './index.js';

// Global date string for forecast/hindcast filenames
const today_short = new Date().toISOString().slice(0, 10);

function ensureDetailsPlotsContainer() {
  if (!ui.detailsModal) return null;
  const content = ui.detailsModal.querySelector('.details-modal-content');
  if (!content) return null;

  let plotRow = content.querySelector('.details-plot-row');
  if (!plotRow) {
    plotRow = document.createElement('div');
    plotRow.className = 'details-plot-row flex gap-3';
    plotRow.innerHTML = `
      <div id="details-forecast-card" class="focus-image-card hidden flex-1 border-2 border-black bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] p-2">
      <p class="text-xs uppercase tracking-widest text-black font-bold mb-2 border-b-2 border-black pb-1">Forecast</p>
      <div class="overflow-hidden bg-gray-100 border border-gray-200">
        <img
          id="details-forecast-thumb"
          class="focus-thumb hidden w-full h-auto cursor-pointer hover:scale-[1.02] transition-transform"
          alt="Forecast plot"
        />
      </div>
    </div>
    <div id="details-hindcast-card" class="focus-image-card hidden flex-1 border-2 border-black bg-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] p-2">
      <p class="text-xs uppercase tracking-widest text-black font-bold mb-2 border-b-2 border-black pb-1">Hindcast</p>
      <div class="overflow-hidden bg-gray-100 border border-gray-200">
        <img
          id="details-hindcast-thumb"
          class="focus-thumb hidden w-full h-auto cursor-pointer hover:scale-[1.02] transition-transform"
          alt="Hindcast plot"
        />
      </div>
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
  if (!cardEl || !thumbEl) {
    return;
  }

  thumbEl.src = url;
  thumbEl.classList.remove('hidden');
  cardEl.classList.remove('hidden');
  thumbEl.onClick = () => openImageModal(url);
}

function hideDetailsImage(cardId, thumbId) {
  const cardEl = document.getElementById(cardId);
  const thumbEl = document.getElementById(thumbId);
  if (!cardEl || !thumbEl) return;
  thumbEl.src = '';
  thumbEl.classList.add('hidden');
  cardEl.classList.add('hidden');
  thumbEl.onClick = null;
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

export async function openDetailsModal(sensorId) {
  if (!ui.detailsModal) {
    return;
  }

  const entry = state.sensorData[sensorId];
  if (!entry || !entry.rows.length) {
    return;
  }

  renderDetailsTitle(entry);

  const forecastPath = `./sensor_images/${sensorId}/${sensorId}_${today_short}_forecast.png`;
  const hindcastPath = `./sensor_images/${sensorId}/${sensorId}_${today_short}_hindcast.png`;

  // Helper: check if image exists
  async function imageExists(url) {
    try {
      const res = await fetch(url, { method: 'HEAD' });
      return res.ok;
    } catch {
      return false;
    }
  }

  const [hasForecast, hasHindcast] = await Promise.all([
    imageExists(forecastPath),
    imageExists(hindcastPath),
  ]);

  const plotRow = ensureDetailsPlotsContainer();
  const tableWrapper = ui.detailsModal.querySelector('.details-table-wrapper');

  if (hasForecast || hasHindcast) {
    // show images, hide table
    plotRow.classList.remove('hidden');
    if (tableWrapper) {
      tableWrapper.classList.add('hidden');
    }

    if (hasForecast) {
      updateDetailsImage(
        'details-forecast-card',
        'details-forecast-thumb',
        forecastPath,
      );
    } else {
      hideDetailsImage('details-forecast-card', 'details-forecast-thumb');
    }

    if (hasHindcast) {
      updateDetailsImage(
        'details-hindcast-card',
        'details-hindcast-thumb',
        hindcastPath,
      );
    } else {
      hideDetailsImage('details-hindcast-card', 'details-hindcast-thumb');
    }
  } else {
    // hide images, show table
    plotRow.classList.add('hidden');
    if (tableWrapper) {
      tableWrapper.classList.remove('hidden');
    }
    renderDetailsTable(entry);
  }

  // show modal
  ui.detailsModal.classList.remove('hidden');
  state.modals.details = true;
}

export function closeDetailsModal() {
  if (!ui.detailsModal) return;
  ui.detailsModal.classList.add('hidden');
  state.modals.details = false;
  hideDetailsImage('details-forecast-card', 'details-forecast-thumb');
  hideDetailsImage('details-hindcast-card', 'details-hindcast-thumb');
}

export function renderDetailsTitle(entry) {
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
}

export function renderDetailsTable(entry) {
  if (!ui.detailsTableHead || !ui.detailsTableBody) return;
  if (!entry.rows || entry.rows.length === 0) return;

  const headerMap = {
    date: 'Date',
    predicted_pm25: 'Pred',
    pm25: 'Actual',
    days_before_forecast_day: 'Days Out',
    predicted_pm25_rolling_3d: 'Roll 3d',
    predicted_pm25_lag_1d: 'Lag 1',
    predicted_pm25_lag_2d: 'Lag 2',
    predicted_pm25_lag_3d: 'Lag 3',
    predicted_pm25_nearby_avg: 'Nb Avg',
    city: 'City',
  };

  const headers = (
    state.csvHeaders.length
      ? state.csvHeaders
      : Object.keys(entry.rows[0] || {})
  ).filter((h) => !HIDDEN_COLUMNS.has(h));

  if (!headers.length) return;

  ui.detailsTableHead.innerHTML = '';
  ui.detailsTableBody.innerHTML = '';

  const headRow = document.createElement('tr');
  headRow.className =
    'bg-black text-white uppercase text-[10px] tracking-wider';

  headers.forEach((h) => {
    const th = document.createElement('th');
    const cleanHeader = h
      .replace(/_/g, ' ')
      .replace(/concentration/i, '')
      .trim();
    th.textContent =
      headerMap[h.toLowerCase()] || h.replace(/_/g, ' ').substring(0, 10);
    th.className =
      'px-2 py-2 border-r border-white last:border-r-0 text-left';
    headRow.appendChild(th);
  });
  ui.detailsTableHead.appendChild(headRow);

  entry.rows.forEach((row, idx) => {
    const tr = document.createElement('tr');
    tr.className = idx % 2 === 0 ? 'bg-white' : 'bg-gray-50';

    headers.forEach((h) => {
      const td = document.createElement('td');
      const value = row[h] ?? '';
      const isDate =
        h.toLowerCase().includes('date') || h.toLowerCase().includes('time');
      const numValue = parseFloat(value);

      if (!isDate && Number.isFinite(numValue)) {
        td.textContent = numValue.toFixed(2);
        td.className = 'px-3 py-1 border-r border-black font-mono text-right';
      } else {
        td.textContent = value;
        td.className =
          'px-3 py-1 border-r border-black text-left whitespace-nowrap overflow-hidden text-ellipsis max-w-[120px]';
      }

      td.classList.add('last:border-r-0');
      tr.appendChild(td);
    });
    ui.detailsTableBody.appendChild(tr);
  });

  const tableContainer = ui.detailsTableBody.closest('table');
  if (tableContainer) {
    tableContainer.className =
      'w-full border-collapse border-2 border-black text-xs mb-4';
  }

  // if (!ui.detailsTableHead || !ui.detailsTableBody) return;
  // if (!entry.rows || entry.rows.length === 0) return;
  // const headers = (
  //   state.csvHeaders.length
  //     ? state.csvHeaders
  //     : Object.keys(entry.rows[0] || {})
  // ).filter((h) => !HIDDEN_COLUMNS.has(h));
  // if (!headers.length) return;

  // ui.detailsTableHead.innerHTML = '';
  // ui.detailsTableBody.innerHTML = '';

  // const headRow = document.createElement('tr');
  // headers.forEach((h) => {
  //   const th = document.createElement('th');
  //   th.textContent = h;
  //   headRow.appendChild(th);
  // });
  // ui.detailsTableHead.appendChild(headRow);

  // entry.rows.forEach((row) => {
  //   const tr = document.createElement('tr');
  //   headers.forEach((h) => {
  //     const td = document.createElement('td');
  //     const value = row[h] ?? '';
  //     const isDateColumn = h.toLowerCase() === 'date';
  //     const numValue = parseFloat(value);
  //     td.textContent =
  //       !isDateColumn && Number.isFinite(numValue)
  //         ? numValue.toFixed(3)
  //         : value;
  //     tr.appendChild(td);
  //   });
  //   ui.detailsTableBody.appendChild(tr);
  // });
}
