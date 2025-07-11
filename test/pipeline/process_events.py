import pandas as pd

records = []

with open('events.txt') as f:
    old_pods = 2

    for line in f:
        if "pipeline has" in line:
            parts = line.split()
            timestep = int(parts[0])
            pods = int(parts[-2])

            pipelines = (pods - 2) // 4

            records.append({"timestep": timestep, "pods": pods, "pipelines": pipelines})

df = pd.DataFrame(records)
df.to_csv('events.csv', index=False)