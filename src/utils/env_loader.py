import yaml
from pathlib import Path
import pymgrid

import os
import pandas as pd
from pymgrid import Microgrid
from pymgrid.modules import BatteryModule, LoadModule, RenewableModule, GridModule

PROJECT_PATH = Path(__file__).parent.parent

def load_from_dataset(dataset_dir, config_path, battery_path, idx=None, extension=".csv.gz"):
    config = yaml.safe_load(open(config_path, 'r'))
    
    grids = []
    loads = []
    renewables = []

    for module in ['grids', 'loads', 'renewables']:
        modules = os.listdir(os.path.join(dataset_dir, module[:-1]))
        
        if idx:
            modules = [f"{module[:-1]}{i}{extension}" for i in idx[module]]

        for filename in modules:
            ts = pd.read_csv(os.path.join(dataset_dir, module[:-1], filename), index_col=0)

            if module == 'grids':
                grids.append(
                    pymgrid.modules.GridModule(
                        max_export=config['max_export'],
                        max_import=config['max_import'],
                        time_series=ts,
                    )
                )

            elif module == 'loads':
                loads.append(
                    pymgrid.modules.LoadModule(time_series=ts)
                )

            elif module == 'renewables':
                src_type = filename.split('_')[0]

                renewables.append(
                    (src_type, pymgrid.modules.RenewableModule(time_series=ts))
                )
        
    batteries = [
        BatteryModule(**b)
        for b in yaml.safe_load(open(battery_path, 'r')).values()
    ]

    return Microgrid([*batteries, *renewables, *loads, *grids])

def env_loader_from_yaml(path_str):
    print(f"Loading environment from {path_str}...") 
    yaml_file = PROJECT_PATH / path_str
    microgrid = yaml.safe_load(yaml_file.open('r'))
    print(f"Environment loaded.")
    return microgrid