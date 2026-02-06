import { HIDDEN_COLUMNS } from '../config/mapConfig.js';
import { state, ui } from './index.js';

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

  if (ui.detailsModalTitle) {
    const parts = [
      entry.sensorId,
      entry.street,
      entry.city,
      entry.lat,
      entry.lon,
    ].filter(Boolean);
    ui.detailsModalTitle.textContent = parts.length
      ? parts.join(', ')
      : entry.sensorId;
  }

  renderDetailsTable(entry);
  ui.detailsModal.classList.remove('hidden');
  state.modals.details = true;
}

export function closeDetailsModal() {
  if (!ui.detailsModal) return;
  ui.detailsModal.classList.add('hidden');
  state.modals.details = false;
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
