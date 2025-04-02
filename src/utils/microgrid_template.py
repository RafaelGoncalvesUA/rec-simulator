import pandas as pd
from pymgrid import Microgrid
from pymgrid import MicrogridGenerator as mgen
from pymgrid.Environments.pymgrid_cspla import MicroGridEnv as CsDaMicroGridEnv

def get_microgrid_template(mg_id, nb_microgrid=10):
    generator = mgen.MicrogridGenerator(nb_microgrid=nb_microgrid)
    generator.generate_microgrid()
    microgrids = generator.microgrids

    samples = [microgrids[9]] + microgrids[1:5] + [microgrids[6]]
    return samples[mg_id]


def microgrid_from_template(base, new_setting):
    parameters = base.parameters.copy()
    parameters["soc"] = [new_setting["last_soc"]]
    parameters["capa_to_charge"] = [new_setting["last_capa_to_charge"]]
    parameters["capa_to_discharge"] = [new_setting["last_capa_to_discharge"]]

    mg = Microgrid.Microgrid(
        {
            'architecture': base.architecture,
            'load': pd.DataFrame({'Electricity:Facility [kW](Hourly)': new_setting["load"]}),
            'pv': pd.DataFrame({'GH illum (lx)': new_setting["pv"]}),
            'grid_ts': pd.DataFrame({'grid_status': new_setting["grid_ts"]}),
            'df_actions': base._df_record_control_dict,
            'df_status': base._df_record_state,
            'df_actual_generation': base._df_record_actual_production,
            'df_cost': base._df_record_cost,
            'df_co2': base._df_record_co2,
            'grid_price_import': pd.DataFrame({0: new_setting["grid_price_import"]}),
            'grid_price_export': pd.DataFrame({0: new_setting["grid_price_export"]}),
            'grid_co2': pd.DataFrame({'CO2_CISO_I_kwh': new_setting["grid_co2"]}),
            'control_dict': base.control_dict,
            'parameters': parameters,
        }
    )

    new_env = CsDaMicroGridEnv({'microgrid': mg,
                            'forecast_args': None,
                            'resampling_on_reset': False,
                            'baseline_sampling_args': None})

    obs = new_env.reset()
    return obs, mg, new_env