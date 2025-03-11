import random
import os
import json

AVAILABLE_MICROGRIDS = len(os.listdir("grid")) # 76
NUM_MICROGRIDS = 15


def generate_microgrid_samples(num_microgrids, force_group_size=None, seed=42):
    random.seed(seed)
    microgrids = list(range(1, num_microgrids + 1))
    random.shuffle(microgrids)

    groups = []
    while microgrids:
        group_size = (
            force_group_size
            if force_group_size
            else random.randint(1, min(3, len(microgrids)))
        )
        groups.append(microgrids[:group_size])
        microgrids = microgrids[group_size:]

    return groups


grids = generate_microgrid_samples(AVAILABLE_MICROGRIDS, force_group_size=1, seed=1)[:NUM_MICROGRIDS]
loads = generate_microgrid_samples(AVAILABLE_MICROGRIDS, seed=2)[:NUM_MICROGRIDS]
renewables = generate_microgrid_samples(AVAILABLE_MICROGRIDS, seed=3)[:NUM_MICROGRIDS]

split = [{"grid": grids[i], "loads": loads[i], "renewables": renewables[i]} for i in range(NUM_MICROGRIDS)]

# save
with open("microgrid_samples.json", "w") as f:
    json.dump(split, f)

# load
with open("microgrid_samples.json", "r") as f:
    split = json.load(f)
print(split)