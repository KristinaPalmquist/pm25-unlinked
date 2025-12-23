import pandas as pd 
import folium 
import requests
from dotenv import load_dotenv
import os
import json

# Load environment variables from .env file
load_dotenv()

# Get your API key from .env
api_key = os.getenv('AQICN_API_KEY')

if not api_key:
    print("API key not found in .env file")
    exit()

# GET data from AQI website through the API
base_url = "https://api.waqi.info"

# (lat, long)-> bottom left, (lat, lon)-> top right
latlngbox = "59.20,17.80,59.45,18.30"  # For Stockholm 

trail_url = f"/map/bounds/?token={api_key}&latlng={latlngbox}"

try:
    my_data = pd.read_json(base_url + trail_url)
    print('columns->', my_data.columns)
    print(my_data['data'])

    # Build a dataframe from the json file 
    all_rows = []
    for each_row in my_data['data']:
        all_rows.append([each_row['station']['name'],
        each_row['lat'],
        each_row['lon'],
        each_row['aqi']])
    
    df = pd.DataFrame(all_rows, columns=['station_name', 'lat', 'lon', 'aqi'])

    # Clean the DataFrame
    df['aqi'] = pd.to_numeric(df.aqi, errors='coerce')
    df1 = df.dropna(subset=['aqi'])
    
    # print("Data fetched successfully:")
    # print(df1)
    
except Exception as e:
    print(f"Error: {e}")