#!/bin/bash

# Check for -y flag
SKIP_PROMPTS=false
if [[ "$1" == "-y" ]]; then
    SKIP_PROMPTS=true
fi

function press_enter_to_continue {
    if [ "$SKIP_PROMPTS" = true ]; then
        echo ""
    else
        read -p "Press ENTER to continue: " && echo
    fi
}

echo "---> Setting up MinIO object storage..."
cd storage
# bash run.sh
press_enter_to_continue

echo "---> Compiling Kubeflow training pipeline..."
cd ../training
python3 pipeline.py
press_enter_to_continue

echo "---> Deploying the inference service..."
cd ../service
# bash run.sh
press_enter_to_continue

echo "---> Deploying the collector service..."
cd collector
# bash run.sh
press_enter_to_continue

echo "---> Deploying a producer script to generate data..."
cd ../../client
# bash run.sh
press_enter_to_continue

echo "DONE."
