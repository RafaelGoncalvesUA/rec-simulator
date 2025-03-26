from agent.sb3_agent import SB3Agent
from agent.random_agent import RandomAgent
from utils.simulation import run_simulation
from torch import nn

import os
import pandas as pd
from itertools import product

from pymgrid import MicrogridGenerator as mgen

import warnings

warnings.filterwarnings("ignore")

os.system("rm -rf logs")
os.system("rm -rf agent/models")
os.system("rm agent.zip")

# ----------------- config space -----------------
generator = mgen.MicrogridGenerator(nb_microgrid=10)
generator.generate_microgrid()
microgrids = generator.microgrids

samples = [microgrids[9]] + microgrids[1:5] + [microgrids[6]]

config_space = {
    "microgrid": [samples[0]],
    
    "agent": [
        (SB3Agent, "DQN"),
        # (SB3Agent, "A2C"),
        # (SB3Agent, "PPO"),
        (RandomAgent, None),
    ],
    "policy_act": [
        nn.ReLU,
        # nn.Tanh,
    ],
    "policy_net_arch": [
        # [32, 32],   # narrower
        [64, 64],   # default
        # [128, 128], # wider
    ],
    "learning_rate": [5e-4],
    "batch_size": [32],

    "train_steps": [100000],
    "train_test_split": [0.7],
}

vals = [
    val for val in [dict(zip(config_space.keys(), val)) for val in product(*config_space.values())]
    
    # no need to variate the policy_act and policy_net_arch for RandomAgent / IdleAgent
    if val["agent"][0] not in {RandomAgent} or \
    (val["policy_act"] == config_space["policy_act"][0] and val["policy_net_arch"] == config_space["policy_net_arch"][0])
]

print(f"Starting benchmark with {len(vals)} configurations...")

# ----------------- config serialisation -----------------
def serialise_config(config):
    return {
        "microgrid": config["microgrid"],
        "agent": f"{config['agent'][0].__name__} {config['agent'][1]}",
        "policy_act": config["policy_act"].__name__,
        "policy_net_arch": config["policy_net_arch"],
        "train_steps": config["train_steps"],
        "train_test_split": config["train_test_split"],
    }

# ----------------- main benchmark loop -----------------
best_performers = set()
lowest_cost = float("inf")

for i, config in enumerate(vals):
    print(f"====== Configuration {i + 1}/{len(vals)} ======")
    print(config)

    agent, total_cost = run_simulation(config, i)

    agent_log = pd.DataFrame([{
        "config_id": i,
        "total_cost": total_cost,
        "total_cost_format": f'{total_cost:.4e}',
        **serialise_config(config),
    }])

    agent_log.to_csv(f"logs/benchmark_log.csv", index=False, mode="a", header=not os.path.exists("logs/benchmark_log.csv"))

    if total_cost <= lowest_cost:
        best_performers.add(i)
        lowest_cost = total_cost
        agent.save("agent.zip")

    print(f"Total cost: {total_cost:.4e}")

# ----------------- print best performers -----------------
print("\n====== Best performer(s) ======")
for idx in best_performers:
    print("--->", vals[idx])
print(f"Lowest cost: {lowest_cost:.4e}")

# ----------------- try to load and run best performer -----------------
print("\n====== Running best performer for best config ======")
best_config = vals[best_performers.pop()]
base_class, agent_type = best_config["agent"]
agent = base_class.load(agent_type, "agent.zip")
run_simulation(best_config) # to ensure that it runs properly
