# Machine Learning as a Service (MLaaS) for Renewable Energy Communities (RECs)

> **Note**: Although the repository is named `rec_simulator`, our goal was not to create a simulator, but rather to develop a Machine Learning as a Service (MLaaS) platform and validate it with simulated environments (based on real data).

**Abstract**: Given the increasing energy demand and the environmental consequences of fossil fuel consumption, the shift toward sustainable energy sources has become a global priority. Renewable Energy Communities (RECs)—comprising citizens, businesses, and legal entities—are emerging to democratise access to renewable energy. These communities allow members to produce their own energy, sharing or selling any surplus, thus promoting sustainability and generating economic value. However, scaling RECs while ensuring profitability is challenging due to renewable energy intermittency, price volatility, and heterogeneous consumption patterns. To address these issues, this paper presents a Machine Learning as a Service (MLaaS) framework, where each REC microgrid has a customised Reinforcement Learning (RL) agent and electricity price forecasts are included to support decision-making. All the conducted experiments, using the open-source simulator Pymgrid, demonstrate that the proposed agents **reduced operational costs by up to 96.41%** compared to a robust baseline heuristic. Moreover, this study also introduces two cost-saving features: Peer-to-Peer (P2P) energy trading between communities and internal energy pools, allowing microgrids to draw local energy before using the main grid. Combined with the best-performing agents, these features achieved **trading cost reductions of up to 45.58%**. Finally, in terms of deployment, the system relies on an MLOps-compliant infrastructure that enables parallel training pipelines and an autoscalable inference service. Overall, this work provides significant contributions to energy management, fostering the development of more sustainable, efficient, and cost-effective solutions.

**Authors**: Rafael Gonçalves, Diogo Gomes and Mário Antunes

## Development Features
- ☁️ Kubernetes-based MLOps pipeline (training + inference)
- 🤖 RL agents per microgrid (DQN, PPO, A2C, etc.)
- 📦 Scalable data storage via MinIO and TimescaleDB
- 🔄 Online training with ADWIN-based drift detection
- 📈 Forecasting of electricity price (NeuralProphet)

## Validation Features
- ⚙️ Modular simulation of microgrids
- 🤝 Peer-to-peer (P2P) energy trading with bid-based matching and clearing

## 📁 Key Directories
### [`data/`](./data)
Contains diverse time series data for microgrid definition.

- [`data/load/`](./data/load): Load profiles (consumption) for multiple microgrids.
- [`data/renewable/`](./data/renewable): Renewable generation profiles (e.g., PV production).
- [`data/grid/`](./data/grid): Grid purchase/sale price profiles.
- [`data/battery/`](./data/battery): Battery configurations (small, large, combinations).
- [`data/gen_microgrids.py`](./data/gen_microgrids.py): Script to generate microgrids.

---

### [`examples/`](./examples)
Examples and templates for generating environments from predefined or custom datasets.

- [`examples/env_from_dataset/`](./examples/env_from_dataset): Example with full dataset structure.
- [`examples/env_from_scratch.py`](./examples/env_from_scratch.py): Script to create microgrid environments programmatically.

---

### [`src/`](./src)
The core source code of the platform.

### Sub-directories
- [`src/logic/agent/`](./src/logic/agent): Implementation of agent types (SB3, heuristic, random).
- [`src/logic/rec.py`](./src/logic/rec.py): Logic for the REC-level coordination and trading.
- [`src/forecasting/`](./src/forecasting): OMIE data collection and Neural Prophet model.
- [`src/training/`](./src/training): Kubeflow-compatible training pipeline for agents.
- [`src/service/`](./src/service): Inference service and data collector deployment.
- [`src/storage/`](./src/storage): TimescaleDB and MinIO deployment.
- [`src/utils/custom_simulator/`](./src/utils/custom_simulator): Customised simulator with OpenAI Gym environment.

### Root files
- [`src/notebook.ipynb`](./notebook.ipynb): Jupyter notebook showcasing how to use the selected simulator.
- [`src/benchmark.py`](./src/benchmark.py): Baseline comparison between heuristic and RL agents.
- [`src/trade.py`](./src/trade.py): Script to execute simulated P2P trading cycles.
- [`src/deploy.sh`](./src/deploy.sh): Deployment automation script.

---

### [`test/`](./test)
Evaluation, monitoring, and benchmarking notebooks and results.

- [`test/agent/`](./test/agent): Evaluation of RL agent performance, reward curves, decision trees.
- [`test/boot/`](./test/boot): K3s deployment resource usage (CPU, RAM) and restore scripts.
- [`test/detector/`](./test/detector): ADWIN-based drift detection testing and visualisation.
- [`test/forecasting/`](./test/forecasting): Forecasting quality and model evaluation.
- [`test/pipeline/`](./test/pipeline): Resource monitoring for training pipelines.
- [`test/trades/`](./test/trades): Evaluation of P2P trading behaviour, cost comparison, and analysis.

