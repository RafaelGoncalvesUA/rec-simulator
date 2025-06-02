import datetime as dt
import pandas as pd
import numpy as np

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import datetime as dt
import matplotlib.pyplot as plt

from utils.data_importer import OMIEMarginalPriceFileImporter

dateIni = dt.datetime(2024, 1, 1)
dateEnd = dt.datetime(2024, 12, 31)

df = OMIEMarginalPriceFileImporter(date_ini=dateIni, date_end=dateEnd).read_to_dataframe(verbose=True)
df.sort_values(by='DATE', axis=0, inplace=True)

def extract_values(raw, var, value):
    df = raw[raw['CONCEPT'] == var]\
                .drop(columns=['CONCEPT'])\
                .melt(id_vars=["DATE"],
                    value_vars=[f"H{i}" for i in range(1, 25)],
                    var_name="HOUR", 
                    value_name=value
                )
    df["HOUR"] = df["HOUR"].str.extract(r"H(\d+)").astype(int)
    df["TIME"] = pd.to_datetime(df["DATE"]) + pd.to_timedelta(df["HOUR"] - 1, unit='h')
    df.drop(columns=["DATE", "HOUR"], inplace=True)
    df = df[["TIME", value]] # reorder columns
    df.sort_values(by=['TIME'], axis=0, inplace=True)
    df.set_index("TIME", inplace=True)
    return df


def disaggregate_energy_random(df):
    df = df.copy()
    new_rows = []

    for timestamp, row in df.iterrows():
        base_time = timestamp
        energy = row["ENERGY"]

        # Generate 4 random proportions that sum to 1
        proportions = np.random.dirichlet(np.ones(4), size=1).flatten()

        for i, p in enumerate(proportions):
            new_time = base_time + pd.Timedelta(minutes=15 * i)
            new_rows.append({"TIME": new_time, "ENERGY": energy * p})

    new_df = pd.DataFrame(new_rows).set_index("TIME").sort_index()
    return new_df


# Extract energy price and interpolate missing values (15 min)
price_df = extract_values(df, "PRICE_PT", "PRICE")
price_df.to_csv("data/raw_price.csv")

price_df.resample("15T").interpolate(method="linear").to_csv("data/price.csv")

# # Extract energy to buy and divide by the 4 quarters
# energy_df = extract_values(df, "ENER_PURCH_PT", "ENERGY")
# energy_df.to_csv("data/raw_purch_energy.csv")

# disaggregate_energy_random(energy_df).to_csv("data/purch_energy.csv")

# # Extract energy to sell and divide by the 4 quarters
# energy_df = extract_values(df, "ENER_SALE_PT", "ENERGY")
# energy_df.to_csv("data/raw_sale_energy.csv")

# disaggregate_energy_random(energy_df).to_csv("data/sale_energy.csv")