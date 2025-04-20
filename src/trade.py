import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from logic.rec import RenewableEnergyCommunity
from utils.microgrid_template import microgrid_generator, microgrid_from_template
import pymarket as pm
from pymarket.bids import BidManager
import pandas as pd
import numpy as np
import pickle as pkl
import random
from dotenv import load_dotenv
from src.utils.notification import send_pushover_message

load_dotenv("./my.env")

NUM_STEPS = 100000 # high enough to cover all the simulation
NUM_RECS = 10
NUM_TENANTS = 5
LOAD_NEW_TS = False
seed = np.random.RandomState(42)

_, samples = microgrid_generator()
print("Generated microgrid templates.\n")

recs = []
market = pm.Market()

marginal_price_ts = pd.read_csv("forecasting/price.csv").iloc[:NUM_STEPS, :]
marginal_price_ts["PRICE"] = marginal_price_ts["PRICE"] / 1000 # convert to kWh

for rec_id in range(NUM_RECS):
    rec = RenewableEnergyCommunity(rec_id, market, marginal_price_ts=marginal_price_ts)
    rec.reset()

    ctr = 0
    while len(rec.microgrids) < NUM_TENANTS:
        template = samples[ctr]

        new_parameters = {
            "last_soc": template._df_record_state["battery_soc"][0],
            "last_capa_to_charge": template._df_record_state["capa_to_charge"][0],
            "last_capa_to_discharge": template._df_record_state["capa_to_discharge"][0],
            "load": template._load_ts["Electricity:Facility [kW](Hourly)"].tolist()[:NUM_STEPS],
            "pv": template._pv_ts["GH illum (lx)"].tolist()[:NUM_STEPS]
        }

        # has connection to the grid
        if hasattr(template, "_grid_status_ts"):
            co2_iso = "CO2_CISO_I_kwh" if "CO2_CISO_I_kwh" in template._grid_co2.columns else "CO2_DUK_I_kwh"
            grid_co2 = template._grid_co2[co2_iso].tolist()[:NUM_STEPS]
            new_parameters["grid_co2_iso"] = co2_iso
            new_parameters["grid_co2"] = grid_co2

            # grid price will be then set by the REC
            new_parameters["grid_price_import"] = marginal_price_ts["PRICE"].tolist()[:NUM_STEPS]
            new_parameters["grid_price_export"] = marginal_price_ts["PRICE"].tolist()[:NUM_STEPS]
            new_parameters["grid_ts"] = [1] * NUM_STEPS
        else:
            ctr += 1
            continue

        if ctr != 0:
            for key in {"load", "pv", "grid_co2"}:
                if LOAD_NEW_TS:
                    with open(f"../data/{key}_{rec_id}_{ctr}.pkl", "rb") as f:
                        new_lst = pkl.load(f)
                    new_parameters[key] = new_lst

                else:
                    new_lst = new_parameters[key].copy()
                    random.shuffle(new_lst)
                    new_parameters[key] = new_lst

                    with open(f"../data/{key}_{rec_id}_{ctr}.pkl", "wb") as f:
                        pkl.dump(new_lst, f)

        print("Using template no. {}...".format(ctr))
        microgrid, env = microgrid_from_template(template, new_parameters)

        rec.add_tenant(microgrid, env)
        ctr += 1
        print()

    print()
    recs.append(rec)

num_iters = 0
num_iters_with_transactions = 0

try:
    while not recs[0].done:
        print("Iteration no. {}".format(num_iters))

        for rec in recs:
            energy_need = rec.handle_exportations()
            rec.negotiate(energy_need)

        transactions, extras = market.run("p2p", r=seed)
        market.bm = BidManager() # clear bids

        if not transactions.get_df().empty:
            num_iters_with_transactions += 1

        for rec in recs:
            rec.handle_market_transactions(transactions.get_df())
            rec.handle_importations()
            rec.step()
            
            absolute_saving = rec.baseline_cost - rec.cost
            percentage_saving = (absolute_saving / rec.baseline_cost) * 100

            # print(f"Saved REC {rec.rec_id}: {absolute_saving:.2f}$ ({percentage_saving:.2f}%)")

        if num_iters % 100 == 0:
            send_pushover_message("Simulation", f"Iteration {num_iters} finished.")

        num_iters += 1

except Exception as e:
    print(f"Simulation interrupted: {e}")
    send_pushover_message("Simulation interrupted", str(e))
    raise e

send_pushover_message("Simulation finished", "Simulation completed successfully.")

for rec in recs:
    logs = pd.DataFrame(rec.logs)
    logs.to_csv(f"rec_{rec.rec_id}.csv", index=False)
print("Simulation finished.")

print(f"Number of iterations: {num_iters}")
print(f"Number of iterations with transactions: {num_iters_with_transactions}")