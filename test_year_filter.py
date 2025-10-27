#!/usr/bin/env python3
"""
Quick test to verify year filtering works correctly
"""

import pandas as pd

# Load data
df = pd.read_csv('storms.csv')
print(f"📊 Total records in dataset: {len(df)}")
print(f"📅 Year range: {df['year'].min()} - {df['year'].max()}")
print()

# Simulate what the dashboard sends
filter_options = {
    'year_start': int("2015"),  # Simulating StringVar.get()
    'year_end': int("2020"),
    'categories': ['Tropical Storm', 'Category 3', 'Category 4', 'Category 5'],
    'min_wind': 35,
    'max_wind': 200
}

print("🎛️ Simulated filter options:")
print(f"  Year: {filter_options['year_start']} - {filter_options['year_end']}")
print(f"  Categories: {filter_options['categories']}")
print(f"  Wind: {filter_options['min_wind']}-{filter_options['max_wind']} mph")
print()

# Apply year filter
filtered_data = df.copy()
year_start = filter_options.get('year_start')
year_end = filter_options.get('year_end')

print(f"🔍 Applying year filter: {year_start} - {year_end}")
if year_start is not None and year_end is not None:
    filtered_data = filtered_data[
        (filtered_data['year'] >= year_start) &
        (filtered_data['year'] <= year_end)
    ]
    print(f"✅ After year filter: {len(filtered_data)} records")
    print(f"   Years in filtered data: {sorted(filtered_data['year'].unique())}")
else:
    print("⚠️ Year filter not applied (year_start or year_end is None)")
print()

# Apply category filter
if 'categories' in filter_options and filter_options['categories']:
    print(f"🔍 Applying category filter: {filter_options['categories']}")
    category_mask = pd.Series(False, index=filtered_data.index)
    
    for cat in filter_options['categories']:
        if cat == 'Tropical Storm':
            category_mask |= (filtered_data['status'] == 'tropical storm')
        elif cat.startswith('Category '):
            cat_num = int(cat.split()[-1])
            category_mask |= (filtered_data['category'] == cat_num)
    
    filtered_data = filtered_data[category_mask]
    print(f"✅ After category filter: {len(filtered_data)} records")
print()

# Apply wind filter
if 'min_wind' in filter_options:
    filtered_data = filtered_data[filtered_data['wind'] >= filter_options['min_wind']]
    print(f"✅ After min wind filter (>= {filter_options['min_wind']}): {len(filtered_data)} records")

if 'max_wind' in filter_options:
    filtered_data = filtered_data[filtered_data['wind'] <= filter_options['max_wind']]
    print(f"✅ After max wind filter (<= {filter_options['max_wind']}): {len(filtered_data)} records")

print()
print(f"🎯 Final result: {len(filtered_data)} records match all filters")

# Show sample of filtered data
if len(filtered_data) > 0:
    print("\n📋 Sample of filtered storms:")
    sample = filtered_data.groupby(['name', 'year']).first().reset_index()
    print(sample[['name', 'year', 'status', 'category', 'wind']].head(10))
else:
    print("\n⚠️ No storms match the filter criteria")
