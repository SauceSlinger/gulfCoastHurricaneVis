#creating a python data visualization of hurricanes in the gulf of mexico
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium

hurricane_data = pd.read_csv("storms.csv")

map = folium.Map(location=[25.0,-90.0], zoom_start=5)

for index, row in hurricane_data.iterrows():
    folium.Marker([row['latitude'],row['longitude']],icon=folium.Icon(color='red')).add_to(map)

map.save("hurricane_map.html")

plt.savefig("hurricane_map.png")
plt.savefig("hurricane_plot.png")