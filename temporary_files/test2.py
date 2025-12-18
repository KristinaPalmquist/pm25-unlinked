import pandas as pd
from dotenv import load_dotenv
import os
import time

load_dotenv()
api_key = os.getenv('AQICN_API_KEY')
if not api_key:
    print("API key not found in .env file")
    exit()

url1 = 'https://api.waqi.info'

# Original bounding box covering Scandinavia
# lat_min, lon_min, lat_max, lon_max = 54.891, 10.849, 69.058, 24.174


lat_min, lon_min, lat_max, lon_max = 50.862218,-7.602536,69.923179,36.738284

# Split into 10x5 = 50 boxes
rows, cols = 10, 5
lat_step = (lat_max - lat_min) / rows
lon_step = (lon_max - lon_min) / cols

all_sweden_stations = []

# Query each of the 50 boxes
for row in range(rows):
    for col in range(cols):
        # Calculate this box's boundaries
        box_lat_min = lat_min + (row * lat_step)
        box_lat_max = lat_min + ((row + 1) * lat_step)
        box_lon_min = lon_min + (col * lon_step)
        box_lon_max = lon_min + ((col + 1) * lon_step)
        
        # Create the box string for API
        box = f"{box_lat_min},{box_lon_min},{box_lat_max},{box_lon_max}"
        
        # Query this box
        url = f"{url1}/map/bounds/?latlng={box}&token={api_key}"
        
        try:
            response = pd.read_json(url)

            if 'data' in response.columns:
                for station in response['data']:
                    station_name = station.get('station', {}).get('name', '')
                    if 'Sweden' in station_name:
                        all_sweden_stations.append(station)
        except:
            pass
        
        time.sleep(0.5)  # Rate limiting

print(f"Found {len(all_sweden_stations)} Sweden stations")
print(all_sweden_stations[0:3])  # Print first 3 stations for verification

stations_data = []
for station in all_sweden_stations:
    # print(f"{station['station']['name']} - AQI: {station.get('aqi', 'N/A')}")
    station_id = station.get('uid')
    station_data = [{
        'station_id': station_id,
        'station_name': station.get('station', {}).get('name', ''),
        'lat': station.get('lat'),
        'lon': station.get('lon'),
        'uid': station.get('uid'),
        'aqi': station.get('aqi'),
        'time': station.get('station', {}).get('time', '')
    }]
    
    # Create DataFrame for this station
    df_station = pd.DataFrame(station_data)
    
    # Save as CSV with station ID as filename
    filename = f'data_sweden/{station_id}.csv'
    df_station.to_csv(filename, index=False)

print(f"Created {len(all_sweden_stations)} CSV files in data_sweden/ folder")
