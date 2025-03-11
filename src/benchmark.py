from agent.sb3_agent import SB3Agent
from agent.random_agent import RandomAgent
from utils.simulation import run_simulation
from torch import nn

import os
import pandas as pd
import json
from itertools import product

import warnings

warnings.filterwarnings("ignore")

# ----------------- config space -----------------
# load microgrid samples
with open("data/microgrid_samples.json", "r") as f:
    samples = json.load(f)

config_space = {
    # env config
    "microgrid": samples[:-5],
    "test_set": [samples[-5:]], # set of microgrids for testing
    "battery": [f"data/battery/comb/{fname}" for fname in os.listdir('data/battery/comb')],
    "microgrid_config": ["data/config.yaml"],
    
    # agent config
    "agent": [
        (RandomAgent, None),
        (SB3Agent, "PPO"),
        (SB3Agent, "DQN"),
        (SB3Agent, "A2C"),
    ],
    "policy_act": [
        nn.ReLU,
        nn.Tanh,
    ],
    "policy_net_arch": [
        {"pi": [32, 32], "vf": [32, 32]},      # narrow
        {"pi": [64, 64], "vf": [64, 64]},     # default
        # {"pi": [32, 32], "vf": [64, 64]},     # narrow pi (obs to action)
        # {"pi": [64, 64], "vf": [32, 32]},     # narrow vf (obs to value)
        {"pi": [128, 128], "vf": [128, 128]}, # wide
        # {"pi": [128, 128], "vf": [64, 64]},   # wide pi (obs to action)
        # {"pi": [64, 64], "vf": [128, 128]},   # wide vf (obs to value)
    ],

    "train_steps": [8760], # 1 year (hourly intervals)
    "test_steps": [8760 // 4], # 3 months (hourly intervals)
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
    return pd.DataFrame(
        {
            "microgrid": [config["microgrid"]],
            "test_set": [config["test_set"]],
            "battery": [config["battery"]],
            "microgrid_config": [config["microgrid_config"]],
            "agent": [f"{config['agent'][0].__name__} {config['agent'][1]}"],
            "policy_act": [config["policy_act"].__name__],
            "policy_net_arch": [config["policy_net_arch"]],
            "train_steps": [config["train_steps"]],
            "test_steps": [config["test_steps"]],
        }
    )


# ----------------- main benchmark loop -----------------
best_performers = set()
best_reward = -float("inf")

for i, config in enumerate(vals):
    print(f"====== Configuration {i + 1}/{len(vals)} ======")
    print(config)

    env, microgrid, total_reward, reward_hist, agent = run_simulation(config)

    microgrid_log = env.get_log(drop_singleton_key=True, as_frame=True)
    microgrid_log.to_csv(f"logs/microgrid/log_{i}.csv")

    agent_log = pd.concat([serialise_config(config), reward_hist], axis=1)

    agent_log.to_csv(f"logs/agent/log_{i}.csv", index=False)

    if total_reward >= best_reward:
        best_performers.add(i)
        best_reward = total_reward
        agent.save("agent.zip")

    print(f"Avg. total reward (test): {total_reward:.2f}\n")

# ----------------- print best performers -----------------
print("\====== Best performer(s) ======")
for idx in best_performers:
    print("--->", vals[i])
print(f"Best reward: {best_reward:.2f}")


# ----------------- try to load and run best performer -----------------
print("\n====== Running best performer for best config ======")
best_config = vals[best_performers.pop()]
agent_cls, agent_type = best_config["agent"]
agent = agent_cls.load(agent_type, "agent.zip")
run_simulation(best_config)
