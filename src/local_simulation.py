from utils.load_env import *
from utils.custom_env import *
from agent.sb3_agent import SB3Agent

TRAIN_ITERATIONS = 100
TEST_ITERATIONS = 1

microgrid = load_env_from_dataset("../example/env_from_dataset/env.yaml")
env = MicrogridEnv(microgrid, api_price_function)

agent = SB3Agent("PPO", env)
agent.learn(env, total_timesteps=TRAIN_ITERATIONS)

obs = env.reset()
done = False
total_reward = 0

print("Running simulation...")
for ep in range(TEST_ITERATIONS):
    # action, _ = agent.predict(obs, deterministic=False)
    action = [0]
    obs, reward, done, info = env.step(action)
    print(f"Episode {ep} | Reward: {reward:.2f}")
    total_reward += reward

print(f"Total reward: {total_reward:.2f}")
agent.save("agent.zip")