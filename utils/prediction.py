import pandas as pd
from datetime import datetime, timedelta


def get_historical_data_for_date(date: str, feature_view, weather_fg, model) -> pd.DataFrame:
    """
    Retrieve data for a specific date from a feature view.

    Args:
        date (str): The date in the format "%Y-%m-%d".
        feature_view: The feature view object.
        model: The machine learning model used for prediction.

    Returns:
        pd.DataFrame: A DataFrame containing data for the specified date.
    """
    date_dt = pd.to_datetime(date).date()
    
    features_df, labels_df = feature_view.training_data(
        start_time=date_dt,
        end_time=date_dt + timedelta(days=1),
        statistics_config=False
    )
    
    result = pd.DataFrame({
        'date': pd.to_datetime(features_df['date']).dt.strftime('%Y-%m-%d'),
        'pm25': labels_df['pm25']
    })
    
    return result.sort_values('date').reset_index(drop=True)


def get_historical_data_in_date_range(date_start: str, date_end: str, feature_view, weather_fg, model) -> pd.DataFrame:
    """
    Retrieve data for a specific date range from a feature view.

    Args:
        date_start (str): The start date in the format "%Y-%m-%d".
        date_end (str): The end date in the format "%Y-%m-%d".
        feature_view: The feature view object.
        model: The machine learning model used for prediction.

    Returns:
        pd.DataFrame: A DataFrame containing data for the specified date range.
    """
    batch_data = feature_view.query.read()
    
    # Normalize dates for comparison
    batch_data['date'] = pd.to_datetime(batch_data['date']).dt.tz_localize(None)
    date_start_dt = pd.to_datetime(date_start)
    date_end_dt = pd.to_datetime(date_end)
    
    # Filter date range
    mask = (batch_data['date'] >= date_start_dt) & (batch_data['date'] <= date_end_dt)
    filtered_data = batch_data[mask].copy()
    
    # Format dates as strings
    filtered_data['date'] = filtered_data['date'].dt.strftime('%Y-%m-%d')
    
    return filtered_data[['date', 'pm25']].sort_values('date').reset_index(drop=True)


def get_future_data_for_date(date: str, feature_view, weather_fg, model) -> pd.DataFrame:
    """
    Predicts future PM2.5 data for a specified date.

    Args:
        date (str): The date in the format "%Y-%m-%d".
        feature_view: The feature view object.
        weather_fg: Weather feature group.
        model: The machine learning model used for prediction.

    Returns:
        pd.DataFrame: A DataFrame containing predictions for the specified date.
    """
    date_dt = pd.to_datetime(date)
    fg_data = weather_fg.read()
    
    # Normalize dates
    fg_data['date'] = pd.to_datetime(fg_data['date']).dt.tz_localize(None)
    
    # Filter for specific date
    df = fg_data[fg_data['date'] == date_dt].copy()
    
    if df.empty:
        return pd.DataFrame(columns=['date', 'pm25'])
    
    # Prepare features and predict
    features = df.drop(['date', 'city'], axis=1)
    df['pm25'] = model.predict(features)
    
    return df[['date', 'pm25']].sort_values('date').reset_index(drop=True)


def get_future_data_in_date_range(date_start: str, date_end: str, feature_view, weather_fg, model) -> pd.DataFrame:
    """
    Predicts future PM2.5 data for a specified date range.

    Args:
        date_start (str): The start date in the format "%Y-%m-%d".
        date_end (str): The end date in the format "%Y-%m-%d" (optional, defaults to date_start).
        feature_view: The feature view object.
        weather_fg: Weather feature group.
        model: The machine learning model used for prediction.

    Returns:
        pd.DataFrame: A DataFrame containing predictions for the specified date range.
    """
    # Handle default end date
    if date_end is None:
        date_end = date_start
    
    # Parse dates
    date_start_dt = pd.to_datetime(date_start)
    date_end_dt = pd.to_datetime(date_end)
    
    # Read and normalize weather data
    fg_data = weather_fg.read()
    fg_data['date'] = pd.to_datetime(fg_data['date']).dt.tz_localize(None)
    
    # Filter date range
    mask = (fg_data['date'] >= date_start_dt) & (fg_data['date'] <= date_end_dt)
    df = fg_data[mask].copy()
    
    if df.empty:
        return pd.DataFrame(columns=['date', 'pm25'])
    
    # Prepare features and predict
    features = df.drop(['date', 'city'], axis=1)
    df['pm25'] = model.predict(features)
    
    return df[['date', 'pm25']].sort_values('date').reset_index(drop=True)