# Project: GreenCharge Optimizer - Solar Battery Scheduling App
# Description: A software tool to optimize when to charge/discharge a home battery based on solar generation and energy prices

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from datetime import datetime, timedelta
import requests  # Added back for real API access

# Streamlit layout
st.subheader("🔄 Optimized Schedule")
st.dataframe(data[['Hour', 'SolarGeneration_kWh', 'GridPrice_per_kWh', 'BatteryCharge', 'BatteryDischarge']])

csv = data.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download CSV", data=csv, file_name='optimized_schedule.csv', mime='text/csv')

st.set_page_config(page_title="GreenCharge Optimizer", layout="wide")
st.title("🔋 GreenCharge Optimizer Dashboard")
# Sidebar parameters
st.sidebar.header("Battery Parameters")
battery_capacity = st.sidebar.slider("Battery Capacity (kWh)", 5.0, 20.0, 10.0)
max_charge_rate = st.sidebar.slider("Max Charge Rate (kWh/hour)", 0.5, 5.0, 2.0)
charge_efficiency = st.sidebar.slider("Charge Efficiency", 0.8, 1.0, 0.95)
price_threshold = st.sidebar.slider("Grid Price Threshold ($/kWh)", 0.10, 0.40, 0.22)

# Parameters for OpenWeatherMap API
api_key = "40838c75ffe84ed438563e6a228c7ddc"  # Replace with your actual API key
lat, lon = 28.6, 77.2  # Example location: New Delhi
url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"

# Fetch solar-related data from API
response = requests.get(url)
forecast = response.json()

# Parse 24-hour forecast data
hours = []
solar_kwh = []
for item in forecast['list'][:24]:
    hour = item['dt_txt']
    clouds = item['clouds']['all']  # 0–100% cloudiness
    solar_estimate = max(0, (100 - clouds) / 100 * 5)  # Simplistic solar generation estimate
    hours.append(hour)
    solar_kwh.append(solar_estimate)

# Simulate grid prices
grid_prices = np.linspace(0.15, 0.40, 24)[::-1]  # cheaper during day, expensive at night

# Create DataFrame with real-time solar and simulated price data
data = pd.DataFrame({
    'Hour': pd.to_datetime(hours),
    'SolarGeneration_kWh': solar_kwh,
    'GridPrice_per_kWh': grid_prices
})

# Simulated battery parameters
battery_capacity = 10.0  # in kWh
battery_charge = 0.0
charge_efficiency = 0.95
max_charge_rate = 2.0  # kWh per hour

# Optimization: Charge battery when solar is available or grid is cheap
def optimize_battery(data):
    data['BatteryCharge'] = 0.0
    battery_state = 0.0

    for i in range(len(data)):
        solar = data.loc[i, 'SolarGeneration_kWh']
        price = data.loc[i, 'GridPrice_per_kWh']

        if solar > 1.0:
            charge = min(max_charge_rate, battery_capacity - battery_state, solar)
            battery_state += charge * charge_efficiency
        elif price < 0.22 and battery_state < battery_capacity:
            charge = min(max_charge_rate, battery_capacity - battery_state)
            battery_state += charge * charge_efficiency
        else:
            charge = 0.0

        data.loc[i, 'BatteryCharge'] = battery_state

    return data

# Apply optimization
data = optimize_battery(data, battery_capacity, max_charge_rate, charge_efficiency, price_threshold)

# Plotting results
plt.figure(figsize=(12,6))
plt.plot(data['Hour'], data['SolarGeneration_kWh'], label='Solar Generation (kWh)')
plt.plot(data['Hour'], data['BatteryCharge'], label='Battery Charge Level (kWh)')
plt.plot(data['Hour'], data['GridPrice_per_kWh']*10, label='Grid Price x10 (for scale)', linestyle='--')
plt.xlabel('Hour')
plt.ylabel('Energy / Price')
plt.title('GreenCharge Optimizer: Solar Battery Scheduling')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
