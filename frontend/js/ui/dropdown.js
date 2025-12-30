import { state, ui } from "./index.js";

export function populateDropdown(config, formatDayLabel) {
  if (!ui.dayDropdown) return;
  ui.dayDropdown.innerHTML = "";
  config.forecastDays.forEach((day) => {
    if (day === 0 || state.dayDates[day]) {
      const option = document.createElement("option");
      option.value = String(day);
      option.textContent = formatDayLabel(day);
      ui.dayDropdown.appendChild(option);
    }
  });
}
