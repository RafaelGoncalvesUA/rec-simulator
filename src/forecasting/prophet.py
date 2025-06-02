import pandas as pd
from neuralprophet import NeuralProphet
from sklearn.model_selection import train_test_split
from neuralprophet.utils import save, load

import warnings
warnings.filterwarnings(category=FutureWarning, action="ignore")

NUM_PV = 1

pv_dfs = [
    pd.read_csv(f"../data/renewable/renewable{i+1}.csv.gz", compression='gzip', index_col=0)
    for i in range(1)
]

price_df = pd.read_csv("price.csv")
price_df = price_df.rename(columns={"TIME": "ds", "PRICE": "y"})
price_df['ds'] = pd.to_datetime(price_df['ds'])
price_df = price_df.iloc[:pv_dfs[0].shape[0]]

for i in range(len(pv_dfs)):
    pv_df = pv_dfs[i]
    pv_df["ds"] = price_df["ds"]
    pv_df = pv_df[["ds", "0"]].rename(columns={"0": "y"})
    pv_dfs[i] = pv_df

print(price_df.head())
print(price_df.shape)

print(pv_dfs[0].head())
print(pv_dfs[0].shape)

METRICS = ["MAE", "RMSE"]
METRICS_VAL = ["MAE_val", "RMSE_val"]

def cv_train(df, lags, forecasts):
    folds = NeuralProphet(n_lags=lags, n_forecasts=forecasts)\
        .crossvalidation_split_df(df, freq='15min', k=10)

    metrics_train = pd.DataFrame(columns=METRICS)
    metrics_test = pd.DataFrame(columns=METRICS_VAL)

    n_fold = 1
    for df_train, df_test in folds:
        print(f"Fold {n_fold}/{len(folds)}")
        n_fold += 1
        m = NeuralProphet(n_lags=lags, n_forecasts=forecasts, batch_size=32)
        train = m.fit(df=df_train, freq="15min", validation_df=df_test)
        test = m.test(df=df_test)
        metrics_train = metrics_train.append(train[METRICS].iloc[-1])
        metrics_test = metrics_test.append(test[METRICS_VAL].iloc[-1])

    print(metrics_test.describe().loc[["mean", "std", "min", "max"]])

    return metrics_train, metrics_test

def train(df, lags, forecasts, split=0.67):
    df_train, df_test = train_test_split(df, test_size=split, shuffle=False)
    m = NeuralProphet(n_lags=lags, n_forecasts=forecasts, batch_size=32)
    train_res = m.fit(df=df_train, freq="15min", validation_df=df_test)
    return m, df_train, df_test, train_res

def predict(m, df_train, df_test):
    future = m.make_future_dataframe(df=df_train, periods=len(df_test))
    forecast = m.predict(future)
    return forecast

for RUN in [f"{lags}_{forecasts}" for lags in [24] for forecasts in [12]]:
    try:
        LAGS, FORECASTS = map(int, RUN.split("_"))

        # send_pushover_message("NeuralProphet", f"Run {RUN} started.")
        metrics_train, metrics_test = cv_train(price_df, LAGS, FORECASTS)
        metrics_train.to_csv(f"run_{RUN}_metrics_train.csv", index=False)
        metrics_test.to_csv(f"run_{RUN}_metrics_test.csv", index=False)

        # send_pushover_message("NeuralProphet Train", f"Run {RUN} started.")
        model, df_train, df_test, train_res = train(price_df, LAGS, FORECASTS)
        train_res.to_csv(f"run_{RUN}_train_res.csv", index=False)

        save(model, f"run_{RUN}_model.np")
        model = load(f"run_{RUN}_model.np")

        # send_pushover_message("NeuralProphet Predict", f"Run {RUN} started.")
        forecast = predict(model, df_train, df_test)
        forecast.to_csv(f"run_{RUN}_forecast.csv", index=False)

        # send_pushover_message("NeuralProphet Predict", f"Run {RUN} completed successfully.")

    except Exception as e:
        # send_pushover_message("NeuralProphet Error", f"Run {RUN} failed with error: {e}")
        raise e
