import pandas as pd
from pymgrid import MicrogridGenerator as mgen
from utils.custom_simulator.concrete_env import CustomEnv
from utils.custom_simulator.microgrid import Microgrid
import pymgrid
import random


def microgrid_generator(nb_microgrid=25) -> mgen.MicrogridGenerator:
    generator = mgen.MicrogridGenerator(nb_microgrid=nb_microgrid, path=pymgrid.__path__[0])
    generator.generate_microgrid(False)
    microgrid_lst = generator.microgrids
    
    return generator, microgrid_lst


def custom_microgrid_generator(nb_microgrid=10) -> mgen.MicrogridGenerator:
    generator = mgen.MicrogridGenerator(nb_microgrid=nb_microgrid, path=pymgrid.__path__[0])
    generator.generate_microgrid(False)
    microgrid_lst = generator.microgrids
    
    samples = [microgrid_lst[9]] + microgrid_lst[1:5] + [microgrid_lst[6]]
    return generator, samples


def get_microgrid_template(mg_id, generator=False):
    if generator:
        generator, _ = microgrid_generator()

    microgrid_lst = generator.microgrids

    samples = [microgrid_lst[9]] + microgrid_lst[1:5] + [microgrid_lst[6]]
    return samples[mg_id]


def shuffle_chunks(lst, chunk_size, seed=None):
    random.seed(seed)
    final_lst = []

    for i in range(0, len(lst), chunk_size):
        chunk = lst[i:i + chunk_size]
        random.shuffle(chunk)
        final_lst += chunk

    return final_lst


def microgrid_from_template(base, new_setting, horizon=24):
    parameters = base.parameters.copy()
    parameters["soc"] = [new_setting["last_soc"]]
    parameters["capa_to_charge"] = [new_setting["last_capa_to_charge"]]
    parameters["capa_to_discharge"] = [new_setting["last_capa_to_discharge"]]

    param_dict = {
        'architecture': base.architecture,
        'load': pd.DataFrame({'Electricity:Facility [kW](Hourly)': new_setting["load"]}),
        'pv': pd.DataFrame({'GH illum (lx)': new_setting["pv"]}),
        'df_actions': base._df_record_control_dict,
        'df_status': base._df_record_state,
        'df_actual_generation': base._df_record_actual_production,
        'df_cost': base._df_record_cost,
        'df_co2': base._df_record_co2,

        'control_dict': base.control_dict,
        'parameters': parameters,
    }
    if "grid_ts" in new_setting:
        param_dict["grid_co2"] = pd.DataFrame({new_setting["grid_co2_iso"]: new_setting["grid_co2"]})
        param_dict["grid_ts"] = pd.DataFrame({'grid_status': new_setting["grid_ts"]})
        param_dict["grid_price_import"] = pd.DataFrame({0: new_setting["grid_price_import"]})
        param_dict["grid_price_export"] = pd.DataFrame({0: new_setting["grid_price_export"]})

    mg = Microgrid(param_dict, horizon=horizon)

    new_env = CustomEnv({'microgrid': mg,
                        'forecast_args': None,
                        'resampling_on_reset': False,
                        'baseline_sampling_args': None},
                        negotiator=None
                        )

    return mg, new_env