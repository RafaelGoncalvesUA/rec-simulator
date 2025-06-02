import pandas as pd
import numpy as np
import os

from pymgrid.Environments.pymgrid_cspla import MicroGridEnv as CsDaMicroGridEnv
from pymgrid.Environments.pymgrid_csca import SafeExpMicrogridEnv

import ray
from ray import tune
from ray.tune.schedulers import PopulationBasedTraining

import plotly.express as px
import plotly.graph_objects as go
import time


def create_env(microgrid, split, continuous=False):
    microgrid.train_test_split(train_size=split)

    if continuous:
        return SafeExpMicrogridEnv(microgrid)
    
    return CsDaMicroGridEnv({'microgrid': microgrid,
                                'forecast_args': None,
                                'resampling_on_reset': False,
                                'baseline_sampling_args': None})


def train(env, config, extra_args={"learning_rate": 5e-4, "batch_size": 32}):
    base_class, agent_type = config["agent"]
    env.reset(testing=False)
    
    agent = base_class(
        agent_type,
        env,
        policy={"activation_fn": config["policy_act"], "net_arch": config["policy_net_arch"]},
        extra_args=extra_args,
    )

    agent.learn(total_timesteps=config["train_steps"])
    return agent


def test(env, agent, log_id=-1):
    obs = env.reset(testing=True)
    costs = []

    while not env.done:
        action, _ = agent.predict(obs, deterministic=True)
        obs, reward, _, _ = env.step(action)
        costs.append(-reward)

    results_df = pd.DataFrame(costs, columns=["costs"])
    
    if log_id != -1:
        os.makedirs("logs", exist_ok=True)
        results_dir = f"./logs/config_{log_id}.csv"
        results_df.to_csv(results_dir)

    env.close()
    
    return results_df["costs"].sum()


def fit_agent(env, config, log_id, extra_args={}):
    agent = train(env, config, extra_args)
    total_cost = test(env, agent, log_id)

    if log_id ==-1:
        tune.report({"cost": total_cost})
        return

    return agent, total_cost


def tune_agent(env, config, log_id, trials):
    ray.init(ignore_reinit_error=True)

    pbt = PopulationBasedTraining(
        time_attr="training_iteration",
        metric="cost",
        mode="min",
        perturbation_interval=1,
        hyperparam_mutations={
            "learning_rate": tune.uniform(1e-4, 1e-2),
            "batch_size": [32, 64, 128, 256],
        }
    )

    analysis = tune.run(
        lambda x: fit_agent(env, config, -1, extra_args=x),
        config={
            "learning_rate": tune.uniform(1e-4, 1e-2),
            "batch_size": tune.choice([32, 64, 128, 256]),
        },
        num_samples=trials,
        scheduler=pbt,
        verbose=0,
    )

    # Fit the best agent
    best_trial = analysis.get_best_trial("cost", "min", "last")
    agent, min_cost = fit_agent(env, config, log_id, extra_args=best_trial.config)
    return agent, min_cost, analysis.dataframe()


def run_simulation(config, log_id=0, tune=False, trials=-1):
    assert set(config.keys()) == {
        "microgrid",
        "agent",
        "policy_act",
        "policy_net_arch",
        "learning_rate",
        "batch_size",
        "train_steps",
        "train_test_split",
    }

    microgrid = config["microgrid"]
    env = create_env(microgrid, split=config["train_test_split"])

    

    # if tune:
    #     return tune_agent(env, config, log_id, trials)
                      
    extra_args = {"learning_rate": config["learning_rate"], "batch_size": config["batch_size"]}
    return fit_agent(env, config, log_id, extra_args)


def plot_results(config_files, labels):
    fig = go.Figure()
    
    for d, label in zip(config_files, labels):
        data = np.cumsum(pd.read_csv(f"./logs/{d}.csv")['costs'])
        fig.add_trace(go.Scatter(y=data, mode='lines', name=label))
    
    # Layout
    fig.update_layout(
        title='Cumulative Operational Cost',
        xaxis_title='Step',
        yaxis_title='Cost ($)',
        font=dict(size=15),
        template='plotly_white',
        showlegend=True,
    )

    # add empty scatter first to avoid writing problems
    empty = px.scatter(x=[0], y=[0])
    empty.write_image("cumulative_cost.pdf", format="pdf")
    time.sleep(1)
    fig.write_image("cumulative_cost.pdf", format="pdf")
