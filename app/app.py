# app.py
import streamlit as st
import requests
import pandas as pd
import altair as alt
import plotly.express as px
import pydeck as pdk
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
from dateutil import parser

# ---------------------------
# Page config & CSS
# ---------------------------
st.set_page_config(page_title="CleanAir Now (Streamlit)", layout="wide")
st.markdown("""
    <style>
    .header {font-size:28px; font-weight:700;}
    .sub {color: #6c6c6c; margin-top:-10px}
    .card {background: #f8f9fa; padding:10px; border-radius:8px}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="header">🌍 CleanAir Now — Real-time Air Quality & Alerts</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Live ground-station data (OpenAQ). Choose chart & map style below.</div>', unsafe_allow_html=True)

# ---------------------------
# Helper: Fetch OpenAQ measurements
# ---------------------------
@st.cache_data(ttl=300)
def fetch_openaq(city: str, parameter: str, limit: int = 200):
    base = "https://api.openaq.org/v2/measurements"
    params = {
        "city": city,
        "parameter": parameter,
        "limit": limit,
        "sort": "desc",
        "order_by": "date"
    }
    try:
        r = requests.get(base, params=params, timeout=15)
        r.raise_for_status()
        j = r.json()
        results = j.get("results", [])
        if not results:
            return pd.DataFrame()
        df = pd.DataFrame(results)
        df['date_local'] = df['date'].apply(lambda x: parser.parse(x['local']))
        def get_lat(row):
            c = row.get('coordinates')
            return c.get('latitude') if c else None
        def get_lon(row):
            c = row.get('coordinates')
            return c.get('longitude') if c else None
        df['lat'] = df.apply(get_lat, axis=1)
        df['lon'] = df.apply(get_lon, axis=1)
        df = df.sort_values('date_local')
        return df
    except Exception as e:
        st.error(f"Error fetching OpenAQ: {e}")
        return pd.DataFrame()

# ---------------------------
# Forecast + Alert helpers
# ---------------------------
def make_forecast(df: pd.DataFrame, hours_ahead: int = 6):
    if df.empty:
        return pd.DataFrame()
    last_ts = df['date_local'].max()
    last_val = df['value'].iloc[-1]
    window = df['value'].dropna().tail(3)
    rolling_val = float(window.mean()) if len(window)>0 else last_val
    rows = []
    for i in range(1, hours_ahead + 1):
        t = last_ts + timedelta(hours=i)
        rows.append({"date": t, "persistence": last_val, "rolling": rolling_val})
    return pd.DataFrame(rows)

WHO_LIKE = {"pm25": 15, "no2": 40, "o3": 100, "pm10": 45}
def get_alert_message(param, value):
    limit = WHO_LIKE.get(param, 35)
    if pd.isna(value):
        return ("No data", "grey", "No recent measurement available.")
    if value <= limit:
        return ("Good", "green", f"{param.upper()} = {value:.1f} µg/m³. Air quality is good.")
    elif value <= 2*limit:
        return ("Moderate", "orange", f"{param.upper()} = {value:.1f} µg/m³. Sensitive groups should limit prolonged outdoor exertion.")
    else:
        return ("Unhealthy", "red", f"{param.upper()} = {value:.1f} µg/m³. Reduce outdoor activities; vulnerable people should stay indoors.")

# ---------------------------
# Sidebar: user controls
# ---------------------------
st.sidebar.header("Query & Display Options")
default_city = "Karachi"
city = st.sidebar.text_input("City name (as listed in OpenAQ)", default_city)
param = st.sidebar.selectbox("Pollutant", ["pm25", "no2", "o3", "pm10"])
hours_forecast = st.sidebar.slider("Forecast horizon (hours)", 3, 24, 6)
records = st.sidebar.slider("Fetch records (limit)", 50, 500, 200)
chart_lib = st.sidebar.selectbox("Chart library", ["Altair", "Plotly"])
map_lib = st.sidebar.selectbox("Map library", ["Folium", "Pydeck"])
if st.sidebar.button("Fetch Data"):
    st.experimental_rerun()

# ---------------------------
# Fetch data
# ---------------------------
df = fetch_openaq(city, param, limit=records)

# ---------------------------
# Top metrics + alert card
# ---------------------------
col_a, col_b, col_c, col_d = st.columns([1,1,1,1])
if df.empty:
    col_a.metric("Latest", "—")
    col_b.metric("24hr avg", "—")
    col_c.metric("24hr max", "—")
    col_d.info("No data found. Try different city or parameter.")
else:
    last_val = float(df['value'].iloc[-1])
    last_ts = df['date_local'].max()
    # 24hr window
    window = df[df['date_local'] >= last_ts - timedelta(hours=24)]
    avg_24 = window['value'].mean() if not window.empty else float('nan')
    max_24 = window['value'].max() if not window.empty else float('nan')
    col_a.metric("Latest", f"{last_val:.1f} {df['unit'].iloc[-1]}", delta=None)
    col_b.metric("24h avg", f"{avg_24:.1f}" if not pd.isna(avg_24) else "—")
    col_c.metric("24h max", f"{max_24:.1f}" if not pd.isna(max_24) else "—")
    # alert card
    status, color, msg = get_alert_message(param, last_val)
    if color == "green":
        col_d.success(f"{status} — {msg}")
    elif color == "orange":
        col_d.warning(f"{status} — {msg}")
    elif color == "red":
        col_d.error(f"{status} — {msg}")
    else:
        col_d.info(msg)

st.markdown("---")

# ---------------------------
# Time series + forecast chart
# ---------------------------
st.subheader("📈 Time Series (observations) + Forecast")

if not df.empty:
    last_ts = df['date_local'].max()
    window = df[df['date_local'] >= last_ts - timedelta(hours=48)]
    if window.empty:
        window = df.copy()

    forecast_df = make_forecast(df, hours_ahead=hours_forecast)

    # Prepare dataframes for plotting
    obs_plot = window[['date_local', 'value']].rename(columns={'date_local':'Time','value':'Value'})
    if not forecast_df.empty:
        p_persist = forecast_df[['date','persistence']].rename(columns={'date':'Time','persistence':'Value'})
        p_rolling = forecast_df[['date','rolling']].rename(columns={'date':'Time','rolling':'Value'})

    if chart_lib == "Altair":
        base = alt.Chart(obs_plot).mark_line(point=True).encode(x='Time:T', y='Value:Q')
        if not forecast_df.empty:
            persist_chart = alt.Chart(p_persist).mark_line(strokeDash=[5,2], color="red").encode(x='Time:T', y='Value:Q')
            rolling_chart = alt.Chart(p_rolling).mark_line(strokeDash=[2,2], color="orange").encode(x='Time:T', y='Value:Q')
            combined = (base + persist_chart + rolling_chart).resolve_scale(y='shared')
            st.altair_chart(combined, use_container_width=True)
        else:
            st.altair_chart(base, use_container_width=True)

    else:  # Plotly
        fig = px.line(obs_plot, x='Time', y='Value', labels={"Value": f"{param.upper()} ({window['unit'].iloc[0]})"})
        if not forecast_df.empty:
            fig.add_scatter(x=p_persist['Time'], y=p_persist['Value'], mode='lines', name='Persistence Forecast', line=dict(dash='dash', color='red'))
            fig.add_scatter(x=p_rolling['Time'], y=p_rolling['Value'], mode='lines', name='Rolling Forecast', line=dict(dash='dot', color='orange'))
        fig.update_layout(height=400, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No time-series to show.")

st.markdown("---")

# ---------------------------
# Map section (Folium or Pydeck)
# ---------------------------
st.subheader("🗺 Monitoring Stations Map")

if df.empty or not df['lat'].notna().any():
    st.info("No station coordinates available to plot on map.")
else:
    valid_coords = df.dropna(subset=['lat','lon']).copy()
    # reduce duplicates by location name (take latest per location)
    valid_coords = valid_coords.sort_values('date_local').groupby('location').tail(1)
    center_lat = valid_coords['lat'].mean()
    center_lon = valid_coords['lon'].mean()
    limit = WHO_LIKE.get(param, 35)

    if map_lib == "Folium":
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles="CartoDB positron")
        for _, row in valid_coords.iterrows():
            try:
                v = float(row['value'])
                color = "green" if v <= limit else "orange" if v <= 2*limit else "red"
                popup = folium.Popup(f"<b>{row['location']}</b><br>{row['value']} {row['unit']}<br>{row['date_local']}", max_width=300)
                folium.CircleMarker(
                    location=[row['lat'], row['lon']],
                    radius=8,
                    color=color,
                    fill=True,
                    fill_opacity=0.9,
                    popup=popup
                ).add_to(m)
            except Exception:
                continue
        st_data = st_folium(m, width=900, height=500)

    else:  # Pydeck
        # prepare color by value
        def rgb_for(v):
            if v <= limit:
                return [0, 180, 0]
            elif v <= 2*limit:
                return [255, 165, 0]
            else:
                return [220, 20, 60]
        valid_coords['color'] = valid_coords['value'].apply(lambda x: rgb_for(float(x)))
        # pydeck layer
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=valid_coords,
            get_position='[lon, lat]',
            get_fill_color='color',
            get_radius=1000,
            pickable=True,
            auto_highlight=True
        )
        view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=10, pitch=0)
        tooltip = {"html": "<b>{location}</b><br>Value: {value} {unit}<br>Time: {date_local}", "style": {"color": "white"}}
        deck = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip)
        st.pydeck_chart(deck)

st.markdown("---")

# ---------------------------
# Export CSV
# ---------------------------
st.subheader("📥 Export / Report")
if not df.empty:
    export_df = df[['date_local','value','unit','location','lat','lon']].copy().rename(columns={'date_local':'datetime'})
    csv = export_df.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download CSV (last records)", data=csv, file_name=f"{city}_{param}_data.csv", mime='text/csv')
else:
    st.info("No data to export.")

# ---------------------------
# Footer notes
# ---------------------------
st.markdown("""
**Notes & next steps (for judges):**
- This prototype uses OpenAQ (ground stations). We can integrate TEMPO (satellite) and weather (OpenWeatherMap/ECMWF) for improved forecasts.
- Forecast here is a baseline (persistence + rolling average). Replace with ML/hybrid model for production.
- Built with Streamlit for rapid prototyping — backend can be separated into FastAPI and front-end moved to React if required.
""")




