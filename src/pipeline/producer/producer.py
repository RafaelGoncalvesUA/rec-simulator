from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import NoBrokersAvailable, TopicAlreadyExistsError
from kafka import KafkaProducer
import json
import pandas as pd
import time
import os
from dotenv import load_dotenv

load_dotenv()

for i in range(int(os.getenv("MAX_CONNECTION_ATTEMPTS"))):
    try:
        print("Connecting to Kafka...")
        admin_client = KafkaAdminClient(
            bootstrap_servers=os.getenv("KAFKA_SERVER"),
            client_id="test",
        )
        print("Connected to Kafka")
        break
    except NoBrokersAvailable:
        print("No brokers available. Retrying...")
        time.sleep(5)
        continue

try:
    topic = NewTopic(name=os.getenv("KAFKA_TOPIC", "test"), num_partitions=1, replication_factor=1)
    admin_client.create_topics(new_topics=[topic], validate_only=False)
except TopicAlreadyExistsError:
    print("Topic already exists")

print("Loading data...")
base_path = os.getenv("DATA_BASE_PATH", "")
grid1 = pd.read_csv(f"{base_path}grid/grid1.csv.gz", compression="gzip", index_col=0)
grid1.columns = [f"g{col}" for col in grid1.columns]

load1 = pd.read_csv(f"{base_path}load/load1.csv.gz", compression="gzip", index_col=0)
load1.columns = [f"l{col}" for col in load1.columns]

renewable1 = pd.read_csv(
    f"{base_path}renewable/renewable1.csv.gz", compression="gzip", index_col=0
)
renewable1.columns = [f"r{col}" for col in renewable1.columns]

print("Data loaded successfully")

kafka_producer_object = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_SERVER"),
    value_serializer=lambda x: json.dumps(x).encode("utf-8"),
)

# produce messages to Kafka
ctr = 0
for i in range(grid1.shape[0]):
    print(f"{ctr} | Message sent")

    for asset, _id in [(grid1, "grid1"), (load1, "load1"), (renewable1, "renewable1")]:
        sample = asset.iloc[i].to_dict()
        # send asset variable name
        sample["id"] = _id
        kafka_producer_object.send(os.getenv("KAFKA_TOPIC"), sample)

    ctr += 1

    time.sleep(3)

    if ctr % 1000 == 0:
        print(f"Sent {ctr} messages")
        time.sleep(200)
