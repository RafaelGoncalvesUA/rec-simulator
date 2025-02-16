import argparse
import os
from pymgrid import Microgrid
from pymgrid.modules import BatteryModule, LoadModule, RenewableModule, GridModule
import yaml
import pickle
import pandas as pd

parser = argparse.ArgumentParser(description='Load a dataset', formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument('-d', '--dataset', type=str, help='Path to dataset root', required=True)
parser.add_argument('-b', '--battery', type=str, help='Path to battery settings (.yaml)', required=True)
parser.add_argument('-c', '--config', type=str, help='Path to create the environment', required=True)
parser.add_argument('-m', '--microgrid', type=str, help='Path to save the microgrid (.yaml)', required=True)

msg = '''
The dataset should have the following structure:
dataset/
├── GridModule/
│   └── grid.csv
├── LoadModule/           # Multiple load files are allowed
│   ├── load[...].csv
│   ├── load[...].csv
│   └── ...
└── RenewableModule/      # Multiple renewable files are allowed
    ├── pv[...].csv
    ├── wind[...].csv
    └── ...
'''

parser.epilog = msg
args = parser.parse_args()

grid = None
loads = []
renewables = []

config = yaml.safe_load(open(args.config, 'r'))

for module in ['grid', 'loads', 'renewables']:
    if os.path.exists(os.path.join(args.dataset, module)):
        if module == 'grid':
            filename = os.listdir(os.path.join(args.dataset, module))[0]
            ts = pd.read_csv(os.path.join(args.dataset, module, filename), index_col=0)

            grid = GridModule(
                max_export=config['max_export'],
                max_import=config['max_import'],
                time_series=ts,
            )

        elif module in {'loads', 'renewables'}:
            for filename in os.listdir(os.path.join(args.dataset, module)):
                ts = pd.read_csv(os.path.join(args.dataset, module, filename), index_col=0)

                if module == 'loads':
                    loads.append(
                        LoadModule(time_series=ts)
                    )

                elif module == 'renewables':
                    src_type = filename.split('_')[0]

                    renewables.append(
                        (src_type, RenewableModule(time_series=ts))
                    )
    else:
        print(f'{module} directory not found. Exiting...')
        exit(1)


batteries = [
    BatteryModule(**b)
    for b in yaml.safe_load(open(args.battery, 'r')).values()
]

microgrid = Microgrid([*batteries, *renewables, *loads, grid])

os.makedirs(args.microgrid, exist_ok=True)
pickle.dump(microgrid, open(os.path.join(args.microgrid, 'env.pkl'), 'wb'))
microgrid.dump(open(os.path.join(args.microgrid, 'env.yaml'), 'w'))

print(f'Microgrid saved to {args.microgrid}')
