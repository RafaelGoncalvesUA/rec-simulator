from kfp import dsl
from kfp.dsl import Input, Output, Artifact, Model


@dsl.component(base_image="rafego16/pipeline-custom-image-train:latest")
def agent_routine(env: Input[Artifact], agent: Output[Model]):
    from load_env import load_env_from_dataset
    from custom_env import MicrogridEnv, api_price_function
    from sb3_agent import SB3Agent
    import joblib
    from pathlib import Path

    microgrid = load_env_from_dataset(f"{env.path}/env.yaml")
    environment = MicrogridEnv(microgrid, api_price_function)

    agent = SB3Agent("PPO", environment)
    agent.learn(environment)
    agent.save(f"{agent.path}")
