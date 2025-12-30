export function formatDateLabel(dateStr) {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  return Number.isNaN(date.getTime()) ? null : date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
}

export function formatDayLabel(day, dayDates) {
  const formatted = formatDateLabel(dayDates?.[day]);
  if (formatted) return day === 0 ? `Observed ${formatted}` : `Forecast ${formatted}`;
  return `Day ${day}`;
}

export function deriveDayDates(rows) {
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
    const offset = Number(
        row.days_before_forecast_day ??
        row.daysBeforeForecastDay ??
        NaN
    );

    if (!row.date) return;
    if (Number.isFinite(offset) && offset >= 1 && !dayDates[offset]) {
      const d = new Date(baseDate);
      d.setDate(baseDate.getDate() + offset);
      dayDates[offset] = d.toISOString().split('T')[0];
    }
});
  return dayDates;
}