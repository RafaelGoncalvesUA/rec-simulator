import yaml
from pathlib import Path
import pymgrid

PROJECT_PATH = Path(__file__).parent.parent

def load_env_from_dataset(path_str):
    print(f"Loading environment from {path_str}...") 
    yaml_file = PROJECT_PATH / path_str
    microgrid = yaml.safe_load(yaml_file.open('r'))
    print(f"Environment loaded.")
    return microgrid
