from utils.load_env import *
from utils.custom_env import *
from pipeline.agent.ppo import *

TRAIN_ITERATIONS = 100
TEST_ITERATIONS = 1

microgrid = load_env_from_dataset("../example/env_from_dataset/env.yaml")
env = MicrogridEnv(microgrid, api_price_function)

agent = ppo_agent(env, total_timesteps=100)

obs = env.reset()
done = False
total_reward = 0

print("Running simulation...")
for ep in range(TEST_ITERATIONS):
    # action, _ = agent.predict(obs, deterministic=False)
    action = microgrid.get_empty_action()
    obs, reward, done, info = env.step(action)
    print(obs)
    print(f"Episode {ep} | Reward: {reward:.2f}")
    total_reward += reward

print(f"Total reward: {total_reward:.2f}")
save_agent(agent, "ppo_agent")
