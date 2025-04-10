from .base_agent import BaseAgent

class BasicAgent(BaseAgent):
    def __init__(self, base, env, policy=None, extra_args=None):
        if env:
            BasicAgent.env = env # store as class attribute to reuse in new loaded instances

    def learn(self, total_timesteps=1, callback=None):
        print("Skipping learning for BasicAgent...")
        pass

    def predict(self, obs, deterministic=True):
        load, pv, soc, capa_to_charge, capa_to_discharge, g_status, *_ = obs

        if not g_status:
            raise ValueError("Grid not available.")

        net_load = load - pv

        # 1. Excess PV -> try to charge battery
        if net_load < 0:
            if soc < 1.0 and capa_to_charge > 0:
                return 4, None  # Charge battery with PV + grid (Action 4 - grid mode)
            else:
                return 3, None # Export excess

        # 2. Not enough PV -> try to discharge battery
        elif net_load > 0:
            if soc > 0 and capa_to_discharge > 0:
                return 1, None  # Discharge battery (Action 1 - grid/genset mode)

            # 3. Battery empty → use grid
            else:
                return 2, None  # Grid import

        return 0, None

    def save(self, path_str):
        print("Skipping saving for BasicAgent...")
        pass

    def load(base, path_str):
        print("Skipping loading for BasicAgent...")
        return BasicAgent(None, None)
