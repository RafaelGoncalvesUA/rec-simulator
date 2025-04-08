from kfp import dsl
from kfp.dsl import Output, Artifact


@dsl.component(base_image="rafego16/pipeline-custom-image:latest")
def data_ingestion(agent_id: int, dataset_dir: Output[Artifact]):
    import pandas as pd
    from dotenv import load_dotenv
    import os
    from minio import Minio
    from db import get_db_conn

    load_dotenv(dotenv_path="/app/.env")

    conn, cursor = get_db_conn(
        database=os.getenv("DATABASE_NAME"),
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD"),
        host=os.getenv("DATABASE_HOST"),
        port=os.getenv("DATABASE_PORT"),
        max_obs_size=os.getenv("MAX_OBS_SIZE"),
    )

    os.makedirs(dataset_dir.path, exist_ok=True)

    # retrieve all accumulated records from the database # TODO: uncomment this
    # cursor.execute(f"SELECT * FROM microgrid_data WHERE tenant_id = '{agent_id}'")
    # records = pd.DataFrame(
    #     cursor.fetchall(), columns=[desc[0] for desc in cursor.description]
    # )
    # records = records.drop(columns=["timestamp", "tenant_id"])

    # simulate retrieval from database
    values = [tuple(0.1 for _ in range(11)) for _ in range(100)]
    records = pd.DataFrame(values, columns=[f"obs_{i}" for i in range(11)])

    records.to_csv(f"{dataset_dir.path}/batch.csv", index=False)

    # delete the accumulated records from the database
    # cursor.execute(f"DELETE FROM microgrid_data WHERE tenant_id = '{agent_id}'")
    # conn.commit()
    print("Retrieved records from the database")

    # load previous agent (if it exists)
    minio_client = Minio(
        endpoint=os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=False,
    )

    if minio_client.bucket_exists(os.getenv("MINIO_BUCKET")):
        objects = minio_client.list_objects(
            os.getenv("MINIO_BUCKET"), prefix=f"agent_{agent_id}.zip"
        )
        if len(objects) > 0:
            minio_client.fget_object(
                os.getenv("MINIO_BUCKET"),
                objects[0].object_name,
                f"{dataset_dir.path}/agent.zip",
            )
            print("Retrieved agent from Minio")
        else:
            print("No agent found in Minio, a new instance will be created")
