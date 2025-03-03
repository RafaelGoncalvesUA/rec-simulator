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

        params = self.supported_agents[base]

        self.base = params["class"]
        self.env = env
        
        if env:
            self.instance = self.base(**params["kwargs"], env=env)

    def learn(self, total_timesteps=1):
        print(f"Training {self.__class__.__name__} agent for {total_timesteps} timesteps...")
        self.instance.learn(total_timesteps)

    def save(self, path_str):
        print(f"Saving {self.base} agent to {path_str}...")
        self.instance.save(path_str)

    def load(base, path_str):
        print(f"Loading {base} agent from {path_str}...")
        new_agent = SB3Agent(base, None)
        base_cls = SB3Agent.supported_agents[base]["class"]
        new_agent.instance = base_cls.load(path_str)
        return new_agent

# Example: agent = SB3Agent("PPO", env)
