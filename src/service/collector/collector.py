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

conn, cursor = get_db_conn(DATABASE, USER, PASSWORD, HOST, PORT, MAX_OBS_SIZE)


def deploy_training_pipeline(tenant_id):
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
            "tenant_id": tenant_id,
        },
    )


# verfify for all available tenants if one has surpassed the buffer size
while True:
    cursor.execute("SELECT tenant_id FROM microgrid_data")
    tenants = cursor.fetchall()

    for tenant in tenants:
        tenant_id = int(tenant[0])
        print(f"Verifying tenant {tenant_id}")

        cursor.execute(
            f"SELECT COUNT(*) FROM microgrid_data WHERE tenant_id = '{tenant_id}'"
        )
        count = cursor.fetchone()[0]

        if count >= MAX_BUFFER_SIZE:
            print(f"Deploying training pipeline for tenant {tenant_id}")
            deploy_training_pipeline(tenant_id)

    time.sleep(VERIFICATION_INTERVAL)
