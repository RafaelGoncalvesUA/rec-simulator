from stable_baselines3 import PPO


def ppo_agent(env, total_timesteps):
    print(f"Training PPO agent for {total_timesteps} timesteps...")
    agent = PPO("MlpPolicy", env, verbose=2)
    agent.learn(total_timesteps)
    print("Training completed.")
    return agent


def save_agent(agent, path_str):
    import joblib
    from pathlib import Path

    path = Path(path_str)
    joblib.dump(agent, path)
    print(f"Agent saved to {path_str}.")


def load_agent(path_str):
    import joblib
    from pathlib import Path

    path = Path(path_str)
    agent = joblib.load(path)
    print(f"Agent loaded from {path_str}.")
    return agent
