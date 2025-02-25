from kfp import dsl
from kfp.dsl import Input, Model

@dsl.component(
    base_image="rafego16/pipeline-custom-image:latest",
    packages_to_install=["minio"],
)
def agent_storing(agent: Input[Model]):
    from minio import Minio
    from dotenv import load_dotenv
    import os

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
        agent.path.split("/")[-1],
        agent.path,
    )

    print(f"Agent {agent.path.split('/')[-1]} uploaded to MinIO.")
