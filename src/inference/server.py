from typing import Dict
from kserve import Model, ModelServer

from sb3_agent import SB3Agent

class AgentService(Model):
    def __init__(self, name: str):
       super().__init__(name)
       self.name = name
       self.load()

    def load(self):
        self.ready = True

    def predict(self, payload: Dict, headers: Dict[str, str]) -> Dict:
        return {"message": "Hello, world!"}

if __name__ == "__main__":
    svc = AgentService("my-agent")
    ModelServer().start([svc])
