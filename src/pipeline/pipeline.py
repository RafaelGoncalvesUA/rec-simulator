from kfp import local
from kfp import dsl
from kfp import compiler
from pathlib import Path

PROJECT_PATH = Path(__file__).parent.parent

# local.init(runner=local.DockerRunner())

# retrieve data from minio
@dsl.component
def data_ingestion(batch_file: str):
    return "test"

# @dsl.component
# def data_preparation():
#     # returns a training environment
#     pass

# @dsl.component
# def agent_routine():
#     # agent = Agent("ppo", env, total_timesteps=100)
#     pass

@dsl.pipeline
def agent_pipeline(batch_file: str):
    ingestion_task = data_ingestion(batch_file=batch_file)
    return ingestion_task

# local:
# res = agent_pipeline()

# compile:
compiler.Compiler().compile(agent_pipeline, "pipeline.yaml")
