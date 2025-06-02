from kfp_client_manager import KFPClientManager
from db import get_db_conn
from dotenv import load_dotenv
import os
import time

load_dotenv(dotenv_path="/app/.env")

DATABASE = os.getenv("DATABASE_NAME")
USER = os.getenv("DATABASE_USER")
PASSWORD = os.getenv("DATABASE_PASSWORD")
HOST = os.getenv("DATABASE_HOST")
PORT = os.getenv("DATABASE_PORT")
MAX_OBS_SIZE = int(os.getenv("MAX_OBS_SIZE"))
MAX_BUFFER_SIZE = int(os.getenv("MAX_BUFFER_SIZE"))
VERIFICATION_INTERVAL = int(os.getenv("VERIFICATION_INTERVAL"))
AGENT_TYPE = os.getenv("AGENT_TYPE")
TRIGGER_COND = os.getenv("TRIGGER_COND")

conn, cursor = get_db_conn(DATABASE, USER, PASSWORD, HOST, PORT, MAX_OBS_SIZE)


def deploy_training_pipeline(tenant_id, agent_type):
    kfp_client_manager = KFPClientManager(
        api_url="http://localhost:8080/pipeline",
        dex_username="user@example.com",
        dex_password="12341234",
        skip_tls_verify=True,
        dex_auth_type="local",
    )

    kfp_client = kfp_client_manager.create_kfp_client()

    _ = kfp_client.create_run_from_pipeline_package(
        pipeline_file="pipeline.yaml",
        namespace="kubeflow-user-example-com",
        arguments={
            "agent_id": tenant_id,
            "agent_type": agent_type,
            "template_id": tenant_id, # e.g. use template 0 for tenant 0 
        },
    )


def trigger(cursor, tenant_id, cond):
    if cond == "buffer_size":
        cursor.execute(f"SELECT COUNT(*) FROM microgrid_data WHERE tenant_id = '{tenant_id}'")
        count = cursor.fetchone()[0]
        return count >= MAX_BUFFER_SIZE
    else:
        raise ValueError(f"Condition {cond} not available")


# (for all available tenants) verfify if one has surpassed the buffer size
while True:
    cursor.execute("SELECT tenant_id FROM microgrid_data")
    tenants = cursor.fetchall()

    for tenant in tenants:
        tenant_id = int(tenant[0])
        print(f"Verifying tenant {tenant_id}")

        if trigger(cursor, tenant_id, TRIGGER_COND):
            print(f"Deploying training pipeline for tenant {tenant_id}")
            deploy_training_pipeline(tenant_id, AGENT_TYPE)

    time.sleep(VERIFICATION_INTERVAL)
