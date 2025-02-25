from kfp import dsl
from kfp.dsl import Input, Output, Artifact, Model


@dsl.component(base_image="rafego16/pipeline-custom-image-train:latest")
def agent_routine(env: Input[Artifact], agent: Output[Model]):
    from load_env import load_env_from_dataset
    from custom_env import MicrogridEnv, api_price_function
    import joblib
    from pathlib import Path
    from stable_baselines3 import PPO

    microgrid = load_env_from_dataset(f"{env.path}/env.yaml")
    environment = MicrogridEnv(microgrid, api_price_function)

    total_timesteps = 1000
    print(f"Training PPO agent for {total_timesteps} timesteps...")
    agent = PPO("MlpPolicy", environment, verbose=2)
    agent.learn(total_timesteps)
    print("Training completed.")

    output_path = Path(agent.path)
    joblib.dump(agent, output_path)
    print(f"Agent saved.")
