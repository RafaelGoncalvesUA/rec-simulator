import pandas as pd
from neuralprophet import NeuralProphet

marginal_price_ts = pd.read_csv("data/price.csv")
marginal_price_ts.to_csv("price.csv", index=False)
marginal_price_ts.rename(columns={"PRICE": "y", "TIME": "ds"}, inplace=True)

forecast_steps = [1, 8, 12]
n_lags = 24
forecast_horizon = 12

predictor = NeuralProphet(
    batch_size=32,
    n_lags=n_lags,
    n_forecasts=forecast_horizon,
)
predictor.fit(marginal_price_ts, freq="15T", epochs=100)

forecasts = predictor.predict(marginal_price_ts)
forecasts[[f"yhat{step}" for step in forecast_steps]].to_csv("price_forecasts.csv", index=False)
