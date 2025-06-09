import plotly.express as px
import numpy as np
import pandas as pd
from neuralprophet import NeuralProphet

ts_size = 8760
min_price = -0.01
max_price = 170
period = 8 * 4

x = np.arange(ts_size)
amplitude = (max_price - min_price) / 2
offset = (max_price + min_price) / 2
price_values = amplitude * np.sin(2 * np.pi * x / period) + offset

# Create DataFrame
marginal_price_ts = pd.DataFrame({
    "TIME": pd.date_range(start="2024-01-01", periods=ts_size, freq="15T"),
    "PRICE": price_values
})

marginal_price_ts.to_csv("price.csv", index=False)

fig = px.line(marginal_price_ts, x="TIME", y="PRICE", title="Marginal Price Time Series")
fig.update_traces(line=dict(width=2))
fig.update_layout(
    font=dict(size=18),
    xaxis_title="Time",
    yaxis_title="Price (kWh)",
    xaxis=dict(showgrid=True, zeroline=False),
    yaxis=dict(showgrid=True, zeroline=False),
    plot_bgcolor='white'
)
fig.show()

forecast_steps = [1 * 4, 4 * 4, 8 * 4] 
forecast_horizon = 8*4

marginal_price_ts = pd.read_csv("price.csv")
marginal_price_ts.rename(columns={"PRICE": "y", "TIME": "ds"}, inplace=True)

predictor = NeuralProphet(
    batch_size=32,
    n_lags=forecast_horizon,
    n_forecasts=forecast_horizon,
)
predictor.fit(marginal_price_ts, freq="15T", epochs=100)

forecasts = predictor.predict(marginal_price_ts)
forecasts[[f"yhat{step}" for step in forecast_steps]].to_csv("price_forecasts.csv", index=False)
