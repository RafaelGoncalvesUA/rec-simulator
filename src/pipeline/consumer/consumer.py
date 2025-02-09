from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from minio import Minio
import json
import time
import os
from dotenv import load_dotenv
from datetime import datetime
from kfp_client_manager import KFPClientManager

load_dotenv()

print("Connecting to MinIO...")
minio_client = Minio(
    endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    secure=False,
)

minio_bucket = os.getenv("MINIO_BUCKET", "kafka-data")

if not minio_client.bucket_exists(minio_bucket):
    minio_client.make_bucket(minio_bucket)
    print(f"Bucket '{minio_bucket}' created.")

print("Connected to MinIO.")

# Connect to Kafka
for i in range(int(os.getenv("MAX_CONNECTION_ATTEMPTS", 20))):
    try:
        print("Connecting to Kafka...")
        consumer = KafkaConsumer(
            os.getenv("KAFKA_TOPIC", "test"),
            bootstrap_servers=os.getenv("KAFKA_SERVER", "localhost:9092"),
            auto_offset_reset="earliest",  # Start reading at the earliest message
            enable_auto_commit=True,       # Commit offsets automatically
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            group_id=None
        )
        print("Connected to Kafka")
        break
    except NoBrokersAvailable:
        print("No brokers available. Retrying...")
        time.sleep(5)
        continue

else:
    print("Max connection attempts reached. Exiting.")
    exit(1)

print("Listening for messages...")

batch = []
batch_size = int(os.getenv("BATCH_SIZE", 10))

try:
    while True:
        messages = consumer.poll(timeout_ms=int(os.getenv("POLL_TIMEOUT", 10)) * 1000)

        for _, records in messages.items():
            batch.extend(records)

        if len(batch) >= batch_size:
            print(f"Processing batch of {len(batch)} messages...")

            # Convert batch to JSON
            batch_data = [msg.value for msg in batch]
            batch_json = json.dumps(batch_data, indent=2)

            # Create a unique filename
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"batch_{timestamp}.json"
            file_path = f"/tmp/{filename}"

            # Save JSON to a file
            with open(file_path, "w") as f:
                f.write(batch_json)

            # Upload to MinIO
            minio_client.fput_object(minio_bucket, filename, file_path)
            print(f"Uploaded {filename} to MinIO bucket '{minio_bucket}'.")

            # Delete local file after upload
            os.remove(file_path)

            # Clear batch
            batch.clear()

            kfp_client_manager = KFPClientManager(
                api_url="http://localhost:8080/pipeline",

                dex_username="user@example.com",
                dex_password="12341234",

                skip_tls_verify=True,
                dex_auth_type="local",
            )

            kfp_client = kfp_client_manager.create_kfp_client()

            run = kfp_client.create_run_from_pipeline_package(
                pipeline_file='../pipeline.yaml',
                namespace='kubeflow-user-example-com',
                arguments={
                    'batch_file': filename,
                },
            )


except KeyboardInterrupt:
    print("Consumer stopped.")

finally:
    consumer.close()
    print("Kafka consumer closed.")
