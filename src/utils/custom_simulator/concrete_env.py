from utils.custom_simulator.base_env import BaseEnvironment
from pymgrid.Environments import Preprocessing
from gym.spaces import Discrete
from neuralprophet import NeuralProphet
import datetime
import pandas as pd
import numpy as np
import logging

# disable all
logging.getLogger("NP").setLevel(logging.CRITICAL)

def normalize_environment_states(mg):
    max_values = {}
    for keys in list(mg._df_record_state.keys()) + ['grid_import', 'grid_export']:
        if keys == 'hour':
            max_values[keys] = 24
        elif keys == 'capa_to_charge' or keys == 'capa_to_discharge' :
            max_values[keys] = mg.parameters.battery_capacity.values[0]
        elif keys == 'grid_status' or keys == 'battery_soc':
            max_values[keys] = 1
        elif keys == 'grid_co2':
            max_values[keys] = max(mg._grid_co2.values[0])
        elif keys == 'grid_price_import':
            max_values[keys] = max(mg._grid_price_import.values[0]) 
        elif keys == 'grid_price_export':
            max_values[keys] = max(mg._grid_price_import.values[0]) 
        elif keys == 'load':
            max_values[keys] = mg.parameters.load.values[0]
        elif keys == 'pv':
            max_values[keys] = mg.parameters.PV_rated_power.values[0]
        elif keys == 'grid_import':
            max_values[keys] = 1000
        elif keys == 'grid_export':
            max_values[keys] = 1000
        else:
            max_values[keys] = mg.parameters[keys].values[0] 
            
    return max_values


class CustomEnv(BaseEnvironment):
    def __init__(
        self,
        env_config,
        predictors: dict[str, NeuralProphet] = None,
        n_lags=0,
        forecast_steps=[],
        first_timestamp=datetime.datetime(2024, 1, 1),
        price_forecasts_file="forecasting/price_forecasts.csv"
    ):
        mg = env_config["microgrid"]

        self.predictors = predictors
        self.n_lags = n_lags
        self.forecast_steps = forecast_steps

        if self.predictors:
            self.forecast_horizon = forecast_steps[-1]
            self.records = {p: [] for p in self.predictors}
        else:
            self.forecast_horizon = 0

        self.first_timestamp = first_timestamp 
        self.price_forecasts = pd.read_csv(price_forecasts_file)

        super().__init__(env_config, ns=len(mg._df_record_state.keys()) + 1 + len(self.forecast_steps))
        print("Creating custom env...")

        self.Na = 2 + self.mg.architecture['grid'] * 3 + self.mg.architecture['genset'] * 1
        
        if self.mg.architecture['grid'] == 1 and self.mg.architecture['genset'] == 1:
            self.Na += 1
        
        self.action_space = Discrete(self.Na)

    def get_action(self, action):
        return self.get_action_priority_list(action)

    def transition(self, reset=True):
        updated_values = self.mg.get_updated_values()
        # print("updated_values", updated_values)
        updated_values = {x:float(updated_values[x])/self.states_normalization[x] for x in self.states_normalization}  
        updated_values['hour_sin'] = np.sin(2*np.pi*updated_values['hour']) # the hour is already divided by 24 in the line above
        updated_values['hour_cos'] = np.cos(2*np.pi*updated_values['hour'])  
        updated_values.pop('hour', None)

        first_window_date = self.first_timestamp + datetime.timedelta(hours=self.mg._tracking_timestep-self.n_lags)
        time_window = [first_window_date + datetime.timedelta(hours=i) for i in range(self.n_lags + self.forecast_horizon)]

        s_ = np.array(list(updated_values.values()))

        if self.predictors:
            for p, predictor in self.predictors.items():
                self.records[p].append(self.mg._df_record_state[p][-1])

                if len(self.records[p]) < self.n_lags + self.forecast_horizon:
                    # use average
                    forecasts = [np.mean(self.records[p])] * len(self.forecast_steps)

                    if reset:
                        self.records[p] = self.records[p][:-1]
                else:
                    forecasts = [max(x, -0.01) for x in self.price_forecasts.iloc[len(self.records[p])-1].values]
                
                s_ = np.append(s_, forecasts)

        if reset:
            return s_

        return s_, updated_values

    def step(self, action):
        # CONTROL
        if self.done:
            print("WARNING : EPISODE DONE")  # should never reach this point
            return self.state, self.reward, self.done, self.info
        try:
            assert (self.observation_space.contains(self.state))
        except AssertionError:
            print("ERROR : INVALID STATE", self.state)

        try:
            assert (self.action_space.contains(action))
        except AssertionError:
            print("ERROR : INVALD ACTION", action)

        # UPDATE THE MICROGRID
        control_dict = self.get_action(action)
        self.mg.run(control_dict)

        # COMPUTE NEW STATE AND REWARD
        self.state, self.info = self.transition(reset=False)
        self.reward = self.get_reward()
        self.done = self.mg.done
        self.round += 1

        return self.state, self.reward, self.done, self.info

    def run_step(self, control_dict):
        # UPDATE THE MICROGRID
        self.mg.run(control_dict)

        # COMPUTE NEW STATE AND REWARD
        self.state, self.info = self.transition(reset=False)
        self.reward = self.get_reward()
        self.done = self.mg.done
        self.round += 1

        return self.state, self.reward, self.done, self.info
    
    def reset(self, testing=False):
        if not testing and self.predictors:
            self.records = {p: [] for p in self.predictors}

        if "testing" in self.env_config:
            testing = self.env_config["testing"]
        self.round = 1
        # Reseting microgrid
        self.mg.reset(testing=testing)
        if testing == True:
            self.TRAIN = False
        elif self.resampling_on_reset == True:
            Preprocessing.sample_reset(self.mg.architecture['grid'] == 1, self.saa, self.mg, sampling_args=sampling_args)
        
        
        self.state, self.reward, self.done, self.info =  self.transition(), 0, False, {}
        
        # return self.state, self.info
        return self.state