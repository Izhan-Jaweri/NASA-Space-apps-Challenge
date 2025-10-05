import requests
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Step 1: Download OpenAQ data for the US (example: PM2.5, last 1000 records)
def fetch_openaq_us_data():
    # Skip API download, use local sample file
    print('Using local sample_openaq_us.csv file for analysis.')

# Step 2: Preprocess data
def preprocess_data(filepath='sample_openaq_us.csv'):
    df = pd.read_csv(filepath, parse_dates=['datetime'])
    df = df[['datetime', 'value', 'city', 'location']]
    df = df.dropna(subset=['value'])
    df = df.sort_values('datetime')
    return df

# Step 3: Visualize time series
def plot_time_series(df):
    plt.figure(figsize=(12,6))
    plt.plot(df['datetime'], df['value'], marker='.', linestyle='-', alpha=0.5)
    plt.title('US Air Quality (PM2.5) Time Series')
    plt.xlabel('Date')
    plt.ylabel('PM2.5 (µg/m³)')
    plt.tight_layout()
    plt.show()

# Step 4: ETS Decomposition (on daily mean)
def ets_decomposition(df):
    df_daily = df.set_index('datetime').resample('D').mean(numeric_only=True)
    df_daily = df_daily.dropna()
    # Exponential Smoothing (ETS)
    model = ExponentialSmoothing(df_daily['value'], trend='add', seasonal='add', seasonal_periods=7)
    fit = model.fit()
    # Plot original and fitted values
    plt.figure(figsize=(12,6))
    plt.plot(df_daily.index, df_daily['value'], label='Observed')
    plt.plot(df_daily.index, fit.fittedvalues, label='Fitted', linestyle='--')
    plt.title('ETS Decomposition (Exponential Smoothing)')
    plt.xlabel('Date')
    plt.ylabel('PM2.5 (µg/m³)')
    plt.legend()
    plt.tight_layout()
    plt.show()
    return fit

if __name__ == '__main__':
    fetch_openaq_us_data()
    df = preprocess_data()
    plot_time_series(df)
    fit = ets_decomposition(df)
    print(fit.summary())
