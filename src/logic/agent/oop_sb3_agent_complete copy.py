from .base_agent import BaseAgent
from gym import Env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3 import PPO, DQN, A2C
import os
import random

random.seed(42)

class SB3Agent(BaseAgent):
    supported_agents = {"PPO": PPO, "DQN": DQN, "A2C": A2C}

    def __init__(self, base: str, env: Env, policy: dict = {}, extra_args: dict = {}):
        if base not in self.supported_agents:
            raise ValueError(f"Unsupported agent: {base}")

        self.base_name = base
        self.base = self.supported_agents[self.base_name]

        os.makedirs("logic/agent/models", exist_ok=True)
        os.makedirs(f"logic/agent/models/{self.base_name}", exist_ok=True)

        self.env = Monitor(env, f"logic/agent/models/{self.base_name}/monitor.csv")
        self.instance = self.base("MlpPolicy", self.env, policy_kwargs=policy, **extra_args)
        self.logs = []

    def learn(self, total_timesteps=1, callback=None):
        if not self.instance:
            raise ValueError("Environment not set for agent to learn")

        print(f"Training {self.__class__.__name__} agent for {total_timesteps} timesteps...")
        self.instance.learn(total_timesteps, callback=callback)

    def predict(self, obs, deterministic=True):
        return self.instance.predict(obs, deterministic=deterministic)

    def episode(self):
        if not self.instance:
            raise ValueError("Environment not set for agent to replay")

        obs = self.env.reset()
        done = False
        while not done:
            action, _ = self.instance.predict(obs, deterministic=True)
            obs, reward, done, info = self.env.step(action)
            yield obs, reward, done, info

    def save(self, path_str):
        print(f"Saving {self.base} agent to {path_str}...")
        self.instance.save(path_str)

    def load(base, path_str, env=None):
        print(f"Loading {base} agent from {path_str} on inference mode...")
        new_agent = SB3Agent(base, None)
        base_cls = SB3Agent.supported_agents[base]
        new_agent.instance = base_cls.load(path_str)

        return new_agent

if __name__ == "__main__":
    import pymgrid
    from utils.custom_simulator import microgrid_generator as mgen
    from utils.custom_simulator.concrete_env import CustomEnv

    generator = mgen.MicrogridGenerator(nb_microgrid=25, random_seed=42, path=pymgrid.__path__[0])
    generator.generate_microgrid()
    mg = generator.microgrids[9]

    env = CustomEnv({'microgrid': mg,
                'forecast_args': None,
                'resampling_on_reset': False,
                'baseline_sampling_args': None},
            )
    
    agent = SB3Agent("PPO", env, policy={"activation_fn": "ReLU", "net_arch": [128, 128]}, extra_args={"learning_rate": 0.001})
    agent.learn(total_timesteps=10000)

    ep = agent.episode()

    for _ in range(10): # stop after 10 steps (lazy)
        obs, reward, done, info = next(ep)
        print(obs, reward, done, info)