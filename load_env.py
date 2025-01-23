import yaml
from pymgrid import PROJECT_PATH

yaml_file = PROJECT_PATH / 'data/scenario/pymgrid25/microgrid_0/microgrid_0.yaml'
microgrid = yaml.safe_load(yaml_file.open('r'))

for j in range(10):
    action = microgrid.sample_action(strict_bound=True)
    microgrid.step(action)

microgrid.get_log(drop_singleton_key=True).to_csv('log.csv')