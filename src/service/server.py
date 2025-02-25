from typing import Dict, Union
from kserve import Model, ModelServer

class CustomModel(Model):
    def __init__(self, name: str):
       super().__init__(name)
       self.name = name
       self.load()

    def load(self):
        self.ready = True
        pass

    def predict(self, payload: Dict, headers: Dict[str, str] = None) -> Dict:
        return {"predictions": "hello world"}

if __name__ == "__main__":
    model = CustomModel("custom-model")
    ModelServer().start([model])
