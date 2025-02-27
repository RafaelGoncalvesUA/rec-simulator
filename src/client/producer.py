import pandas as pd
import time
import os
from dotenv import load_dotenv
import requests

load_dotenv()

print("Loading data...")
base_path = os.getenv("DATA_BASE_PATH", "")
grid1 = pd.read_csv(f"{base_path}grid/grid1.csv.gz", compression="gzip", index_col=0)
grid1.columns = [f"g{col}" for col in grid1.columns]

load1 = pd.read_csv(f"{base_path}load/load1.csv.gz", compression="gzip", index_col=0)
load1.columns = [f"l{col}" for col in load1.columns]

renewable1 = pd.read_csv(f"{base_path}renewable/renewable1.csv.gz", compression="gzip", index_col=0)
renewable1.columns = [f"r{col}" for col in renewable1.columns]

print("Data loaded successfully")

# produce messages
ctr = 0
for i in range(grid1.shape[0]):
    print(f"{ctr} | Message sent")

    samples = []

    for asset, _id in [(grid1, "grid1"), (load1, "load1"), (renewable1, "renewable1")]:
        sample = asset.iloc[i].to_dict()
        sample["id"] = _id
        samples.append(sample)

    # make a post request to the server
    response = requests.post(
        os.getenv("SERVICE_BASE_URL") + "/v1/models/my-agent:predict",
        json=samples,
    )

    ctr += 1

    time.sleep(3)

    if ctr % 1000 == 0:
        print(f"Sent {ctr} messages")
        time.sleep(200)
