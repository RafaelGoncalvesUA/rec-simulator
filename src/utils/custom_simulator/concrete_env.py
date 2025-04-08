from utils.custom_simulator.base_env import BaseEnvironment
from gym.spaces import Discrete
import numpy as np

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
    def __init__(self, env_config, negotiator):
        mg = env_config["microgrid"]
        # include hour, grid_import, grid_export
        super().__init__(env_config, ns=len(mg._df_record_state.keys()) + 3)

        print("Creating custom env...")
        
        self.Na = 2 + self.mg.architecture['grid'] * 3 + self.mg.architecture['genset'] * 1
        
        if self.mg.architecture['grid'] == 1 and self.mg.architecture['genset'] == 1:
            self.Na += 1
        
        self.action_space = Discrete(self.Na)
        self.negotiator = negotiator

    def get_action(self, action):
        return self.get_action_priority_list(action)

    def transition(self, reset=True):
        updated_values = self.mg.get_updated_values()
        updated_values = {x:float(updated_values[x])/self.states_normalization[x] for x in self.states_normalization}  
        updated_values['hour_sin'] = np.sin(2*np.pi*updated_values['hour']) # the hour is already divided by 24 in the line above
        updated_values['hour_cos'] = np.cos(2*np.pi*updated_values['hour'])  
        updated_values.pop('hour', None)

        pv_norm_factor =  max(self.mg.parameters.PV_rated_power.values[0]/6, 1000)
        updated_values.update({"grid_import": self.mg.prev_grid_import/pv_norm_factor, "grid_export": self.mg.prev_grid_export/pv_norm_factor})
        
        s_ = np.array(list(updated_values.values()))

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

        if self.mg._data_set_to_use == "testing":
            next_timestamp = self.mg._tracking_timestep + 1
            self.mg._grid_price_import_train.iloc[next_timestamp,0] = 1.0
            self.mg._grid_price_export_train.iloc[next_timestamp,0] = 1.0

            self.mg._grid_price_import_train.iloc[next_timestamp +1, 0] = 2.0
            self.mg._grid_price_export_train.iloc[next_timestamp +1, 0] = 2.0

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
        if self.mg._data_set_to_use == "testing":
            next_timestamp = self.mg._tracking_timestep + 1
            self.mg._grid_price_import_train.iloc[next_timestamp,0] = 1.0
            self.mg._grid_price_export_train.iloc[next_timestamp,0] = 1.0

            self.mg._grid_price_import_train.iloc[next_timestamp +1, 0] = 2.0
            self.mg._grid_price_export_train.iloc[next_timestamp +1, 0] = 2.0

        # UPDATE THE MICROGRID
        self.mg.run(control_dict)

        # COMPUTE NEW STATE AND REWARD
        self.state, self.info = self.transition(reset=False)
        self.reward = self.get_reward()
        self.done = self.mg.done
        self.round += 1

        return self.state, self.reward, self.done, self.info