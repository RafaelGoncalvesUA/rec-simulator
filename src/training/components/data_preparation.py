from kfp import dsl
from kfp.dsl import Input, Output, Artifact


@dsl.component(base_image="rafego16/pipeline-custom-image-train:latest")
def data_preparation(agent_type: str, microgrid_template_id: int, dataset_dir: Input[Artifact], env: Output[Artifact]):
    import os
    import pickle as pkl
    from agent.sb3_agent import SB3Agent
    from microgrid_template import get_microgrid_template, microgrid_from_template

    template = get_microgrid_template(microgrid_template_id)
    _, microgrid_env = microgrid_from_template(template)

    agent_path = os.path.join(dataset_dir.path, 'agent.zip')
    if os.path.exists(agent_path):
        agent = SB3Agent.load(agent_type, agent_path, microgrid_env)
    else:
        agent = SB3Agent(agent_type, microgrid_env)

    with open(os.path.join(env.path, 'env.pkl'), 'wb') as f:
        pkl.dump(microgrid_env, f)
    print(f'Microgrid environment saved to {env.path}/env.pkl')

    agent.save(os.path.join(env.path, 'agent.zip'))
    print(f'Agent saved to {env.path}/agent.pkl')
