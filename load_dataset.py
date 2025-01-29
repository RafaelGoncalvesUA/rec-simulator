import argparse
import os
from pymgrid import Microgrid
from pymgrid.modules import BatteryModule, LoadModule, RenewableModule
import yaml

parser = argparse.ArgumentParser(description='Load a dataset')
parser.add_argument('-d', '--dataset', type=str, help='Path to dataset root', required=True)
parser.add_argument('-b', '--battery', type=str, help='Path to battery yaml file', required=True)
parser.add_argument('-m', '--microgrid', type=str, help='Path to save the microgrid yaml file', required=True)

args = parser.parse_args()

for module in ['GridModule', 'LoadModule', 'RenewableModule']:
    if os.path.exists(os.path.join(args.dataset, module)):
        pass

    else:
        print(f'{module} not found. Exiting...')
        exit(1)


batteries = [
    BatteryModule(**b)
    for b in yaml.safe_load(open(args.battery, 'r')).values()
]

# microgrid = Microgrid([*batteries, *renewables, *loads, grid])