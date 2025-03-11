from utils.env_loader import load_from_dataset
from utils.microgrid_env import CustomMicrogridEnv
import pandas as pd
import numpy as np
from tqdm import tqdm

def eval_iteration(config, agent, test, steps, i=None, reward_hist=None):
    if isinstance(test, CustomMicrogridEnv):
        test_env = test
    else:
        test_microgrid = load_from_dataset(
            "data",
            config["microgrid_config"],
            config["battery"],
            idx={
                "grids": test["grid"],
                "loads": test["loads"],
                "renewables": test["renewables"],
            },
        )
        test_env = CustomMicrogridEnv.from_microgrid(test_microgrid)

    obs = test_env.reset()
    iter_reward_hist = []

    for s in tqdm(range(steps), desc="Steps"):
        action, _ = agent.predict(obs, deterministic=True)
        obs, reward, _, _ = test_env.step(action)

        if reward_hist is None:
            iter_reward_hist.append(reward)
            continue

        reward_hist[s, i] = reward

    return iter_reward_hist if reward_hist is None else reward_hist 


def run_simulation(config):
    # check if config has all the necessary keys
    assert set(config.keys()) == {
        "microgrid",
        "test_set",
        "battery",
        "microgrid_config",
        "agent",
        "policy_act",
        "policy_net_arch",
        "train_steps",
        "test_steps",
    }

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
    agent.learn(total_timesteps=config["train_steps"])

    test_set = config["test_set"]
    train_steps = config["train_steps"]
    test_steps = config["test_steps"]

    reward_hist = np.zeros((test_steps, len(test_set)))

    print("---Evaluation on training microgrid---")
    train_reward = sum(eval_iteration(config, agent, env, train_steps))
    print(f"Total reward (train): {train_reward:.2f}")

    for i, test in enumerate(test_set):
        print(f"---Running simulation for test microgrid {i + 1}/{len(test_set)}---")
        reward_hist = eval_iteration(config, agent, test, test_steps, i, reward_hist)

    reward_hist = reward_hist.sum(axis=0)
    total_reward = reward_hist.mean()
    reward_hist = np.append(reward_hist, [total_reward, train_reward])

    columns = [f"reward_test{microgrid_id}" for microgrid_id in range(len(test_set))] + ["avg_test_reward", "train_reward"]
    reward_hist = pd.DataFrame(reward_hist.reshape(1, -1), columns=columns)

    return env, microgrid, total_reward, reward_hist, agent
