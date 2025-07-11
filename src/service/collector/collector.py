from kfp_client_manager import KFPClientManager
from db import get_db_conn
from dotenv import load_dotenv
import os
import time
from datetime import datetime, timedelta

# ANSI escape codes for colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Load environment variables
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

# Database connection
conn, cursor = get_db_conn(DATABASE, USER, PASSWORD, HOST, PORT, MAX_OBS_SIZE)

# Deploy training pipeline
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
            "template_id": tenant_id,
        },
    )

# Trigger condition
def trigger(cursor, tenant_id, cond):
    if cond == "buffer_size":
        cursor.execute(f"SELECT COUNT(*) FROM microgrid_data WHERE tenant_id = '{tenant_id}'")
        count = cursor.fetchone()[0]
        return count >= MAX_BUFFER_SIZE
    else:
        raise ValueError(f"Condition {cond} not available")

# Simulated time loop
BASE_DATE = datetime.strptime("2025-07-14 15:17:19", "%Y-%m-%d %H:%M:%S")
ctr = 0

while True:
    simulated_time = BASE_DATE + timedelta(seconds=ctr * VERIFICATION_INTERVAL)
    print(f"{Colors.HEADER}--- Iteration at {simulated_time.strftime('%Y-%m-%d %H:%M:%S')} ---{Colors.ENDC}")

    cursor.execute("SELECT DISTINCT tenant_id FROM microgrid_data")
    tenants = cursor.fetchall()

    for tenant in tenants:
        tenant_id = int(tenant[0])
        print(f"{Colors.OKCYAN}Tenant {tenant_id}: Verifying condition '{TRIGGER_COND}'...{Colors.ENDC}")

        try:
            if trigger(cursor, tenant_id, TRIGGER_COND):
                print(f"{Colors.WARNING}Tenant {tenant_id}: Condition '{TRIGGER_COND}' met.{Colors.ENDC}")
                print(f"{Colors.OKGREEN}Tenant {tenant_id}: Deploying training pipeline.{Colors.ENDC}")
                deploy_training_pipeline(tenant_id, AGENT_TYPE)
            else:
                print(f"{Colors.OKBLUE}Tenant {tenant_id}: No action needed.{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Tenant {tenant_id}: Error occurred - {e}{Colors.ENDC}")

    ctr += 1
    print()
    time.sleep(VERIFICATION_INTERVAL)
