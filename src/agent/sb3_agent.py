from agent.base_agent import BaseAgent
from agent.policies import *
from stable_baselines3 import PPO, DQN, A2C, SAC

class SB3Agent(BaseAgent):
    supported_agents = {
        "PPO": PPO,
        "DQN": DQN,
        "A2C": A2C,
        "SAC": SAC,
    }

    supported_policies = {
        "MlpPolicy": ("MlpPolicy", None),
        "custom_policy1": ("MlpPolicy", custom_policy1),
    }

    def __init__(self, base, env, policy="MlpPolicy", verbose=2):
        if base not in self.supported_agents:
            raise ValueError(f"Unsupported agent: {base}")

        if policy not in self.supported_policies:
            raise ValueError(f"Unsupported policy: {policy}")

        self.base = self.supported_agents[base]
        self.env = env

        if env:
            policy_str, policy_kwargs = self.supported_policies[policy]
            self.instance = self.base(env=env, verbose=verbose, policy=policy_str, policy_kwargs=policy_kwargs)

    def learn(self, total_timesteps=1):
        print(f"Training {self.__class__.__name__} agent for {total_timesteps} timesteps...")
        self.instance.learn(total_timesteps)

    def predict(self, obs, deterministic=True):
        return self.instance.predict(obs, deterministic=deterministic)

    def save(self, path_str):
        print(f"Saving {self.base} agent to {path_str}...")
        self.instance.save(path_str)

    def load(base, path_str):
        print(f"Loading {base} agent from {path_str}...")
        new_agent = SB3Agent(base, None)
        base_cls = SB3Agent.supported_agents[base]
        new_agent.instance = base_cls.load(path_str)
        return new_agent

# Example: agent = SB3Agent("PPO", env)
