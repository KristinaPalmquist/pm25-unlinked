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
    const newSize =
      (100 * (containerWidth - padding)) / textWidth;
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

// Layout states:
// < 1100px  : days vertical in bottom-left | toggles vertical above legend in bottom-right
// 1100-1399px: toggles horizontal (top) + days horizontal (bottom) in bottom-left | legend in bottom-right
// >= 1400px : toggles in bottom-left | days horizontal in bottom-center | legend in bottom-right
function updateLayout() {
  const toggleSection = document.getElementById(
    "toggle-controls",
  );
  const daySection =
    document.getElementById("day-selector");
  const leftContainer =
    document.getElementById("bottom-left");
  const centerContainer =
    document.getElementById("bottom-center");
  const rightContainer =
    document.getElementById("bottom-right");
  if (
    !toggleSection ||
    !daySection ||
    !leftContainer ||
    !centerContainer ||
    !rightContainer
  )
    return;

  if (xlQuery.matches) {
    // >= 1400px: toggles left, days center
    leftContainer.appendChild(toggleSection);
    centerContainer.appendChild(daySection);
  } else if (mdQuery.matches) {
    // 900-1279px: toggles above days, both left-aligned
    leftContainer.appendChild(toggleSection);
    leftContainer.appendChild(daySection);
  } else {
    // < 1100px: days in left, toggles above legend in right
    leftContainer.appendChild(daySection);
    rightContainer.insertBefore(
      toggleSection,
      rightContainer.firstChild,
    );
  }
}

const mdQuery = window.matchMedia("(min-width: 1100px)");
const xlQuery = window.matchMedia("(min-width: 1400px)");
mdQuery.addEventListener("change", updateLayout);
xlQuery.addEventListener("change", updateLayout);
updateLayout();
