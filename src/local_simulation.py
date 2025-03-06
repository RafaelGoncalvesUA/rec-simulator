from utils.env_loader import load_from_dataset, env_loader_from_yaml
from utils.microgrid_env import CustomMicrogridEnv
from agent.sb3_agent import SB3Agent
import random
import os
from itertools import product
from tqdm import tqdm

import warnings

warnings.filterwarnings("ignore")
  

def run_simulation(config):
    microgrid = load_from_dataset(
        "data",
        config["microgrid_config"],
        config["battery"],
        idx={
            "grids": config["grids"],
            "loads": config["loads"],
            "renewables": config["renewables"],
        },
    )

    env = CustomMicrogridEnv.from_microgrid(microgrid)

    agent = SB3Agent(config["agent"], env, config["policy"], verbose=0)
    agent.learn(total_timesteps=config["train_episodes"])

    obs = env.reset()
    done = False
    total_reward = 0

    custom_rewards = []

    print("Running simulation...")
    for _ in tqdm(range(config["test_steps"]), desc="Steps"):
        action, _ = agent.predict(obs, deterministic=True)
        # action = env.action_space.sample()
        obs, reward, done, info = env.step(action)
        custom_rewards.append(reward)
        total_reward += reward

    print(env.state_dict(normalized=False))
    print(env.state_dict(normalized=True))

    return env, microgrid, total_reward, custom_rewards, agent


AVAILABLE_MICROGRIDS = len(os.listdir("data/grid")) # 76


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


NUM_MICROGRIDS = 1

config_space = {
    # env config
    "grids": generate_microgrid_samples(AVAILABLE_MICROGRIDS, force_group_size=1, seed=1)[:NUM_MICROGRIDS],
    "loads": generate_microgrid_samples(AVAILABLE_MICROGRIDS, seed=2)[:NUM_MICROGRIDS],
    "renewables": generate_microgrid_samples(AVAILABLE_MICROGRIDS, seed=3)[:NUM_MICROGRIDS],
    "battery": ["examples/dataset/battery.yaml"],
    "microgrid_config": ["examples/dataset/config.yaml"],
    
    # agent config
    "agent": ["PPO"],
    "policy": ["custom_policy1"],
    "train_episodes": [1],
    "test_steps": [1],
}

vals = [dict(zip(config_space.keys(), val)) for val in product(*config_space.values())]
print("Starting benchmark...")


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
agent = SB3Agent.load(best_config["agent"], "agent.zip")
run_simulation(best_config)