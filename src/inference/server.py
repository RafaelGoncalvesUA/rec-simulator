from typing import Dict
from kserve import Model, ModelServer
from sb3_agent import SB3Agent
from minio import Minio
from datetime import datetime
from dotenv import load_dotenv
import json
import os

MAX_BATCH_SIZE = 10
load_dotenv(dotenv_path="/app/.env")

class AgentService(Model):
    def __init__(self, name: str):
        super().__init__(name)
        self.name = name
        self.load()
        self.buffer = []
        self.ctr = 0
        self.minio_client = None

    def load(self):
        if not self.minio_client:
            self.minio_client = Minio(
                endpoint=os.getenv("MINIO_ENDPOINT"),
                access_key=os.getenv("MINIO_ACCESS_KEY"),
                secret_key=os.getenv("MINIO_SECRET_KEY"),
                secure=False,
            )

        self.minio_client.fget_object(os.getenv("MINIO_AGENTS_BUCKET"), "agent.zip", "agent.zip")
        self.agent = SB3Agent.load("PPO", "agent.zip")
        self.ready = True

    def predict(self, payload: Dict, headers: Dict[str, str] = None) -> Dict:
        if not isinstance(payload, list):
            if "load" in payload:
                self.load()
                return {"status": "loaded"}

            return {"error": "payload must be a list of records or a 'load' command"}
        
        self.buffer += payload
        self.ctr += 1

        # TODO: action prediction

        if self.ctr < MAX_BATCH_SIZE:
            return {"action": "PLACE_HERE_PREDICTION"}

        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"batch_{timestamp}.json"

        # Save buffer as json
        with open(filename, "w") as f:
            json.dump(self.buffer, f, indent=4)

        # Upload to MinIO
        self.minio_client.fput_object(os.getenv("MINIO_BATCHES_BUCKET"), filename, filename)
        print(f"Uploaded {filename} to MinIO bucket 'batches'.")

        # Delete local file after upload
        os.remove(filename)

        # Clear batch
        self.buffer.clear()
        self.ctr = 0

        # kfp_client_manager = KFPClientManager(
        #     api_url="http://localhost:8080/pipeline",

        #     dex_username="user@example.com",
        #     dex_password="12341234",

        #     skip_tls_verify=True,
        #     dex_auth_type="local",
        # )

        # kfp_client = kfp_client_manager.create_kfp_client()

        # run = kfp_client.create_run_from_pipeline_package(
        #     pipeline_file='../pipeline.yaml',
        #     namespace='kubeflow-user-example-com',
        #     arguments={
        #         'batch_file': filename,
        #     },
        # )

        return {"action": "PLACE_HERE_PREDICTION"}

if __name__ == "__main__":
    svc = AgentService("my-agent")
    ModelServer().start([svc])
