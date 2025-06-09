from logic.agent.sb3_agent import SB3Agent
from logic.agent.heuristics_agent import BasicAgent
from utils.microgrid_template import microgrid_from_template
from utils.custom_simulator.concrete_env import CustomEnv
from torch import nn
import pymgrid
import os
import pandas as pd
import numpy as np
from itertools import product
from utils.custom_simulator import microgrid_generator as mgen
import warnings
from dotenv import load_dotenv
from utils.notification import send_pushover_message

warnings.filterwarnings("ignore")
load_dotenv("./my.env")

if os.path.exists("logs"):
    os.system("rm -rf logs")
    os.system("rm -rf logic/agent/models")
    os.system("rm agent.zip")

# ----------------- load data -----------------
generator = mgen.MicrogridGenerator(nb_microgrid=25, random_seed=42, path=pymgrid.__path__[0])
generator.generate_microgrid()
microgrids = generator.microgrids

predictors = {"grid_price_import": "run_24_12_model.np"}

samples = []
n_microgrids = 10
ctr = 0

while len(samples) < n_microgrids:
    template = microgrids[ctr]
    # has connection to the grid
    if hasattr(template, "_grid_status_ts"):
        samples.append(template)
    else:
        ctr += 1
        continue

    ctr += 1

marginal_price_ts = pd.read_csv("forecasting/price.csv")
marginal_price_ts["PRICE"] = marginal_price_ts["PRICE"] / 1000 # convert to kWh

# ----------------- config space -----------------
config_space = {
    "microgrid": samples,
    
    "agent": [
        (SB3Agent, "DQN"),
        (SB3Agent, "A2C"),
        (SB3Agent, "PPO"),
        (BasicAgent, "heuristics"),
    ],
        
    "policy_act": [
        nn.ReLU,
        nn.Tanh,
    ],
    "policy_net_arch": [
        [64, 64],   # default
        [128, 128], # wider
    ],
    "learning_rate": [1e-4, 5e-4, 1e-3],
    "train_steps": [100000],
}

vals = [
    val for val in [dict(zip(config_space.keys(), val)) for val in product(*config_space.values())]
    
    # no need to variate the policy_act and policy_net_arch for RandomAgent / IdleAgent
    if val["agent"][0] not in {BasicAgent} or \
    (val["policy_act"] == config_space["policy_act"][0] and val["policy_net_arch"] == config_space["policy_net_arch"][0])
]

print(f"Starting benchmark with {len(vals)} configurations...")

# ----------------- config serialisation -----------------
def serialise_config(config):
    return {
        "microgrid": config["microgrid"],
        "agent": f"{config['agent'][0].__name__} {config['agent'][1]}",
        "policy_act": config["policy_act"].__name__,
        "policy_net_arch": config["policy_net_arch"],
        "train_steps": config["train_steps"],
        "learning_rate": config["learning_rate"]
    }

# ----------------- main benchmark loop -----------------
best_performers = set()
lowest_cost = float("inf")

for i, config in enumerate(vals):
    try:
        print(f"====== Configuration {i + 1}/{len(vals)} ======")
        print(config)

        template = config["microgrid"]

        co2_iso = "CO2_CISO_I_kwh" if "CO2_CISO_I_kwh" in template._grid_co2.columns else "CO2_DUK_I_kwh"

        new_setting = {
            "last_soc": template._df_record_state["battery_soc"][0],
            "last_capa_to_charge": template._df_record_state["capa_to_charge"][0],
            "last_capa_to_discharge": template._df_record_state["capa_to_discharge"][0],
            "load": template._load_ts["Electricity:Facility [kW](Hourly)"].tolist(),
            "pv": template._pv_ts["GH illum (lx)"].tolist(),
            "co2_iso": "CO2_CISO_I_kwh",
            "grid_co2_iso": co2_iso,
            "grid_co2": template._grid_co2[co2_iso].tolist(),
            "grid_price_import": marginal_price_ts["PRICE"].tolist(),
            "grid_price_export": marginal_price_ts["PRICE"].tolist(),
            "grid_ts": [1] * template._load_ts.shape[0],
        }

        microgrid, _ = microgrid_from_template(template, new_setting, horizon=24, timestep=1)

        print(microgrid.battery.capacity)
        exit(0)

        microgrid_env = CustomEnv({'microgrid': microgrid,
                                'forecast_args': None,
                                'resampling_on_reset': False,
                                'baseline_sampling_args': None},
                                # predictors,
                                # n_lags=24,
                                # forecast_steps=[1, 8, 12],
                            )
        
        # ------------------ fit agent -----------------
        print("Fitting agent...")
        base_cls, agent_type = config["agent"]
        
        obs = microgrid_env.reset(testing=False)

        agent = base_cls(
            agent_type,
            microgrid_env,
            policy={"activation_fn": config["policy_act"], "net_arch": config["policy_net_arch"]},
            extra_args={"learning_rate": config["learning_rate"]}
        )

        agent.learn(total_timesteps=config["train_steps"])

        # ------------------ test agent -----------------
        print("Testing agent...")
        obs = microgrid_env.reset(testing=True)
        costs = []
        Y = []

        while not microgrid_env.done:
            action, _ = agent.predict(obs, deterministic=True)
            obs, reward, _, _ = microgrid_env.step(action)
            costs.append(-reward)
            Y.append(action)

        # ------------------ save results -----------------

        unique_action_idx, counts = np.unique(Y, return_counts=True)
        actions_lst = ["charge", "full discharge", "import", "export", "genset", "other_5", "other_6"]
        actions_dict = {actions_lst[i]: counts[idx] for idx, i in enumerate(unique_action_idx) if i < len(actions_lst)}

        results_df = pd.DataFrame(costs, columns=["costs"])
        
        os.makedirs("logs", exist_ok=True)
        results_dir = f"./logs/config_{i}.csv"
        results_df.to_csv(results_dir)
        microgrid_env.close()
        
        total_cost = sum(costs)

        agent_log = pd.DataFrame([{
            "config_id": i,
            "total_cost": total_cost,
            "total_cost_format": f'{total_cost:.4e}',
            **serialise_config(config),
            **actions_dict,
        }])

        agent_log.to_csv(f"logs/benchmark_log.csv", index=False, mode="a", header=not os.path.exists("logs/benchmark_log.csv"))

        if total_cost <= lowest_cost:
            best_performers.add(i)
            lowest_cost = total_cost
            agent.save("agent.zip")

        print(f"Total cost: {total_cost:.2e} ({total_cost})")

        if i % 20 == 0:
            send_pushover_message("Benchmark", f"Configuration {i + 1}/{len(vals)}: {total_cost:.2e} ({total_cost})")

    except Exception as e:
        print(f"Error in configuration {i + 1}: {e}")
        send_pushover_message("Benchmark", f"Error in configuration {i + 1}: {e}")
        raise e

send_pushover_message("Benchmark", f"Finished benchmark with {len(vals)} configurations. Best cost: {lowest_cost:.2e} ({lowest_cost})")

# ----------------- print best performers -----------------
print("\n====== Best performer(s) ======")
for idx in best_performers:
    print("--->", vals[idx])
print(f"Lowest cost: {lowest_cost:.2e}")

# ----------------- try to load best performer -----------------
print("\n====== Running best performer for best config ======")
best_config = vals[best_performers.pop()]
base_class, agent_type = best_config["agent"]
agent = base_class.load(agent_type, "agent.zip")
