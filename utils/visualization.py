import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator
import numpy as np
import matplotlib.colors as mcolors
from scipy.spatial.distance import cdist
from datetime import datetime


def plot_air_quality_forecast(city: str, street: str, df: pd.DataFrame, file_path: str, hindcast=False):
    plt.close('all')
    fig, ax = plt.subplots(figsize=(10, 6))

    day = pd.to_datetime(df['date']).dt.date
    # Plot each column separately in matplotlib
    ax.plot(day, df['predicted_pm25'], label='Predicted PM2.5', color='red', linewidth=2, marker='o', markersize=5, markerfacecolor='blue')

    # Set the y-axis to a logarithmic scale
    ax.set_yscale('log')
    ax.set_yticks([0, 10, 25, 50, 100, 250, 500])
    ax.get_yaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_ylim(bottom=1)

    # Set the labels and title
    ax.set_xlabel('Date')
    ax.set_title(f"PM2.5 Predicted (Logarithmic Scale) for {city}, {street}")
    ax.set_ylabel('PM2.5')

    colors = ['green', 'yellow', 'orange', 'red', 'purple', 'darkred']
    labels = ['Good', 'Moderate', 'Unhealthy for Some', 'Unhealthy', 'Very Unhealthy', 'Hazardous']
    ranges = [(0, 49), (50, 99), (100, 149), (150, 199), (200, 299), (300, 500)]
    for color, (start, end) in zip(colors, ranges):
        ax.axhspan(start, end, color=color, alpha=0.3)

    # Add a legend for the different Air Quality Categories
    patches = [Patch(color=colors[i], label=f"{labels[i]}: {ranges[i][0]}-{ranges[i][1]}") for i in range(len(colors))]
    legend1 = ax.legend(handles=patches, loc='upper right', title="Air Quality Categories", fontsize='x-small')

    # Aim for ~10 annotated values on x-axis, will work for both forecasts ans hindcasts
    if len(df.index) > 11:
        every_x_tick = len(df.index) / 10
        ax.xaxis.set_major_locator(MultipleLocator(every_x_tick))

    plt.xticks(rotation=45)

    if hindcast == True:
        ax.plot(day, df['pm25'], label='Actual PM2.5', color='black', linewidth=2, marker='^', markersize=5, markerfacecolor='grey')
        legend2 = ax.legend(loc='upper left', fontsize='x-small')
        ax.add_artist(legend1)

    # Ensure everything is laid out neatly
    plt.tight_layout()

    # # Save the figure, overwriting any existing file with the same name
    plt.savefig(file_path)
    return fig


def idw_interpolation(points, values, grid_points, lon_mesh, power=2):
    # Compute distances between grid points and known data points 
    distances = cdist(grid_points, points)
    # Replace 0 with a small value to avoid division by zero
    distances = np.where(distances == 0, 1e-10, distances)
    # Compute weights based on inverse distance
    weights = 1.0 / (distances ** power)
    # Sum of weights for normalization
    weights_sum = np.sum(weights, axis=1)
    # Compute interpolated values - weighted average of known values for each grid point
    interpolated = np.sum(weights * values, axis=1) / weights_sum
    # Reshape to match grid shape
    return interpolated.reshape(lon_mesh.shape)


def plot_pm25_idw_heatmap(
    predictions: pd.DataFrame,
    sensor_locations: dict,
    forecast_date: datetime,
    path: str,
    grid_bounds: tuple,
    today: datetime.date,
    grid_resolution=800,
    power=2,
):
    df_day = predictions[predictions["date"] == forecast_date].copy()

    # Determine which column to use
    is_today = forecast_date.date() == today
    pm25_column = "pm25" if is_today else "predicted_pm25"

    if pm25_column not in df_day.columns:
        raise ValueError(f"Required column '{pm25_column}' not found for {forecast_date}")

    # Collect sensor coordinates + PM2.5 values
    sensor_coords_list = []
    pm25_values_list = []

    for sid in df_day["sensor_id"].unique():
        if sid not in sensor_locations:
            continue

        row = df_day[df_day["sensor_id"] == sid].iloc[0]
        val = row.get(pm25_column)

        if pd.isna(val):
            continue

        try:
            val = float(val)
        except:
            continue

        sensor_coords_list.append([
            sensor_locations[sid]["longitude"],
            sensor_locations[sid]["latitude"]
        ])
        pm25_values_list.append(val)

    sensor_coords = np.array(sensor_coords_list, dtype=np.float64)
    pm25_values = np.array(pm25_values_list, dtype=np.float64)

    if len(sensor_coords) == 0:
        raise ValueError(f"No valid sensor data for {forecast_date}")

    # Build grid
    min_lon, min_lat, max_lon, max_lat = grid_bounds
    lon_grid = np.linspace(min_lon, max_lon, grid_resolution)
    lat_grid = np.linspace(min_lat, max_lat, grid_resolution)
    lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
    grid_points = np.column_stack([lon_mesh.ravel(), lat_mesh.ravel()])

    # IDW interpolation
    idw_result = idw_interpolation(sensor_coords, pm25_values, grid_points, lon_mesh, power=power)

    vmin = max(0, np.nanmin(idw_result))
    vmax = np.nanmax(idw_result)

    # Expand vmax slightly so extreme values stand out
    vmax = max(vmax, 500)

    # Build AQI colormap (full range)
    category_colors = [
        "#00e400", "#7de400", "#ffff00", "#ffb000",
        "#ff7e00", "#ff4000", "#ff0000", "#c0007f",
        "#8f3f97", "#7e0023"
    ]
    aqi_cmap = mcolors.LinearSegmentedColormap.from_list("aqi", category_colors, N=512)

    # Render
    plt.close("all")
    fig, ax = plt.subplots(figsize=(10, 10))

    im = ax.imshow(
        idw_result,
        extent=(min_lon, max_lon, min_lat, max_lat),
        origin="lower",
        cmap=aqi_cmap,
        vmin=vmin,
        vmax=vmax,
        alpha=0.65,         
        interpolation="bilinear",
    )

    ax.set_xlim(min_lon, max_lon)
    ax.set_ylim(min_lat, max_lat)
    ax.axis("off")

    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0, transparent=True)
    plt.close(fig)
