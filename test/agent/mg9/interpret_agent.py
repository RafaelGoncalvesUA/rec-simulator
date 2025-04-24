import sys
import pandas as pd
import pymgrid
sys.path.append("../../../src")

from utils.custom_simulator import microgrid_generator as mgen
from utils.microgrid_template import microgrid_from_template
from utils.custom_simulator.concrete_env import CustomEnv
from logic.agent.sb3_agent import SB3Agent
from torch import nn

from sklearn.tree import DecisionTreeClassifier
from sklearn.tree import export_graphviz
import graphviz
import numpy as np
import pickle as pkl

# ----------------- load agent -----------------
agent = SB3Agent.load("DQN", "worst_mg_agent.zip")

# ----------------- load microgrid env -----------------
with open("microgrid_env.pkl", "rb") as f:
    microgrid_env = pkl.load(f)

# ----------------- run agent -----------------
obs = microgrid_env.reset(testing=True)
cost = 0
X, Y = [], []

np.random.seed(2)

while not microgrid_env.done:
    action, _ = agent.predict(obs, deterministic=False)
    obs, reward, _, info = microgrid_env.step(action)
    cost -= reward

    X.append(obs)
    Y.append(action)

print(f"SB3Agent | Total cost ($): {cost:.4e} ({cost})")

unique_action_idx, counts = np.unique(Y, return_counts=True)
actions_lst = ["charge", "full discharge", "import", "export", "genset", "other_5", "other_6"]
actions_dict = {actions_lst[i]: counts[idx] for idx, i in enumerate(unique_action_idx) if i < len(actions_lst)}
print("Actions:", actions_dict)

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
