from logic.agent.random_agent import RandomAgent


class RenewableEnergyCommunity:
    def __init__(self, rec_id, market, marginal_price_ts=None):
        self.rec_id = rec_id
        self.cost = 0
        self.baseline_cost = 0
        self.microgrids = {}
        self.environments = {}
        self.observations = {}
        self.agents = {}
        self.individual_costs = {}
        self.n_tenants = 0

        self.logs = []

        if marginal_price_ts is None:
            self.marginal_price_ts = [1.0] * 50

    def reset(self):
        self.current_step = 0
        self.energy_pool = 0
        self.reputation = {tenant_id: 0 for tenant_id in self.agents}
        self.individual_costs = {tenant_id: 0 for tenant_id in self.agents}

    @property
    def done(self):
        return any(env.done for env in self.environments.values())

    def add_tenant(self, microgrid, env):
        tenant_id = self.n_tenants
        self.microgrids[tenant_id] = microgrid
        self.environments[tenant_id] = env
        self.reputation[tenant_id] = 0
        self.individual_costs[tenant_id] = 0
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
            del self.individual_costs[tenant_id]
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
            self.energy_pool += energy_need
            print("REC {} | Negotiating to buy energy: {} units.".format(self.rec_id, energy_need))
            return energy_need * self.marginal_price_ts[self.current_step]

        elif energy_need < 0:
            # try to sell energy to the market (may fail)
            self.energy_pool -= energy_need
            print("REC {} | Negotiating to sell energy: {} units.".format(self.rec_id, -energy_need))
            return -energy_need * self.marginal_price_ts[self.current_step]
        
        return 0

    def retrieve_exchange_actions(self):
        exchanges = []
        controls = []

        for tenant_id in range(self.n_tenants):
            obs = self.observations[tenant_id]
            env = self.environments[tenant_id]
            
            action, _ = self.agents[tenant_id].predict(obs, env=env)
            
            control_dict = env.get_action(action)
            controls.append(control_dict)
            exchanges.append(control_dict["grid_export"] - control_dict["grid_import"])

        return controls, exchanges
    
    def log_step(self, step_cost, step_demand):
        self.logs.append({
            "step": self.current_step,
            "total_demand": step_demand,
            "energy_pool": self.energy_pool,
            "cost": step_cost,
            "accumulated_cost": self.cost,
            "accumulated_baseline_cost": self.baseline_cost,
            **{f"tenant_{i}_cost": self.individual_costs[i] for i in range(self.n_tenants)},
        })
    
    def execute_transactions(self, controls, transactions):
        for tenant_id in range(self.n_tenants):
            env = self.environments[tenant_id]
            control_dict = controls[tenant_id]
            transaction = transactions[tenant_id]

            if transaction > 0:
                control_dict["grid_export"] = transaction
                control_dict["grid_import"] = 0

            elif transaction < 0:
                control_dict["grid_export"] = 0
                control_dict["grid_import"] = abs(transaction)

            obs, reward, _, _ = env.run_step(control_dict)
            print("REC {} | Tenant {}: Executed action with individual cost {}.".format(self.rec_id, tenant_id, -reward))
            self.observations[tenant_id] = obs
            self.individual_costs[tenant_id] -= reward

    def step(self):
        controls, actions = self.retrieve_exchange_actions()
        transactions = [0] * self.n_tenants

        # handle energy exports
        for tenant_id, surplus in enumerate(actions):
            if surplus > 0:
                self.energy_pool += surplus
                self.reputation[tenant_id] += surplus * self.marginal_price_ts[self.current_step]
                transactions[tenant_id] = surplus
                print("REC {} | Tenant {}: Energy surplus of {} added to pool.".format(self.rec_id, tenant_id, surplus))

        # handle energy imports
        total_demand = sum(max(0, -action) for action in actions)
        self.baseline_cost += total_demand * self.marginal_price_ts[self.current_step]

        step_cost = self.negotiate(total_demand - self.energy_pool) # positive if it needs to buy energy

        if total_demand <= self.energy_pool:
            print("REC {} | Energy pool is sufficient to meet demand.".format(self.rec_id))
            # full statisfaction of demand
            for tenant_id, demand in enumerate(actions):
                if demand < 0:
                    self.energy_pool -= abs(demand)
                    self.reputation[tenant_id] -= abs(demand) * self.marginal_price_ts[self.current_step]
                    transactions[tenant_id] = demand
                    print("REC {} | Tenant {}: Asked for {} units, received {} units.".format(self.rec_id, tenant_id, -demand, abs(demand)))
        else:
            # limited energy, distribute proportionally to credits
            # consider total reputation of all tenants that are requesting energy
            print("REC {} |Energy pool is insufficient to meet demand.".format(self.rec_id))
            total_reputation = sum(self.reputation[i] for i in range(len(actions)) if actions[i] < 0)

            if total_reputation == 0:
                print("REC {} | No reputation available to distribute energy.".format(self.rec_id))
                self.cost += step_cost
                self.log_step(step_cost, total_demand)
                return

            for tenant_id, demand in enumerate(actions):
                if demand < 0 and self.reputation[tenant_id] > 0:
                    # calculate the share of energy based on reputation
                    share = (self.reputation[tenant_id] / total_reputation) * self.energy_pool
                    self.energy_pool -= share
                    self.reputation[tenant_id] -= share * self.marginal_price_ts[self.current_step]
                    transactions[tenant_id] = share
                    print("REC {} | Tenant {}: Asked for {} units, received {} units.".format(self.rec_id, tenant_id, -demand, share))

        self.execute_transactions(controls, transactions)
        self.current_step += 1

        self.cost += step_cost
        self.log_step(step_cost, total_demand)