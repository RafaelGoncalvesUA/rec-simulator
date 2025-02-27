from abc import ABC, abstractmethod
from gym import Env

class BaseAgent(ABC):
    @abstractmethod
    def learn(self, env: Env, total_timesteps: int):
        pass

    @abstractmethod
    def save(self, path_str: str):
        pass

    @abstractmethod
    def load(self, path_str: str):
        pass
