from kfp import dsl
from kfp.dsl import Input, Model

@dsl.component(
    base_image="rafego16/pipeline-custom-image:latest",
    packages_to_install=["requests"],
)
def agent_storing(agent_id: int, agent_type: str, agent: Input[Model]):
    from minio import Minio
    from dotenv import load_dotenv
    import os
    import requests

    load_dotenv(dotenv_path="/app/.env")

    minio_client = Minio(
        endpoint=os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=False,
    )

    # create a new bucket called 'agents'
    if not minio_client.bucket_exists("agents"):
        minio_client.make_bucket("agents")

    # upload the agent to the 'agents' bucket
    minio_client.fput_object(
        "agents",
        f"agent_{agent_id}.zip",
        f"{agent.path}/agent.zip",
    )

    print(f"Agent {agent.path.split('/')[-1]} uploaded to MinIO.")

    # notify inference service
    payload = {"agent_id": agent_id, "agent_type": agent_type, "load": True}

    response = requests.post(
        os.getenv("SERVICE_BASE_URL") + "/v1/models/my-agent:predict",
        json=payload,
    )

    assert response.status_code == 200, f"Failed to notify inference service: {response.text}"
    print("Inference service updated with new agent.")
