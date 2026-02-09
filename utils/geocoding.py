# from geopy.geocoders import Nominatim

# def get_city_coordinates(city_name: str):
#     """
#     Takes city name and returns its latitude and longitude (rounded to 2 digits after dot).
#     """
#     # Initialize Nominatim API (for getting lat and long of the city)
#     geolocator = Nominatim(user_agent="MyApp")
#     city = geolocator.geocode(city_name)

#     latitude = round(city.latitude, 2)
#     longitude = round(city.longitude, 2)

#     return latitude, longitude