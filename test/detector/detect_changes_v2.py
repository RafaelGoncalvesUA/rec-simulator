import pymgrid
import sys
from river import drift
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from time import sleep

sys.path.append("../../src")

import utils.custom_simulator.microgrid_generator as mgen
from utils.custom_simulator.concrete_env import CustomEnv

generator = mgen.MicrogridGenerator(nb_microgrid=25, random_seed=42, path=pymgrid.__path__[0])
generator.generate_microgrid()
microgrids = generator.microgrids

samples = []
n_microgrids = 10
ctr = 0

while len(samples) < n_microgrids:
    template = microgrids[ctr]
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
    fig2 = go.Figure()
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

            if adwin.drift_detected:
                drift_detected.append(ctr-1)
                break

    observations_df = pd.DataFrame(observations, columns=info.keys())
    return observations_df, drift_detected

# Run both simulations
obs_df, drift_1e_7 = simulate_drift(1e-7)
_, drift_1e_2 = simulate_drift(1e-2)  # Use same obs_df since env reset inside simulate_drift

subplot_titles = ["Load (MWh)", "PV Generation (MWh)"]

fig = make_subplots(
    rows=2, cols=1,
    shared_yaxes=True,
    subplot_titles=subplot_titles,
    vertical_spacing=0.3
)

for annotation in fig['layout']['annotations']:
    annotation['font'] = dict(size=19)

# Plot observations for first two variables with original colors but no legend
for i, col in enumerate(obs_df.columns[:2]):
    fig.add_trace(
        go.Scatter(
            x=obs_df.index,
            y=obs_df[col],
            name=col,
            showlegend=False  # hide legend for these lines
        ),
        row=i + 1, col=1,
    )

# Add drift detection vertical lines for delta=1e-7 (blue)
for drift_x in drift_1e_7:
    fig.add_vline(
        x=drift_x-45,
        line_width=2,
        line_dash="dash",
        line_color="blue",
    )

# Add drift detection vertical lines for delta=1e-2 (red)
for drift_x in drift_1e_2:
    fig.add_vline(
        x=drift_x-45,
        line_width=2,
        line_dash="dash",
        line_color="red",
    )

fig.update_xaxes(title_text="Timesteps", row=2, col=1)

# Add legend entries for drift lines only
fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines',
                         line=dict(color='blue', dash='dash'),
                         name='δ=1e-7'), row=1, col=1)
fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines',
                         line=dict(color='red', dash='dash'),
                         name='δ=1e-2'), row=1, col=1)

fig.update_layout(
    font=dict(size=17),
    width=1000,
    height=450,
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=20, r=20, t=50, b=20),
)

# Save figure
fname = "combined_drift_detection.pdf"
load_math_js(fname)
fig.write_image(fname)