from utils.kfp_client_manager import KFPClientManager

kfp_client_manager = KFPClientManager(
    api_url="http://localhost:8080/pipeline",

    dex_username="user@example.com",
    dex_password="12341234",

    skip_tls_verify=True,
    dex_auth_type="local",
)

kfp_client = kfp_client_manager.create_kfp_client()

run = kfp_client.create_run_from_pipeline_package(
    pipeline_file='training/pipeline.yaml',
    namespace='kubeflow-user-example-com',
    arguments={
        'agent_id': 0,
        "agent_type": "PPO",
        'template_id': 0,
    },
)

# run: python -m training.deploy