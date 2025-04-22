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

tmux new-session -d -s k3s_monitor 'python3 ../k3s_monitor.py'
cd ../../src

echo "---> Setting up MinIO object storage..."
cd storage
bash run.sh
press_enter_to_continue

echo "---> Deploying the inference service..."
cd ../service
bash run.sh
press_enter_to_continue

echo "---> Deploying the collector service..."
cd collector
bash run.sh
press_enter_to_continue

cd ../../../test/boot

echo "Stress testing the inference service..."
kubectl create namespace test > /dev/null 2>&1
kubectl delete -f perf.yaml -n test> /dev/null 2>&1
kubectl create -f perf.yaml -n test

TEST_PODNAME=$(kubectl get pods -n test -o jsonpath='{.items[0].metadata.name}')
kubectl logs ${TEST_PODNAME} -n test > test_deploy_results.txt

tmux kill-session -t k3s_monitor