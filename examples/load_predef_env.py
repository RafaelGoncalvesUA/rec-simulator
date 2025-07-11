import yaml
from pathlib import Path
import pymgrid

PROJECT_PATH = Path(__file__).parent

yaml_file = PROJECT_PATH / 'microgrid_0/microgrid_0.yaml'
print(yaml_file)
microgrid = yaml.safe_load(yaml_file.open('r'))

for j in range(10):
    action = microgrid.sample_action(strict_bound=True)
    microgrid.step(action)

microgrid.get_log(drop_singleton_key=True).to_csv('log.csv')
