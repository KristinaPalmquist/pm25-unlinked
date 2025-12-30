// Grid bounds
// Map settings
// Color scales
// Layer configuration

export function buildMapConfig (gridBounds, interpolationBase) {
    const config = {
      forecastDays: [0, 1, 2, 3, 4, 5, 6],
      interpolationBase: interpolationBase,
      interpolationTemplate: 'forecast_interpolation_{day}d.png',
      predictionsCsv: './models/predictions.csv',
      mapBounds: [
        gridBounds.MIN_LONGITUDE,
        gridBounds.MIN_LATITUDE,
        gridBounds.MAX_LONGITUDE,
        gridBounds.MAX_LATITUDE
      ],
      mapCenter: [gridBounds.CENTER_LONGITUDE, gridBounds.CENTER_LATITUDE],
      mapZoom: 3,
    }
    return config
};

// configuration constants
const AQI_COLORS = ['#00e400', '#ffff00', '#ff7e00', '#ff0000'];
const AQI_THRESHOLDS = [50, 100, 150];

// data processing constants
export const HIDDEN_COLUMNS = new Set(['longitude', 'latitude', 'sensor_id', 'city_y', 'city_x', 'street', 'country', 'feed_url']);


export function getAQIColor(aqi) {
  for (let i = 0; i < AQI_THRESHOLDS.length; i += 1) {
    if (aqi < AQI_THRESHOLDS[i]) return AQI_COLORS[i];
  }
  return AQI_COLORS[AQI_COLORS.length - 1];
}