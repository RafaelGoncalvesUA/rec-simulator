from base_agent import BaseAgent
from stable_baselines3 import PPO

class SB3Agent(BaseAgent):
    supported_agents = {
        "PPO": {
            "class": PPO,
            "kwargs": {
                "policy": "MlpPolicy",
                "verbose": 2
            }
        }
    }

    def __init__(self, base, env):
        if base not in self.supported_agents:
            raise ValueError(f"Unsupported agent: {base}")

        args = self.supported_agents[base]

        self.base = args["class"]
        self.env = env
        self.instance = self.base(env, **args["kwargs"])

    def learn(self, env, total_timesteps = 1000):
        print(f"Training {self.__class__.__name__} agent for {total_timesteps} timesteps...")
        self.instance.learn(total_timesteps)

    def save(self, path_str):
        print(f"Saving {self.__class__.__name__} agent to {path_str}...")
        self.instance.save(path_str)

    def load(self, path_str):
        print(f"Loading {self.__class__.__name__} agent from {path_str}...")
        self.instance = self.base.load(path_str)
        return self

# Example: agent = SB3Agent("PPO", env)
