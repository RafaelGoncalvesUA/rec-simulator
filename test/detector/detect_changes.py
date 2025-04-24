import pymgrid
import sys
from river import drift
import pandas as pd
import plotly.graph_objects as go
from plotly import express as px
from plotly.subplots import make_subplots
from time import sleep

sys.path.append("../../src")

import utils.custom_simulator.microgrid_generator as mgen
from utils.custom_simulator.concrete_env import CustomEnv

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

mg = samples[0]

microgrid_env = CustomEnv({'microgrid': mg,
                        'forecast_args': None,
                        'resampling_on_reset': False,
                        'baseline_sampling_args': None},
                        price_forecasts_file='../../src/forecasting/price_forecasts.csv',
                    )

def load_math_js(name):
    # create random figure
    fig2 = px.scatter(x=[0, 1], y=[0, 1])
    fig2.write_image(name)
    sleep(1)

def simulate_drift(delta):
    obs = microgrid_env.reset()

    detectors = [
        drift.ADWIN(delta=delta) for _ in range(len(obs))
    ]

    ctr = 0
    drift_start = 1000
    observations = []
    drift_detected = []

    for _ in range(3000):
        action = microgrid_env.action_space.sample()
        obs, reward, done, info = microgrid_env.step(action)
        
        # generate drift
        if ctr >= drift_start:
            obs = [val + 1 for val in obs[:2]]

        observations.append(obs)
        ctr += 1

        # detect drift
        for i, val in enumerate(obs[:2]):
            adwin = detectors[i]
            key = list(info.keys())[i]
            adwin.update(val)

            found = False

            if adwin.drift_detected:
                print(f"Change detected at index {ctr-1} for {key}, input value: {val}")
                drift_detected.append(ctr-1)
                found = True

            if found:
                break

    observations_df = pd.DataFrame(observations, columns=info.keys())

    # show in the same figure of plotly all the variables
    subplot_titles = list(info.keys())[:2]
    fig = make_subplots(
        rows=2, cols=1,
        shared_yaxes=True,
        subplot_titles=subplot_titles,  # Use the variable names here
        vertical_spacing=0.3  # Reduce the distance between subplots
    )

    for i, col in enumerate(subplot_titles):
        fig.add_trace(
            go.Scatter(
                x=observations_df.index,  # Use the DataFrame index as the x-axis (Time)
                y=observations_df[col],
                name=col,
            ),
            row=i + 1, col=1,
        )

    fig.update_xaxes(title_text="Time", row=2, col=1)  # Add x-axis label

    # add vertical lines for the drift
    print(drift_detected)
    for drift_x in drift_detected:
        fig.add_vline(x=drift_x, line_width=2, line_dash="dash", line_color="red")

    fig.update_layout(
        width=1000,
        height=450,
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
    )

    fname = f"drift_delta{delta}.pdf"

    load_math_js(fname)
    fig.write_image(fname)

simulate_drift(1e-7)
simulate_drift(1e-2)