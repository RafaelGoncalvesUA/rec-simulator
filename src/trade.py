import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from logic.rec import RenewableEnergyCommunity
from utils.microgrid_template import microgrid_generator, get_microgrid_template, microgrid_from_template

import random

random.seed(1234)

NUM_STEPS = 100
NUM_RECS = 1
NUM_TENANTS = 5

_, samples = microgrid_generator()
print("Generated microgrid templates.\n")

recs = []

for rec_id in range(NUM_RECS):
    rec = RenewableEnergyCommunity(rec_id, None)
    rec.reset()

    ctr = 0
    while len(rec.microgrids) < NUM_TENANTS:
        template = samples[ctr]

        new_parameters = {
            "last_soc": template._df_record_state["battery_soc"][0],
            "last_capa_to_charge": template._df_record_state["capa_to_charge"][0],
            "last_capa_to_discharge": template._df_record_state["capa_to_discharge"][0],
            "load": template._load_ts["Electricity:Facility [kW](Hourly)"][:NUM_STEPS],
            "pv": template._pv_ts["GH illum (lx)"].tolist()[:NUM_STEPS]
        }

        # has connection to the grid
        if hasattr(template, "_grid_status_ts"):
            co2_iso = "CO2_CISO_I_kwh" if "CO2_CISO_I_kwh" in template._grid_co2.columns else "CO2_DUK_I_kwh"
            grid_co2 = template._grid_co2[co2_iso].tolist()[:NUM_STEPS]
            new_parameters["grid_co2_iso"] = co2_iso
            new_parameters["grid_co2"] = grid_co2

            # grid price will be then set by the REC
            new_parameters["grid_price_import"] = template._grid_price_import[0].tolist()[:NUM_STEPS]
            new_parameters["grid_price_export"] = template._grid_price_export[0].tolist()[:NUM_STEPS]
            new_parameters["grid_ts"] = [1] * NUM_STEPS
        else:
            ctr += 1
            continue

        if ctr != 0:
            for key in {"load", "pv", "grid_co2"}:
                new_lst = new_parameters[key].copy()
                random.shuffle(new_lst)
                new_parameters[key] = new_lst

        print("Using template no. {}...".format(ctr))
        microgrid, env = microgrid_from_template(template, new_parameters)
        
        rec.add_tenant(microgrid, env)
        ctr += 1
        print()

    print()
    recs.append(rec)

while not recs[0].done:
    for rec in recs:
        rec.step()
        print()


