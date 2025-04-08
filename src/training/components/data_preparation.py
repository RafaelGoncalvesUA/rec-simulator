from kfp import dsl
from kfp.dsl import Input, Output, Artifact


@dsl.component(base_image="rafego16/pipeline-custom-image-train:latest")
def data_preparation(agent_type: str, template_id: int, dataset_dir: Input[Artifact], env: Output[Artifact]):
    import os
    import pickle as pkl
    import pandas as pd
    from logic.agent.sb3_agent import SB3Agent
    from microgrid_template import get_microgrid_template, microgrid_from_template

    template = get_microgrid_template(template_id)

    records = pd.read_csv(os.path.join(dataset_dir.path, 'batch.csv'))
    n_records = records.shape[0]

    new_parameters = {
        "load": records["obs_0"].tolist(),
        "pv": records["obs_1"].tolist(),
        "last_soc": records["obs_2"].tolist()[-1],
        "last_capa_to_charge": records["obs_3"].tolist()[-1],
        "last_capa_to_discharge": records["obs_4"].tolist()[-1],
        "grid_ts": records["obs_5"].tolist(),
        "grid_co2": records["obs_6"].tolist(),
        "grid_price_import": records["obs_7"].tolist(),
        "grid_price_export": records["obs_8"].tolist(),
    }

    _, microgrid_env = microgrid_from_template(template, new_parameters)

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
