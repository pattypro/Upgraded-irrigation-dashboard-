
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
from weather_api import fetch_weather_data

st.set_page_config(layout="wide")
st.title("Upgraded Smart Irrigation Dashboard - Treatments T2 to T4")

# --- Sidebar inputs ---
st.sidebar.title("Irrigation Setup")

# Transplant date input
transplant_date = st.sidebar.date_input("Transplant Date", datetime.date(2025, 6, 4))
today = datetime.date.today()
dat = (today - transplant_date).days
st.sidebar.markdown(f"**Days After Transplant (DAT):** {dat}")

# Define growth stage based Kc
if dat <= 20:
    kc = 0.6
elif 21 <= dat <= 40:
    kc = 0.85
elif 41 <= dat <= 75:
    kc = 1.15
else:
    kc = 0.9
st.sidebar.markdown(f"**Kc (Stage-based):** {kc}")

# Emitter configuration
emitter_rate = st.sidebar.number_input("Emitter flow rate (L/hr)", value=2.0)
emitters_per_plant = st.sidebar.number_input("Emitters per plant", value=1)
plant_density = 10  # 10 plants/m²

# GPS coordinates (Utsunomiya Univ.)
lat = 36.547869
lon = 139.911161
et0, forecast_rain = fetch_weather_data(lat, lon)

st.sidebar.markdown(f"**ET₀ (from weather):** {et0} mm")
st.sidebar.markdown(f"**Rain forecast:** {forecast_rain} mm")

# Upload data
uploaded_file = st.file_uploader("Upload CSV with 'timestamp', 'soil_moisture', 'NDVI'", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["timestamp"])
    fc = 38.0
    moisture_threshold = 0.70 * fc

    def decision(row):
        ndvi = row.get("NDVI", 1)
        sm = row.get("soil_moisture", 100)

        irrigate = False
        if (
            ndvi < 0.65 and
            sm < moisture_threshold and
            et0 > 3.5 and
            forecast_rain < 2
        ):
            irrigate = True
        etc = et0 * kc if irrigate else 0
        irrigation_mm = max(0, etc - forecast_rain) if irrigate else 0
        irrigation_time_min = (irrigation_mm * 60) / (plant_density * emitter_rate * emitters_per_plant) if irrigation_mm > 0 else 0
        return pd.Series([irrigate, etc, irrigation_mm, irrigation_time_min])

    df[["irrigate", "ETc", "irrigation_mm", "irrigation_minutes"]] = df.apply(decision, axis=1)

    st.success("Irrigation schedule computed.")
    st.dataframe(df)

    # Plot
    st.subheader("📈 Visualization")
    fig, ax = plt.subplots(figsize=(12, 6))
    for col in ["NDVI", "soil_moisture", "irrigation_mm"]:
        if col in df.columns:
            sns.lineplot(data=df, x="timestamp", y=col, label=col, ax=ax)
    ax.legend()
    ax.set_title("Smart Irrigation Metrics")
    st.pyplot(fig)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Schedule", csv, "schedule.csv", "text/csv")
else:
    st.info("Upload your CSV file to proceed.")
