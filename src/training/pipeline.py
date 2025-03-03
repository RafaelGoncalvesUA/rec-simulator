from kfp import dsl
from components.data_ingestion import data_ingestion
from components.data_preparation import data_preparation
from components.agent_routine import agent_routine
from components.agent_storing import agent_storing

TEST = False

if TEST:
    from kfp import local
    local.init(runner=local.DockerRunner())
else:
    from kfp import compiler

# TODO: accept battery json and config json
# TODO: config file should have the number of grids, loads and renewables
# TODO: dsl.ParallelFor (hyperparameter tuning)
@dsl.pipeline
def agent_pipeline(agent_id: int, batch_file: str):
    ingested_data = data_ingestion(batch_file=batch_file)
    prepared_data = data_preparation(dataset_dir=ingested_data.outputs["dataset_dir"])
    trained_agent = agent_routine(env=prepared_data.outputs["env"])
    agent_storing(agent=trained_agent.outputs["agent"], agent_id=agent_id)


if TEST: agent_pipeline(batch_file="batch_20250207171510.json")
else: compiler.Compiler().compile(agent_pipeline, "pipeline.yaml")
