from pymgrid.Environments.Environment import Environment, generate_sampler
from pymgrid.Environments import Preprocessing
import numpy as np
from gym.spaces import Box

import numpy as np


class BaseEnvironment(Environment):
    def __init__(self, env_config, seed = 42, ns=None):
        # Set seed
        np.random.seed(seed)

        self.states_normalization = Preprocessing.normalize_environment_states(env_config['microgrid'])

        self.TRAIN = True
        # Microgrid
        self.env_config = env_config
        self.mg = env_config['microgrid']
        # State space
        self.mg.train_test_split()
        #np.zeros(2+self.mg.architecture['grid']*3+self.mg.architecture['genset']*1)
        # Number of states
        if ns is None:
            self.Ns = len(self.mg._df_record_state.keys())+1
        else:
            self.Ns = ns
        # Number of actions

        #training_reward_smoothing
        try:
            self.training_reward_smoothing = env_config['training_reward_smoothing']
        except:
            self.training_reward_smoothing = 'sqrt'

        try:
            self.resampling_on_reset = env_config['resampling_on_reset']
        except:
            self.resampling_on_reset = True
        
        if self.resampling_on_reset == True:
            self.forecast_args = env_config['forecast_args']
            self.baseline_sampling_args = env_config['baseline_sampling_args']
            self.saa = generate_sampler(self.mg, self.forecast_args)
        
        # self.observation_space = spaces.Box(low=-1, high=float('inf'), shape=(self.Ns,), dtype=float)
        self.observation_space = Box(low=-1, high=float('inf'), shape=(self.Ns,), dtype=float)
        #np.zeros(len(self.mg._df_record_state.keys()))
        # Action space
        self.metadata = {"render.modes": [ "human"]}
        
        self.state, self.reward, self.done, self.info, self.round = None, None, None, None, None
        self.round = None

        # Start the first round
        self.seed()
        self.reset()
        

        try:
            assert (self.observation_space.contains(self.state))
        except AssertionError:
            print("ERROR : INVALID STATE", self.state)