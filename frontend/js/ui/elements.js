export const ui = {
  appHeader: document.getElementById("app-header"),
  regionName: document.getElementById("region-name"),
  headerContainer: document.getElementById(
    "header-container",
  ),
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
  const container = ui.headerContainer;
  const header = ui.appHeader;
  if (!container || !header) return;

  // Reset to a known size before measuring
  header.style.fontSize = "100px";
  const containerWidth = container.offsetWidth;
  const padding = 48; // 24px each side
  const textWidth = header.scrollWidth;

  if (textWidth > 0) {
    const newSize = 100 * (containerWidth - padding) / textWidth;
    header.style.fontSize = `${newSize}px`;
  }
}

const observer = new ResizeObserver(() => {
  adjustHeaderText();
});

if (ui.headerContainer) {
  observer.observe(ui.headerContainer);
}

adjustHeaderText();

// Move toggle controls: bottom-left on lg+, back to bottom-right on small
function repositionToggles(isLg) {
  const toggleSection = document.getElementById("toggle-controls");
  const leftContainer = document.getElementById("bottom-left");
  const rightContainer = document.getElementById("bottom-right");
  if (!toggleSection || !leftContainer || !rightContainer) return;

  if (isLg) {
    leftContainer.appendChild(toggleSection);
  } else {
    rightContainer.insertBefore(toggleSection, rightContainer.firstChild);
  }
}

const lgQuery = window.matchMedia("(min-width: 1024px)");
lgQuery.addEventListener("change", (e) => repositionToggles(e.matches));
repositionToggles(lgQuery.matches);
