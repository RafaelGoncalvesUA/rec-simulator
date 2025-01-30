from stable_baselines3 import PPO

def ppo_agent(env, total_timesteps):
    print(f"Training PPO agent for {total_timesteps} timesteps...")
    agent = PPO("MlpPolicy", env, verbose=2)
    agent.learn(total_timesteps)
    print("Training completed.")
    return agent
