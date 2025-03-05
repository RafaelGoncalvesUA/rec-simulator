from kfp import dsl
from kfp.dsl import Input, Output, Artifact


@dsl.component(base_image="rafego16/pipeline-custom-image:latest")
def data_preparation(dataset_dir: Input[Artifact], env: Output[Artifact]):
    import os
    from env_loader import load_from_dataset

    microgrid = load_from_dataset(dataset_dir.path, 'config.yaml', 'battery.yaml')

    os.makedirs(env.path, exist_ok=True)
    microgrid.dump(open(os.path.join(env.path, 'env.yaml'), 'w'))

    print(f'Microgrid saved to {env.path}')
