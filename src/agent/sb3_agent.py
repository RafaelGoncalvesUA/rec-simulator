from agent.base_agent import BaseAgent
from stable_baselines3 import PPO, DQN, A2C
# from sb3_contrib import QRDQN, RecurrentPPO, ARS, TRPO

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

    def __init__(self, base, env, policy=None, verbose=2):
        if base not in self.supported_agents:
            raise ValueError(f"Unsupported agent: {base}")

        self.base = self.supported_agents[base]
        self.env = env

        if env:
            self.instance = self.base(env=env, verbose=verbose, policy="MlpPolicy", policy_kwargs=policy)

    def learn(self, total_timesteps=1):
        print(f"Training {self.__class__.__name__} agent for {total_timesteps} timesteps...")
        self.instance.learn(total_timesteps, log_interval=1)

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
