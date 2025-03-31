from typing import Dict
from kserve import Model, ModelServer
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
import os

from agent.sb3_agent import SB3Agent
load_dotenv(dotenv_path="/app/.env")


class AgentService(Model):
    def __init__(self, name: str):
        super().__init__(name)
        self.name = name
        self.minio_client = None
        self.agent = {}
        self.agent_id = None
        self.load()

    def load(self, agent_type=None):
        if not self.minio_client:
            self.minio_client = Minio(
                endpoint=os.getenv("MINIO_ENDPOINT"),
                access_key=os.getenv("MINIO_ACCESS_KEY"),
                secret_key=os.getenv("MINIO_SECRET_KEY"),
                secure=False,
            )

            # test connection
            self.minio_client.bucket_exists(os.getenv("MINIO_AGENTS_BUCKET"))

        if self.agent_id is not None:
            fname = f"agent-{self.agent_id}.zip"
            self.minio_client.fget_object(os.getenv("MINIO_AGENTS_BUCKET"), fname, fname)
            self.agent[self.agent_id] = SB3Agent.load(agent_type, fname)

        self.ready = True

    def custom_validation(self, payload: Dict):
        if "agent_id" not in payload or not isinstance(payload["agent_id"], int):
            return {"error": "provide an 'agent_id' (int) in the payload"}
        
        if "agent_type" not in payload or not isinstance(payload["agent_type"], str):
            return {"error": "provide an 'agent_type' (str) in the payload"}
        
        if payload["agent_id"] not in self.agent or "load" in payload:
            self.agent_id = payload["agent_id"]
            self.load(payload["agent_type"])
            return {"status": f"loaded agent {self.agent_id}"}

        if "records" not in payload or not isinstance(payload["records"], list):
            return {"error": "payload must be a list of records or a 'load' command"}

    def predict(self, payload: Dict, headers: Dict[str, str] = None) -> Dict:
        error = self.custom_validation(payload)

        if error:
            return error

        agent = self.agent[self.agent_id]

        if not agent:
            return {"status": "agent not loaded yet"}

        action, _ = agent.predict(payload["records"])
        return {"action": action}


if __name__ == "__main__":
    svc = AgentService("my-agent")
    ModelServer().start([svc])
