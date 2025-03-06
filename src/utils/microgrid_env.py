from pymgrid.envs import DiscreteMicrogridEnv
from pymgrid import Microgrid

import pandas as pd

class CustomMicrogridEnv(DiscreteMicrogridEnv):
    def step(self, action, normalized=False):
        """
        Run one timestep of the environment's dynamics.

        When the end of the episode is reached, you are responsible for calling `reset()`
        to reset the environment's state.

        Accepts an action and returns a tuple (observation, reward, done, info).

        Parameters
        ----------
        action : int or np.ndarray
            An action provided by the agent.

        normalized : bool, default False
            Whether the passed action is normalized or not.

        Returns
        -------
        observation : dict[str, list[float]] or np.ndarray, shape self.observation_space.shape
            Observations of each module after using the passed ``action``.
            ``observation`` is a nested dict if :attr:`~.flat_spaces` is True and a one-dimensional numpy array
            otherwise.

        reward : float
            Reward/cost of running the microgrid. A positive value implies revenue while a negative
            value is a cost.

        done : bool
            Whether the microgrid terminates.

        info : dict
            Additional information from this step.

        """
        self._microgrid_logger.log(net_load=self.compute_net_load())

        action = self.convert_action(action)
        self._log_action(action, normalized)

        obs, reward, done, info = Microgrid.step(self, action, normalized=normalized)
        obs = self._get_obs()

        self.step_callback(**self._get_step_callback_info(action, obs, reward, done, info))

        return obs, reward, done, info
