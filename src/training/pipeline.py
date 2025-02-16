from kfp import local
from kfp import dsl
from kfp.dsl import Output, Artifact, Input
from kfp import compiler
from pathlib import Path

PROJECT_PATH = Path(__file__).parent.parent

local.init(runner=local.DockerRunner())


# retrieve data from minio
@dsl.component(
    base_image="registry.localhost/pipeline-custom-image:latest",
    packages_to_install=["minio"],
)
def data_ingestion(batch_file: str, output_artifact: Output[Artifact]):
    from minio import Minio
    import pandas as pd
    from dotenv import load_dotenv
    import os

    load_dotenv(dotenv_path="/app/.env")

    minio_client = Minio(
        endpoint=os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=False,
    )

    minio_client.fget_object(os.getenv("MINIO_BUCKET"), batch_file, "batch.json")

    os.makedirs(f"{output_artifact.path}/grid", exist_ok=True)
    os.makedirs(f"{output_artifact.path}/loads", exist_ok=True)
    os.makedirs(f"{output_artifact.path}/renewables", exist_ok=True)

    df = pd.read_json("batch.json")
    df[df["id"] == "grid1"][["g0", "g1", "g2", "g3"]].to_csv(f"{output_artifact.path}/grid/grid.csv")
    df[df["id"] == "load1"]["l0"].to_csv(f"{output_artifact.path}/loads/load1.csv")
    df[df["id"] == "renewable1"]["r0"].to_csv(f"{output_artifact.path}/renewables/renewable1.csv")


# returns a training environment
@dsl.component(base_image="registry.localhost/pipeline-custom-image:latest")
def data_preparation(input_artifact: Input[Artifact], output_artifact: Output[Artifact]):
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
        if os.path.exists(os.path.join(input_artifact.path, module)):
            if module == 'grid':
                filename = os.listdir(os.path.join(input_artifact.path, module))[0]
                ts = pd.read_csv(os.path.join(input_artifact.path, module, filename), index_col=0)

                grid = GridModule(
                    max_export=config['max_export'],
                    max_import=config['max_import'],
                    time_series=ts,
                )

            elif module in {'loads', 'renewables'}:
                for filename in os.listdir(os.path.join(input_artifact.path, module)):
                    ts = pd.read_csv(os.path.join(input_artifact.path, module, filename), index_col=0)

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

    os.makedirs(output_artifact.path, exist_ok=True)
    microgrid.dump(open(os.path.join(output_artifact.path, 'env.yaml'), 'w'))

    print(f'Microgrid saved to {output_artifact.path}')


@dsl.component(
    base_image="registry.localhost/pipeline-custom-image:latest",
    # packages_to_install=["stable-baselines3"]
)
def agent_routine(input_artifact: Input[Artifact]):
    from load_env import load_env_from_dataset

    microgrid = load_env_from_dataset(f"{input_artifact.path}/env.yaml")
    # # agent = Agent("ppo", env, total_timesteps=100)


# TODO: accept battery json and config json
# config file should have the number of grids, loads and renewables
@dsl.pipeline
def agent_pipeline(batch_file: str):
    ingested_data = data_ingestion(batch_file=batch_file)
    prepared_data = data_preparation(input_artifact=ingested_data.outputs["output_artifact"])
    agent_routine(input_artifact=prepared_data.outputs["output_artifact"])
    # return routine.outputs


# local
agent_pipeline(batch_file="batch_20250207171510.json")

# compile
# compiler.Compiler().compile(agent_pipeline, "pipeline.yaml")
