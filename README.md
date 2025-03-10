# rec-simulator
## Notebook
**[notebook.ipynb](notebook.ipynb)**: Jupyter notebook that explains the simulation and the results.

```
.
├── data
│   ├── config.yaml
│   ├── gen_microgrids.py
│   ├── battery
│       ├── small.yaml
│       ├── large.yaml
│       └── gen_batteries.py
│   ├── grid
│   ├── load
│   └── renewable
├── examples
│   ├── dataset
│   │   ├── battery.yaml
│   │   ├── config.yaml
│   │   ├── grid
│   │   ├── loads
│   │   └── renewables
│   ├── env_from_dataset
│   │   ├── data
│   │   └── env.yaml
│   ├── env_from_dataset.py
│   ├── env_from_scratch.py
│   ├── load_predef_env.py
│   └── log.csv
├── notebook.ipynb
├── README.md
├── requirements.txt
└── src
    ├── agent
    │   ├── base_agent.py
    │   ├── __init__.py
    │   ├── policies.py
    │   └── sb3_agent.py
    ├── client
    │   ├── Dockerfile
    │   ├── producer.py
    │   ├── producer.yaml
    │   └── run.sh
    ├── __init__.py
    ├── local_simulation.py
    ├── logs
    │   └── log_0.csv
    ├── pipeline.yaml
    ├── run.sh
    ├── service
    │   ├── agent.zip
    │   ├── inference-service.yaml
    │   ├── init.json
    │   ├── requirements.txt
    │   ├── run.sh
    │   └── server.py
    ├── storage
    │   ├── minio-ingress.yaml
    │   ├── run.sh
    │   └── values.yaml
    ├── training
    │   ├── components
    │   ├── deploy.py
    │   ├── images
    │   ├── local_outputs
    │   ├── pipeline.py
    │   └── pipeline.yaml
    └── utils
        ├── env_loader.py
        ├── __init__.py
        ├── kfp_client_manager.py
        └── microgrid_env.py
```