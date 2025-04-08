from kfp import dsl
from kfp.dsl import Input, Output, Artifact, Model


@dsl.component(base_image="rafego16/pipeline-custom-image-train:latest")
def agent_routine(agent_type: str, env: Input[Artifact], agent: Output[Model]):
    from logic.agent.sb3_agent import SB3Agent
    import pickle as pkl
    import os

    microgrid_env = pkl.load(open(os.path.join(env.path, 'env.pkl'), 'rb'))
    agent = SB3Agent.load(agent_type, os.path.join(env.path, 'agent.zip'), microgrid_env)

    agent.learn(total_timesteps=os.getenv("TRAIN_STEPS"))
    agent.save(os.path.join(agent.path, 'agent.zip'))
