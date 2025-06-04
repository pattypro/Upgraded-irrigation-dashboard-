
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
from weather_api import fetch_weather_data

st.set_page_config(layout="wide")
st.title("Smart Irrigation Dashboard (Treatments T2–T4)")

# Sidebar – Transplant and Growth Info
st.sidebar.title("Crop & Irrigation Settings")
transplant_date = st.sidebar.date_input("Transplant Date", datetime.date(2025, 6, 4))
today = datetime.date.today()
dat = (today - transplant_date).days
st.sidebar.markdown(f"**Days After Transplant (DAT):** {dat}")

# Kc by growth stage
if dat <= 20:
    kc = 0.6
elif 21 <= dat <= 40:
    kc = 0.85
elif 41 <= dat <= 75:
    kc = 1.15
else:
    kc = 0.9
st.sidebar.markdown(f"**Crop Coefficient (Kc):** {kc}")

# Emitter & Spacing Settings
emitter_rate = st.sidebar.number_input("Emitter Flow Rate (L/hr)", value=2.0)
emitters_per_plant = st.sidebar.number_input("Emitters per Plant", value=1)
plant_density = 10  # plants per m²

# Weather API Input
lat, lon = 36.547869, 139.911161
et0, forecast_rain = fetch_weather_data(lat, lon)
st.sidebar.markdown(f"**ET₀:** {et0:.2f} mm/day")
st.sidebar.markdown(f"**Rain Forecast:** {forecast_rain:.2f} mm")

# Upload CSV
uploaded_file = st.file_uploader("Upload your CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["timestamp"])
    required_cols = ["timestamp", "soil_moisture", "NDVI"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"Missing columns in CSV: {', '.join(missing)}")
    else:
        fc = 38.0
        moisture_threshold = 0.70 * fc

        def irrigation_logic(row):
            ndvi = row["NDVI"]
            soil_moisture = row["soil_moisture"]

            irrigate = (
                ndvi < 0.65 and
                soil_moisture < moisture_threshold and
                et0 > 3.5 and
                forecast_rain < 2
            )
            etc = et0 * kc if irrigate else 0
            irrigation_mm = max(0, etc - forecast_rain) if irrigate else 0
            time_min = (
                (irrigation_mm * 60) / (plant_density * emitter_rate * emitters_per_plant)
                if irrigation_mm > 0 else 0
            )
            return pd.Series([irrigate, etc, irrigation_mm, time_min])

        df[["irrigate", "ETc", "irrigation_mm", "irrigation_minutes"]] = df.apply(irrigation_logic, axis=1)

        st.success("Irrigation recommendations calculated.")
        st.dataframe(df)

        # Plotting
        st.subheader("Visualization")
        fig, ax = plt.subplots(figsize=(12, 6))
        for col in ["NDVI", "soil_moisture", "irrigation_mm"]:
            sns.lineplot(data=df, x="timestamp", y=col, label=col, ax=ax)
        ax.set_title("Irrigation Scheduling Overview")
        ax.set_ylabel("Value")
        ax.grid(True)
        st.pyplot(fig)

        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download Schedule", csv_data, "irrigation_schedule.csv", "text/csv")
else:
    st.info("Awaiting CSV upload to continue.")
