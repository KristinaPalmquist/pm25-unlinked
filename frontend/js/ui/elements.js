export const ui = {
  appHeader: document.getElementById("app-header"),
  regionName: document.getElementById("region-name"),
  dayButtons: document.querySelectorAll(".day-button"),
  sensorToggle: document.getElementById("toggle-sensors"),
  overlayToggle: document.getElementById("toggle-overlay"),
  focusPanel: document.getElementById("focus-panel"),
  focusName: document.getElementById("focus-name"),
  focusMeta: document.getElementById("focus-meta"),
  focusDetailsBtn: document.getElementById(
    "focus-details-btn",
  ),
  imageModal: document.getElementById("image-modal"),
  imageModalImg: document.getElementById("image-modal-img"),
  imageModalClose: document.getElementById(
    "image-modal-close",
  ),
  imageModalBackdrop: document.getElementById(
    "image-modal-backdrop",
  ),
  detailsModal: document.getElementById("details-modal"),
  detailsModalTitle: document.getElementById(
    "details-modal-title",
  ),
  detailsModalClose: document.getElementById(
    "details-modal-close",
  ),
  detailsModalBackdrop: document.getElementById(
    "details-modal-backdrop",
  ),
  detailsTableHead: document.getElementById(
    "details-table-head",
  ),
  detailsTableBody: document.getElementById(
    "details-table-body",
  ),
};

export function getCardElements(cardId, thumbId) {
  return {
    cardEl: document.getElementById(cardId),
    thumbEl: document.getElementById(thumbId),
  };
}

export function adjustHeaderText() {
  ui.regionName.style.transform = "scaleX(1)";
  const containerWidth = ui.appHeader.offsetWidth;
  const textWidth = ui.regionName.offsetWidth;
  const scaleFactor = containerWidth / textWidth;
  ui.regionName.style.transform = `scaleX(${scaleFactor})`;
}

const observer = new ResizeObserver(adjustHeaderText);
observer.observe(ui.appHeader);

adjustHeaderText();
