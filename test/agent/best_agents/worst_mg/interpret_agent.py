import sys
import pandas as pd
import pymgrid
sys.path.append("../../../../src")

from utils.custom_simulator import microgrid_generator as mgen
from utils.microgrid_template import microgrid_from_template
from utils.custom_simulator.concrete_env import CustomEnv
from logic.agent.sb3_agent import SB3Agent
from logic.agent.heuristics_agent import BasicAgent
from torch import nn

from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import export_graphviz
import graphviz
import numpy as np
import pickle as pkl
from collections import Counter

# ----------------- load agent -----------------
agent = SB3Agent.load("DQN", "worst_mg_agent.zip")

# # ----------------- load microgrid env -----------------
# with open("microgrid_env.pkl", "rb") as f:
#     microgrid_env = pkl.load(f)

n_template = 9

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

marginal_price_ts = pd.read_csv("../../../../src/forecasting/price.csv")
marginal_price_ts["PRICE"] = marginal_price_ts["PRICE"] / 1000 # convert to kWh

template = samples[n_template]
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

microgrid, _ = microgrid_from_template(template, new_setting, horizon=24, timestep=1, return_new_env=False)

microgrid_env = CustomEnv({
    'microgrid': microgrid,
    'forecast_args': None,
    'resampling_on_reset': False,
    'baseline_sampling_args': None},
    predictors,
    n_lags=24,
    forecast_steps=[1, 8, 12],
    price_forecasts_file="../../../../src/forecasting/price_forecasts.csv",
)


# agent = BasicAgent("heuristics", microgrid_env)

# ----------------- run agent -----------------
obs = microgrid_env.reset(testing=True)
cost = 0
X, Y = [], []

success_controls = []
actions_lst = ["charge", "discharge", "import", "export", "genset", "charge/import | export", "discharge | genset"]

np.random.seed(2)

def check_action(actual_act, env, action, append=False):
    control_dict = env.get_action(action)
    action_name = "charge" if action == 0 else "discharge" if action == 1\
    else "import" if action == 2 else "export" if action == 3\
    else "genset" if action == 4 else "charge/import | export" if action == 5\
    else "discharge | genset"

    for type_act in ["battery_discharge", "battery_charge", "grid_import", "grid_export", "genset"]:
        if control_dict[type_act] > 0:
            actual_act += f"{type_act}|"

    actual_act = actual_act[:-1]

    if append:
        if actual_act == "":
            actual_act = "idle"

        success_controls.append(f"{action_name} ---> {actual_act}")

    return actual_act

a_ctr = 0
while not microgrid_env.done:
    action, _ = agent.predict(obs, deterministic=False)

    actual_act = ""

    acual_act = check_action(actual_act, microgrid_env, action)
    obs, reward, _, info = microgrid_env.step(action)
    check_action(actual_act, microgrid_env, action, append=True)

    cost -= reward

    X.append(obs)
    Y.append(action)

print(f"SB3Agent | Total cost ($): {cost:.4e} ({cost})")

count_dict = dict(Counter(success_controls))
for k, v in count_dict.items():
    if v > 0:
        print(f"{k}: {v}")

print(sum(count_dict.values()))
print(a_ctr)

unique_action_idx, counts = np.unique(Y, return_counts=True)
actions_dict = {actions_lst[i]: counts[idx] for idx, i in enumerate(unique_action_idx) if i < len(actions_lst)}
print("Actions:", actions_dict)

exit(0)

# ----------------- model_interpretability -----------------
clf = DecisionTreeClassifier(max_depth=20, min_samples_split=8)
clf.fit(X, Y)

def tree_policy(state):
    return clf.predict([state])[0]

obs = microgrid_env.reset(testing=True)
cost = 0
new_X, new_Y = [], []

while not microgrid_env.done:
    action = tree_policy(obs)
    obs, reward, _, info = microgrid_env.step(action)
    cost -= reward
    new_X.append(obs)
    new_Y.append(action)

print(f"DecisionTreeClassifier | Total cost ($): {cost:.4e} ({cost})")

action_counts = {}
unique_action_idx, counts = np.unique(new_Y, return_counts=True)
unique_action_idx = unique_action_idx.tolist()
actions_lst = ["charge", "full discharge", "import", "export", "genset", "other_5", "other_6"]

for a in actions_lst:
    action_idx =  actions_lst.index(a)

    if action_idx in unique_action_idx:
        idx = unique_action_idx.index(action_idx)
        action_counts[a] = counts[idx]
    else:
        action_counts[a] = 0

print("Actions:", action_counts)

dot_data = export_graphviz(
    clf,
    feature_names=list(info.keys()) + ["yhat1", "yhat8", "yhat12"],
    class_names=list(action_counts.keys()),
    filled=True,
    rounded=True,
    max_depth=2,
)
graph = graphviz.Source(dot_data)
graph.render("decision_tree", format="png", cleanup=True)
