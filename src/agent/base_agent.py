from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def learn(self, total_timesteps: int):
        pass

    @abstractmethod
    def save(self, path_str: str):
        pass

    @abstractmethod
    def load(path_str: str):
        pass
