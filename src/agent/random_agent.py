from agent.base_agent import BaseAgent

class RandomAgent(BaseAgent):
    def __init__(self, base, env, policy=None, verbose=0):
        if env:
            RandomAgent.env = env # store as class attribute to reuse in new loaded instances

    def learn(self, total_timesteps=1):
        print("Skipping learning for RandomAgent...")
        pass

    def predict(self, obs, deterministic=True):
        return RandomAgent.env.action_space.sample(), None

    def save(self, path_str):
        print("Skipping saving for RandomAgent...")
        pass

    def load(base, path_str):
        print("Skipping loading for RandomAgent...")
        return RandomAgent(None, None)
