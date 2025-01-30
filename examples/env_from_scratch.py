import numpy as np
from pymgrid import Microgrid
from pymgrid.modules import GensetModule, BatteryModule, LoadModule, RenewableModule


genset = GensetModule(running_min_production=0,
                      running_max_production=50,
                      genset_cost=0.5)

battery = BatteryModule(min_capacity=0,
                        max_capacity=100,
                        max_charge=50,
                        max_discharge=50,
                        efficiency=1.0,
                        init_soc=0.5)

# Using random data
renewable = RenewableModule(time_series=50*np.random.rand(100))

load = LoadModule(time_series=60*np.random.rand(100))

microgrid = Microgrid([genset, battery, ("pv", renewable), load])

for j in range(10):
    action = microgrid.sample_action(strict_bound=False)
    microgrid.step(action)

microgrid.get_log(drop_singleton_key=True).to_csv('log.csv')