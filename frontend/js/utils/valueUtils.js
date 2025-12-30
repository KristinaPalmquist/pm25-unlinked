export function getValueForDay(data, day, dayDates) {
  if (!data.rows?.length) return null;
  
  const row = day === 0
    ? data.rows.find((r) => r.date === dayDates[0])
    : data.rows.find((r) => Number(r.days_before_forecast_day ?? r.daysBeforeForecastDay ?? 'NaN') === day);
  
  if (!row) return null;
  
  const value = day === 0
    ? parseFloat(row.pm25 ?? 'NaN')
    : parseFloat(row.predicted_pm25 ?? row.predicted ?? 'NaN');
  
  return Number.isFinite(value) ? value : null;
}