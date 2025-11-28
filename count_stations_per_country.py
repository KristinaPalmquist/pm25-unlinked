from collections import Counter

# Read the station names file
with open('station_names.txt', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# Extract countries from each line
countries = []
for line in lines:
    line = line.strip()
    if line.startswith('Station: ') and ', ' in line:
        # Extract country (last part after the last comma)
        country = line.split(', ')[-1]
        countries.append(country)

# Count stations per country
country_counts = Counter(countries)

# Print results sorted by count (descending)
print("Stations per country:")
print("-" * 30)
for country, count in country_counts.most_common():
    print(f"{country}: {count}")

print(f"\nTotal stations: {sum(country_counts.values())}")
print(f"Countries found: {len(country_counts)}")
