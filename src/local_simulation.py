from utils.env_loader import load_from_dataset
from utils.microgrid_env import CustomMicrogridEnv

from agent.sb3_agent import SB3Agent
from agent.random_agent import RandomAgent
from torch import nn

import os
import json
from itertools import product
from tqdm import tqdm

import warnings

warnings.filterwarnings("ignore")
  

# ----------------- simulation function -----------------
def run_simulation(config):
    microgrid = load_from_dataset(
        "data",
        config["microgrid_config"],
        config["battery"],
        idx={
            "grids": config["microgrid"]["grid"],
            "loads": config["microgrid"]["loads"],
            "renewables": config["microgrid"]["renewables"],
        },
    )

    env = CustomMicrogridEnv.from_microgrid(microgrid)
    agent_cls, agent_type = config["agent"]
    policy = {"activation_fn": config["policy_act"], "net_arch": config["policy_net_arch"]}

    agent = agent_cls(agent_type, env, policy, verbose=0)
    agent.learn(total_timesteps=config["train_episodes"])

    obs = env.reset()
    done = False
    total_reward = 0

    custom_rewards = []

    print("Running simulation...")
    for _ in tqdm(range(config["test_steps"]), desc="Steps"):
        action, _ = agent.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        custom_rewards.append(reward)
        total_reward += reward

    return env, microgrid, total_reward, custom_rewards, agent

# ----------------- config space -----------------
# load microgrid samples
with open("data/microgrid_samples.json", "r") as f:
    samples = json.load(f)

config_space = {
    # env config
    "microgrid": samples,
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
        nn.Tanh
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

    "train_episodes": [1],
    "test_steps": [1],
}

vals = [
    val for val in [dict(zip(config_space.keys(), val)) for val in product(*config_space.values())]
    
    # no need to variate the policy_act and policy_net_arch for RandomAgent
    if val["agent"][0] != RandomAgent or \
    (val["policy_act"] == config_space["policy_act"][0] and val["policy_net_arch"] == config_space["policy_net_arch"][0])
]

print(f"Starting benchmark with {len(vals)} configurations...")

# ----------------- main benchmark loop -----------------
results = {}
best_performers = set()
best_reward = -float("inf")

for i, config in enumerate(vals):
    print(f"====== Configuration {i + 1}/{len(vals)} ======")
    print(config)

    env, microgrid, total_reward, custom_rewards, agent = run_simulation(config)

    df = env.get_log(drop_singleton_key=True, as_frame=True)
    df["custom_reward"] = custom_rewards
    df.to_csv(f"logs/log_{i}.csv")

    if total_reward >= best_reward:
        best_performers.add(i)
        best_reward = total_reward
        agent.save("agent.zip")

    print(f"Total reward: {total_reward:.2f}\n")

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
