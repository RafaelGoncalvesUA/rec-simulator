import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from utils.microgrid_template import microgrid_generator, get_microgrid_template, microgrid_from_template
from agent.random_agent import RandomAgent
import random

random.seed(1234)

class RenewableEnergyCommunity:
    def __init__(self, rec_id, market_type, marginal_price_ts=None):
        self.rec_id = rec_id
        self.microgrids = {}
        self.environments = {}
        self.observations = {}
        self.agents = {}
        self.n_tenants = 0

        if marginal_price_ts is None:
            self.marginal_price_ts = [1.0] * 50

    def reset(self):
        self.current_step = 0
        self.energy_pool = 0
        self.reputation = {tenant_id: 0 for tenant_id in self.agents}

    @property
    def done(self):
        return any(env.done for env in self.environments.values())

    def add_tenant(self, microgrid, env):
        tenant_id = self.n_tenants
        self.microgrids[tenant_id] = microgrid
        self.environments[tenant_id] = env
        self.reputation[tenant_id] = 0
        self.n_tenants += 1
        print("REC {} | Added tenant {}.".format(self.rec_id, tenant_id))

        self.train_agent(tenant_id)
        self.observations[tenant_id] = self.environments[tenant_id].reset(testing=True)

    def remove_tenant(self, tenant_id):
        if tenant_id in self.agents:
            del self.agents[tenant_id]
            del self.environments[tenant_id]
            del self.observations[tenant_id]
            del self.microgrids[tenant_id]
            del self.reputation[tenant_id]
            self.n_tenants -= 1
            print("REC {} | Removed tenant {}.".format(self.rec_id, tenant_id))
        else:
            print("REC {} | Tenant {} not found.".format(self.rec_id, tenant_id))

    def train_agent(self, tenant_id):
        agent = RandomAgent("random", self.environments[tenant_id])
        agent.learn(100000)
        self.agents[tenant_id] = agent

    def negotiate(self, energy_need):
        if energy_need > 0:
            # try to buy energy from the market (may fail)
            self.cost += energy_need * self.price_ts[self.current_step]
            self.energy_pool += energy_need
            print("REC {} | Negotiating to buy energy: {} units.".format(self.rec_id, energy_need))
        elif energy_need < 0:
            # try to sell energy to the market (may fail)
            self.cost -= energy_need * self.price_ts[self.current_step]
            self.energy_pool -= energy_need
            print("REC {} | Negotiating to sell energy: {} units.".format(self.rec_id, -energy_need))

    def retrieve_exchange_actions(self):
        exchanges = []

        for tenant_id in range(self.n_tenants):
            obs = self.observations[tenant_id]
            env = self.environments[tenant_id]
            action, _ = self.agents[tenant_id].predict(obs, env=env)
            print(action, env.action_space)
            control_dict = env.get_action(action)
            print(control_dict)
            break
    
    def step(self):
        exchanges = self.retrieve_exchange_actions()
        print(self.observations)
        exit(0)

        self.cost = 0
        transactions = [0] * self.n_tenants

        # handle energy exports
        for tenant_id, surplus in enumerate(actions):
            if surplus > 0:
                self.energy_pool += surplus
                self.reputation[tenant_id] += surplus * self.price_ts[self.current_step]
                transactions[tenant_id] = surplus
                print("REC {} | Tenant {}: Energy surplus of {} added to pool.".format(self.rec_id, tenant_id, surplus))

        # handle energy imports
        print(actions)
        total_demand = sum(max(0, -action) for action in actions)

        self.negotiate(total_demand - self.energy_pool) # positive if it needs to buy energy
        print(total_demand, self.energy_pool)

        if total_demand <= self.energy_pool:
            print("REC {} | Energy pool is sufficient to meet demand.".format(self.rec_id))
            # full statisfaction of demand
            for tenant_id, demand in enumerate(actions):
                if demand < 0:
                    self.energy_pool -= abs(demand)
                    self.reputation[tenant_id] -= abs(demand) * self.price_ts[self.current_step]
                    transactions[tenant_id] = demand
                    print("REC {} | Tenant {}: Asked for {} units, received {} units.".format(self.rec_id, tenant_id, -demand, abs(demand)))
        else:
            # limited energy, distribute proportionally to credits
            # consider total reputation of all tenants that are requesting energy
            print("REC {} |Energy pool is insufficient to meet demand.".format(self.rec_id))
            total_reputation = sum(self.reputation[i] for i in range(len(actions)) if actions[i] < 0)

            if total_reputation == 0:
                print("REC {} | No reputation available to distribute energy.".format(self.rec_id))
                return self.cost

            for tenant_id, demand in enumerate(actions):
                if demand < 0 and self.reputation[tenant_id] > 0:
                    # calculate the share of energy based on reputation
                    share = (self.reputation[tenant_id] / total_reputation) * self.energy_pool
                    self.energy_pool -= share
                    self.reputation[tenant_id] -= share * self.price_ts[self.current_step]
                    transactions[tenant_id] = share
                    print("REC {} | Tenant {}: Asked for {} units, received {} units.".format(self.rec_id, tenant_id, -demand, share))

        return self.cost


NUM_STEPS = 50
NUM_RECS = 1
NUM_TENANTS = 5
MARKET_TYPE="muda"

_, samples = microgrid_generator()
print("Generated microgrid templates.\n")

recs = []

for rec_id in range(NUM_RECS):
    rec = RenewableEnergyCommunity(rec_id, MARKET_TYPE)
    rec.reset()

    ctr = 0
    while len(rec.microgrids) < NUM_TENANTS:
        template = samples[ctr]

        new_parameters = {
            "last_soc": template._df_record_state["battery_soc"][0],
            "last_capa_to_charge": template._df_record_state["capa_to_charge"][0],
            "last_capa_to_discharge": template._df_record_state["capa_to_discharge"][0],
            "load": template._load_ts["Electricity:Facility [kW](Hourly)"][:NUM_STEPS],
            "pv": template._pv_ts["GH illum (lx)"].tolist()[:NUM_STEPS]
        }

        # has connection to the grid
        if hasattr(template, "_grid_status_ts"):
            co2_iso = "CO2_CISO_I_kwh" if "CO2_CISO_I_kwh" in template._grid_co2.columns else "CO2_DUK_I_kwh"
            grid_co2 = template._grid_co2[co2_iso].tolist()[:NUM_STEPS]
            new_parameters["grid_co2_iso"] = co2_iso
            new_parameters["grid_co2"] = grid_co2

            # grid price will be then set by the REC
            new_parameters["grid_price_import"] = template._grid_price_import[0].tolist()[:NUM_STEPS]
            new_parameters["grid_price_export"] = template._grid_price_export[0].tolist()[:NUM_STEPS]
            new_parameters["grid_ts"] = [1] * NUM_STEPS
        else:
            ctr += 1
            continue

        if ctr != 0:
            for key in {"load", "pv", "grid_co2"}:
                new_lst = new_parameters[key].copy()
                random.shuffle(new_lst)
                new_parameters[key] = new_lst

        print("Using template no. {}...".format(ctr))
        microgrid, env = microgrid_from_template(template, new_parameters)
        
        rec.add_tenant(microgrid, env)
        ctr += 1
        print()

    print()
    recs.append(rec)

while not recs[0].done:
    for rec in recs:
        rec.step()


