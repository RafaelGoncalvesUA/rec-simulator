from kfp import dsl
from kfp.dsl import Input, Output, Artifact


@dsl.component(base_image="rafego16/pipeline-custom-image-train:latest")
def data_preparation(template_id: int, dataset_dir: Input[Artifact], env: Output[Artifact]):
    import os
    import pickle as pkl
    import pandas as pd
    from utils.microgrid_template import get_microgrid_template, microgrid_from_template

    template = get_microgrid_template(template_id)

    # records = pd.read_csv(os.path.join(dataset_dir.path, 'batch.csv'))

    # new_parameters = {
    #     "load": records["obs_0"].tolist(),
    #     "pv": records["obs_1"].tolist(),
    #     "last_soc": records["obs_2"].tolist()[-1],
    #     "last_capa_to_charge": records["obs_3"].tolist()[-1],
    #     "last_capa_to_discharge": records["obs_4"].tolist()[-1],
    #     "grid_ts": records["obs_5"].tolist(),
    #     "grid_co2_iso": "CO2_CISO_I_kwh" if "CO2_CISO_I_kwh" in template._grid_co2.columns else "CO2_DUK_I_kwh",
    #     "grid_co2": records["obs_6"].tolist(),
    #     "grid_price_import": records["obs_7"].tolist(),
    #     "grid_price_export": records["obs_8"].tolist(),
    # }

    marginal_price_ts = pd.read_csv("forecasting/price.csv")
    marginal_price_ts["PRICE"] = marginal_price_ts["PRICE"] / 1000 # convert to kWh

    new_parameters = {
        "last_soc": template._df_record_state["battery_soc"][0],
        "last_capa_to_charge": template._df_record_state["capa_to_charge"][0],
        "last_capa_to_discharge": template._df_record_state["capa_to_discharge"][0],
        "load": template._load_ts["Electricity:Facility [kW](Hourly)"].tolist(),
        "pv": template._pv_ts["GH illum (lx)"].tolist(),
        "co2_iso": "CO2_CISO_I_kwh",
        "grid_co2_iso": "CO2_CISO_I_kwh",
        "grid_co2": template._grid_co2["CO2_CISO_I_kwh"].tolist(),
        "grid_price_import": marginal_price_ts["PRICE"].tolist(),
        "grid_price_export": marginal_price_ts["PRICE"].tolist(),
        "grid_ts": [1] * template._load_ts.shape[0],
    }

    _, microgrid_env = microgrid_from_template(template, new_parameters)

    os.makedirs(env.path, exist_ok=True)

    with open(os.path.join(env.path, 'env.pkl'), 'wb') as f:
        pkl.dump(microgrid_env, f)
    print(f'Microgrid environment saved to {env.path}/env.pkl')
