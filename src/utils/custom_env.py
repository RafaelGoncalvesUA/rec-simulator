import gym
from gym import spaces
import numpy as np

class MicrogridEnv(gym.Env):
    def __init__(self, microgrid, api_price_function):
        super(MicrogridEnv, self).__init__()
        
        # Store the microgrid and external price function
        self.microgrid = microgrid
        self.api_price_function = api_price_function
        
        # Define the action space: continuous range [-max_export, max_import]
        self.action_space = spaces.Box(
            low=-100,
            high=100,
            shape=(1,),
            dtype=np.float32
        )
        
        # Define the observation space
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(len(self.microgrid.state_dict()) + 1,),  # Add space for external price
            dtype=np.float32
        )
        
    def reset(self):
        """Resets the environment to its initial state."""
        self.microgrid.reset()
        self.current_price = self.api_price_function()
        return self._get_observation()
    
    def step(self, action):
        """
        Takes a step in the environment given the action.
        
        Args:
        - action: Energy to buy (>0) or sell (<0).
        
        Returns:
        - observation: The new state.
        - reward: The reward for the action.
        - done: Whether the episode is over.
        - info: Additional information.
        """
        # Clip action to the allowable range
        action = np.clip(action, self.action_space.low, self.action_space.high)
        
        # Get the required structure for control
        control = self.microgrid.get_empty_action()

        # Define the grid action
        control['grid'] = [action[0]]  # Assign grid action

        # Assign default actions for the batteries (e.g., no charging or discharging)
        control['battery'] = [0.0 for _ in range(len(self.microgrid.modules.battery))]
        
        # Run the microgrid with the action
        obs, reward, done, info = self.microgrid.step(control, normalized=False)
        
        # Calculate reward (e.g., profit - penalty for unmet load)
        profit = action[0] * self.current_price
        unmet_load_penalty = 10  # Example penalty
        reward = profit - unmet_load_penalty
        
        # Update price
        self.current_price = self.api_price_function()
        
        return self._get_observation(), reward, done, info
    
    def _get_observation(self):
        """
        Combines the microgrid state and the current price into a single observation.
        Returns a flat NumPy array.
        """
        state_dict = self.microgrid.state_dict()
    
        observations = []

        for k, v in state_dict.items():
            if isinstance(v, list):
                for k2, v2 in v[0].items():
                    observations.append(v2)
            else:
                observations.append(v)
                
        return observations[:-2]


def api_price_function():
    """Example function to get the current price."""
    return 0.1  # Placeholder price
