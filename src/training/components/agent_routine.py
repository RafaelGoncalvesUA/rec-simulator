from kfp import dsl
from kfp.dsl import Input, Output, Artifact, Model


@dsl.component(base_image="rafego16/pipeline-custom-image-train:latest")
def agent_routine(agent_type: str, env: Input[Artifact], agent: Output[Model]):
    from logic.agent.sb3_agent import SB3Agent
    import pickle as pkl
    import os

    microgrid_env = pkl.load(open(os.path.join(env.path, 'env.pkl'), 'rb'))
    agent_model = SB3Agent(agent_type, microgrid_env, extra_args={"learning_rate": 5e-4})

    agent_model.learn(total_timesteps=100000)
    agent_model.save(os.path.join(agent.path, 'agent.zip'))
