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


@dsl.pipeline
def agent_pipeline(agent_id: int, agent_type: str, template_id: int):
    ingested_data = data_ingestion(agent_id=agent_id)

    prepared_data = data_preparation(
        template_id=template_id,
        dataset_dir=ingested_data.outputs["dataset_dir"]
    )
    
    trained_agent = agent_routine(agent_type=agent_type, env=prepared_data.outputs["env"])

    agent_storing(agent_id=agent_id, agent_type=agent_type, agent=trained_agent.outputs["agent"])


if TEST: agent_pipeline(agent_id=0, template_id=0)
else: compiler.Compiler().compile(agent_pipeline, "pipeline.yaml")
