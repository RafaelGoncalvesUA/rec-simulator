from .base_agent import BaseAgent
from gym import Env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3 import PPO, DQN, A2C
import pymgrid
from utils.custom_simulator import microgrid_generator as mgen
from utils.custom_simulator.concrete_env import CustomEnv

class SB3Agent(BaseAgent):
    supported_agents = {"PPO": PPO, "DQN": DQN, "A2C": A2C}

    def __init__(self, base: str, env: Env, extra_args: dict = {}):
        self.base_name = base
        self.base = self.supported_agents[self.base_name]
        self.env = Monitor(env, "monitor.csv")
        self.instance = self.base("MlpPolicy", self.env, **extra_args)
        self.logs = []

    def learn(self, total_timesteps=1, callback=None):
        print(f"Training {self.__class__.__name__} agent for {total_timesteps} timesteps...")
        self.instance.learn(total_timesteps, callback=callback)

    def predict(self, obs, deterministic=True):
        return self.instance.predict(obs, deterministic=deterministic)

    # Generator
    def episode(self):
        obs = self.env.reset()
        done = False
        while not done:
            action, _ = self.instance.predict(obs, deterministic=True)
            obs, reward, done, info = self.env.step(action)
            yield obs, reward, done, info

if __name__ == "__main__":
    generator = mgen.MicrogridGenerator(path=pymgrid.__path__[0]).generate_microgrid()
    mg = generator.microgrids[9]

    env = CustomEnv({'microgrid': mg, 'forecast_args': None, 'resampling_on_reset': False})
    agent = SB3Agent("PPO", env, extra_args={"learning_rate": 0.001})
    agent.learn(total_timesteps=10000)

    ep = agent.episode()

    for _ in range(10): # stop after 10 steps (lazy)
        obs, reward, done, info = next(ep)
        print(obs, reward, done, info)