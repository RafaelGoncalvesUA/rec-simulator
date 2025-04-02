import time
from dotenv import load_dotenv
from pymgrid import MicrogridGenerator as mgen
from pymgrid.Environments.pymgrid_cspla import MicroGridEnv as CsDaMicroGridEnv
from db import init_db
import os
import requests

load_dotenv(dotenv_path="/app/.env")

USER = os.getenv("DATABASE_USER")
PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE = os.getenv("DATABASE_NAME")
HOST = os.getenv("DATABASE_HOST")
PORT = os.getenv("DATABASE_PORT")
SERVICE_BASE_URL= os.getenv("SERVICE_BASE_URL")
MAX_OBS_SIZE = int(os.getenv("MAX_OBS_SIZE"))
AGENT_TYPE = os.getenv("AGENT_TYPE")

print("Creating microgrids...")
generator = mgen.MicrogridGenerator(nb_microgrid=10)
generator.generate_microgrid()
microgrids = generator.microgrids

samples_ = [microgrids[9]] + microgrids[1:5] + [microgrids[6]]
samples = [
    CsDaMicroGridEnv({'microgrid': microgrid,
                    'forecast_args': None,
                    'resampling_on_reset': False,
                    'baseline_sampling_args': None})
    for microgrid in [samples_[4]]
    # TODO: change to [microgrids[9]] + microgrids[1:5] + [microgrids[6]]
]

conn, cursor = init_db(DATABASE, USER, PASSWORD, HOST, PORT, MAX_OBS_SIZE)
obs = {}
# actions = set()


def produce_microgrid(tenant_id, env):
    if tenant_id not in obs:
        print(f"Microgrid {tenant_id} has started")
        obs[tenant_id] = env.reset()

    if env.done:
        env.close()
        print(f"Microgrid {tenant_id} has finished")
        return

    # save the current obs in db
    obs_def = f"INSERT INTO microgrid_data (tenant_id, "
    obs_def += ", ".join([f"obs_{i}" for i in range(MAX_OBS_SIZE)])
    obs_def += ") VALUES (%s, "
    obs_def += ", ".join(["%s" for _ in range(MAX_OBS_SIZE)])
    obs_def += ");"

    obs_values = [tenant_id] + \
    [obs[tenant_id][i] if i < len(obs[tenant_id]) else None for i in range(MAX_OBS_SIZE)]

    cursor.execute(obs_def, obs_values)
    conn.commit()

    # POST to get the action
    body = {
        "agent_id": tenant_id,
        "agent_type": AGENT_TYPE,
        "records": [obs[tenant_id].tolist()]
    }
    response = requests.post(f"{SERVICE_BASE_URL}/models/my-agent:predict", json=body).json()

    if "action" not in response:
        print(f"There is no action available for microgrid {tenant_id}") 
        return

    action = response["action"][0]
    obs[tenant_id], reward, _, _ = env.step(action)

    # if action not in actions:
    #     actions.add(action)
    #     print(f"(NEW) Microgrid {tenant_id} has taken action {action}")


ctr = 1
done_microgrid = 0

for i, microgrid in enumerate(samples[:1]): # TODO: change to samples
    init_body = {
        "agent_id": i,
        "agent_type": AGENT_TYPE,
        "load": True
    }
    response = requests.post(f"{SERVICE_BASE_URL}/models/my-agent:predict", json=init_body).json()
print("Loaded all agents.")

while True:
    for i, microgrid in enumerate(samples[:1]): # TODO: change to samples
        produce_microgrid(i, microgrid)

    time.sleep(0.1)

    if ctr % 100 == 0:
        print(f"Executed {ctr} iterations")
        time.sleep(5)

    ctr += 1
