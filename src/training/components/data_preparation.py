from kfp import dsl
from kfp.dsl import Input, Output, Artifact


@dsl.component(base_image="rafego16/pipeline-custom-image:latest")
def data_preparation(dataset_dir: Input[Artifact], env: Output[Artifact]):
    from pymgrid import Microgrid
    from pymgrid.modules import BatteryModule, LoadModule, RenewableModule, GridModule
    import yaml
    import pandas as pd
    import os

    grid = None
    loads = []
    renewables = []

    config = yaml.safe_load(open("config.yaml", 'r'))

    # TODO: support multiple grids
    for module in ['grid', 'loads', 'renewables']:
        if os.path.exists(os.path.join(dataset_dir.path, module)):
            if module == 'grid':
                filename = os.listdir(os.path.join(dataset_dir.path, module))[0]
                ts = pd.read_csv(os.path.join(dataset_dir.path, module, filename), index_col=0)

                grid = GridModule(
                    max_export=config['max_export'],
                    max_import=config['max_import'],
                    time_series=ts,
                )

            elif module in {'loads', 'renewables'}:
                for filename in os.listdir(os.path.join(dataset_dir.path, module)):
                    ts = pd.read_csv(os.path.join(dataset_dir.path, module, filename), index_col=0)

                    if module == 'loads':
                        loads.append(
                            LoadModule(time_series=ts)
                        )

                    elif module == 'renewables':
                        src_type = filename.split('_')[0]

                        renewables.append(
                            (src_type, RenewableModule(time_series=ts))
                        )
        else:
            print(f'{module} directory not found. Exiting...')
            exit(1)


    batteries = [
        BatteryModule(**b)
        for b in yaml.safe_load(open("battery.yaml", 'r')).values()
    ]

    microgrid = Microgrid([*batteries, *renewables, *loads, grid])

    os.makedirs(env.path, exist_ok=True)
    microgrid.dump(open(os.path.join(env.path, 'env.yaml'), 'w'))

    print(f'Microgrid saved to {env.path}')