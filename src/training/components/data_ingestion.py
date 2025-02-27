from kfp import dsl
from kfp.dsl import Output, Artifact


@dsl.component(
    base_image="rafego16/pipeline-custom-image:latest",
    packages_to_install=["minio"],
)
def data_ingestion(batch_file: str, dataset_dir: Output[Artifact]):
    from minio import Minio
    import pandas as pd
    from dotenv import load_dotenv
    import os

    load_dotenv(dotenv_path="/app/.env")

    minio_client = Minio(
        endpoint=os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=False,
    )

    # retrieve batch file from MinIO's specified bucket
    minio_client.fget_object(os.getenv("MINIO_BUCKET"), batch_file, "batch.json")

    os.makedirs(f"{dataset_dir.path}/grid", exist_ok=True)
    os.makedirs(f"{dataset_dir.path}/loads", exist_ok=True)
    os.makedirs(f"{dataset_dir.path}/renewables", exist_ok=True)

    df = pd.read_json("batch.json")
    ids = df["id"].unique()

    for module in ids:
        if module.startswith("grid"):
            df[df["id"] == module][["g0", "g1", "g2", "g3"]].to_csv(
                f"{dataset_dir.path}/grid/{module}.csv"
            )
        elif module.startswith("load"):
            df[df["id"] == module]["l0"].to_csv(
                f"{dataset_dir.path}/loads/{module}.csv"
            )
        elif module.startswith("renewable"):
            df[df["id"] == module]["r0"].to_csv(
                f"{dataset_dir.path}/renewables/{module}.csv"
            )

