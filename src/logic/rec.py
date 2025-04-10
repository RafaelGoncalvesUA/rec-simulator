from logic.agent.heuristics_agent import BasicAgent

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

        self.market = market

        self.logs = []

        if marginal_price_ts is None:
            self.marginal_price_ts = [1.0] * 50
        else:
            self.marginal_price_ts = marginal_price_ts["PRICE"].tolist()

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

    def log_step(self):
        absolute_saving = self.baseline_cost - self.cost
        percentage_saving = (absolute_saving / self.baseline_cost) * 100 if self.baseline_cost > 0 else 0

        self.logs.append({
            "step": self.current_step,
            "total_demand": self.total_demand,
            "energy_pool": self.energy_pool,
            "cost": self.step_cost,
            "accumulated_cost": self.cost,
            "accumulated_baseline_cost": self.baseline_cost,
            "absolute_accumulated_saving": absolute_saving,
            "percentage_accumulated_saving": percentage_saving,
            **{f"tenant_{i}_cost": self.individual_costs[i] for i in range(self.n_tenants)},
        })

    def train_agent(self, tenant_id):
        agent = BasicAgent("heuristics", None)
        agent.learn(100000)
        self.agents[tenant_id] = agent

    def negotiate(self, energy_need):
        price = self.marginal_price_ts[self.current_step]
        print("REC {} actions: {}".format(self.rec_id, self.actions))

        if energy_need > 0:
            # Needs to buy energy -> add a demand bid
            self.market.accept_bid(energy_need, price, self.rec_id, True, self.current_step)
            print(f"REC {self.rec_id} wants to buy {energy_need} units.")
        
        elif energy_need < 0:
            # Wants to sell energy -> add a supply offer
            self.market.accept_bid(abs(energy_need), price * 1.1, self.rec_id, False)
            print(f"REC {self.rec_id} wants to sell {abs(energy_need)} units.")

    def retrieve_exchange_actions(self):
        exchanges = []
        controls = []

        for tenant_id in range(self.n_tenants):
            obs = self.observations[tenant_id]
            env = self.environments[tenant_id]
            
            action, _ = self.agents[tenant_id].predict(obs)
            
            control_dict = env.get_action(action)
            controls.append(control_dict)
            exchanges.append(control_dict["grid_export"] - control_dict["grid_import"])

        return controls, exchanges

    def handle_exportations(self):
        self.controls, self.actions = self.retrieve_exchange_actions()
        self.tenant_transactions = [0] * self.n_tenants

        # handle energy exports
        for tenant_id, surplus in enumerate(self.actions):
            if surplus > 0:
                self.energy_pool += surplus
                self.reputation[tenant_id] += surplus * self.marginal_price_ts[self.current_step]
                self.tenant_transactions[tenant_id] = surplus
                print("REC {} | Tenant {}: Energy surplus of {} added to pool.".format(self.rec_id, tenant_id, surplus))

        # handle energy imports
        self.total_demand = sum(max(0, -action) for action in self.actions)
        self.energy_need = self.total_demand - self.energy_pool

        return self.energy_need

    def execute_tenant_transactions(self):
        for tenant_id in range(self.n_tenants):
            env = self.environments[tenant_id]
            control_dict = self.controls[tenant_id]
            transaction = self.tenant_transactions[tenant_id]

            if transaction < 0:
                control_dict["grid_import"] = abs(transaction)
                control_dict["grid_export"] = 0

            elif transaction > 0:
                control_dict["grid_import"] = 0
                control_dict["grid_export"] = transaction

            obs, reward, _, _ = env.run_step(control_dict)
            print("REC {} | Tenant {}: Executed action with individual cost {}.".format(self.rec_id, tenant_id, -reward))
            self.observations[tenant_id] = obs
            self.individual_costs[tenant_id] -= reward
    
    def handle_market_transactions(self, transactions):
        print("REC {} | Handling market transactions.".format(self.rec_id))

        self.baseline_cost += self.total_demand * self.marginal_price_ts[self.current_step]
        rec_transactions = transactions[transactions.bid == self.rec_id]

        # TODO: with a given probability, grid disconnects

        if self.energy_need == 0:
            print("REC {} | No energy needed, no negotation.".format(self.rec_id))
            return

        if rec_transactions.empty:
            print("REC {} | No transaction, negotiating with OMIE market.".format(self.rec_id))
            self.energy_pool += self.energy_need
            self.step_cost = self.energy_need * self.marginal_price_ts[self.current_step]
        else:
            t = rec_transactions.iloc[0]
            
            if self.energy_need > 0:
                self.energy_pool += t.quantity
                self.step_cost = t.price * t.quantity
                print("REC {} | Bought {} units at price {}.".format(self.rec_id, t.quantity, t.price))
            else:
                self.energy_pool -= t.quantity
                self.step_cost = -t.price * t.quantity
                print("REC {} | Sold {} units at price {}.".format(self.rec_id, t.quantity, t.price))

    def handle_importations(self):
        if self.total_demand <= self.energy_pool:
            print("REC {} | Energy pool is sufficient to meet demand.".format(self.rec_id))
            # full statisfaction of demand
            for tenant_id, demand in enumerate(self.actions):
                if demand < 0:
                    self.energy_pool -= abs(demand)
                    self.reputation[tenant_id] -= abs(demand) * self.marginal_price_ts[self.current_step]
                    self.tenant_transactions[tenant_id] = demand
                    print("REC {} | Tenant {}: Asked for {} units, received {} units.".format(self.rec_id, tenant_id, -demand, abs(demand)))
        else:
            # limited energy, distribute proportionally to credits
            # consider total reputation of all tenants that are requesting energy
            print("REC {} | Energy pool is insufficient to meet demand.".format(self.rec_id))

            current_reputation = self.reputation.copy()
            total_reputation = sum(current_reputation[i] for i in range(len(self.actions)) if self.actions[i] < 0)

            if total_reputation == 0:
                print("REC {} | No reputation, distributing equally.".format(self.rec_id))
                current_reputation = [1] * len(self.actions)

            for tenant_id, demand in enumerate(self.actions):
                if demand < 0 and self.reputation[tenant_id] > 0:
                    # calculate the share of energy based on reputation
                    share = (current_reputation[tenant_id] / total_reputation) * self.energy_pool
                    self.energy_pool -= share
                    self.reputation[tenant_id] -= share * self.marginal_price_ts[self.current_step]
                    self.tenant_transactions[tenant_id] = share
                    print("REC {} | Tenant {}: Asked for {} units, received {} units.".format(self.rec_id, tenant_id, -demand, share))

    def step(self):
        self.execute_tenant_transactions()
        self.current_step += 1

        self.cost += self.step_cost
        self.log_step()
