#!/bin/bash

#SBATCH --job-name=rl-rec
#SBATCH --output=benchmark.txt
#SBATCH --nodes=1
#SBATCH --ntasks=1                  # 1 tarefa (processo) por nó
#SBATCH --cpus-per-task=8           # 8 CPUs por tarefa
#SBATCH --gres=gpu:1                # 1 GPU por nó
#SBATCH --time=7-00:00:00           # Limite de tempo para execução
#SBATCH --partition=gpuPartition    # Partição padrão (ajustar conforme necessário)

SCRIPT_NAME="local_simulation.py"

source ../venv/bin/activate # virtual env should be created in the root directory
srun python ${SCRIPT_NAME}
