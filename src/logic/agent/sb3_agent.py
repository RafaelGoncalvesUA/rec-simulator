from .base_agent import BaseAgent
from gym import Env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3 import PPO, DQN, A2C
# from sb3_contrib import QRDQN, RecurrentPPO, ARS, TRPO
import os

from logic.agent._save_callback import SaveOnBestTrainingRewardCallback # TODO: remove

class SB3Agent(BaseAgent):
    # Supported agents for discrete action space
    supported_agents = {
        "PPO": PPO,
        "DQN": DQN,
        "A2C": A2C,
        # "QR-DQN": QRDQN,
        # "RecurrentPPO": RecurrentPPO,
        # "TRPO": TRPO,
        # "ARS": ARS
    }

    custom_default_args = {
        "PPO": {},
        "DQN": {
            "train_freq": 1,
            "buffer_size": 50000,
            "learning_starts": 1000,
            "exploration_final_eps": 0.02,
            "exploration_fraction": 0.25,
        },
        "A2C": {}
    }

    def __init__(self, base: str, env: Env, policy: dict = {}, extra_args: dict = {}):
        if base not in self.supported_agents:
            raise ValueError(f"Unsupported agent: {base}")

        self.base_name = base
        self.base = self.supported_agents[self.base_name]

        os.makedirs("agent/models", exist_ok=True)
        os.makedirs(f"agent/models/{self.base_name}", exist_ok=True)

        if env:
            self.env = Monitor(env, f"agent/models/{self.base_name}/monitor.csv")

            self.instance = self.base(
                "MlpPolicy",
                self.env,
                policy_kwargs=policy,
                **self.custom_default_args[base],
                **extra_args,
            )

    def learn(self, total_timesteps=1, callback=None):
        if not self.env:
            raise ValueError("Environment not set for agent to learn")

        print(f"Training {self.__class__.__name__} agent for {total_timesteps} timesteps...")
        callback_ = SaveOnBestTrainingRewardCallback(check_freq=6000, log_dir=f"agent/models/{self.base_name}") # TODO: remove
        self.instance.learn(total_timesteps, callback=callback_)

    def predict(self, obs, deterministic=True):
        return self.instance.predict(obs, deterministic=deterministic)

    def save(self, path_str):
        print(f"Saving {self.base} agent to {path_str}...")
        self.instance.save(path_str)

    def load(base, path_str, env=None):
        if env:
            print(f"Loading {base} agent from {path_str} with a training environment...")
            new_agent = SB3Agent(base, env)
        else:
            print(f"Loading {base} agent from {path_str} on inference mode...")
            new_agent = SB3Agent(base, None)
            base_cls = SB3Agent.supported_agents[base]
            new_agent.instance = base_cls.load(path_str, env=env)

        return new_agent
