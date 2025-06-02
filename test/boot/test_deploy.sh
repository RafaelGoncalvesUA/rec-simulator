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

function check_pod_running {
    local namespace=$1
    local min_pods=$2

    while true; do
        running_pods=$(kubectl get pods -n "$namespace" --no-headers | grep Running | wc -l)
        if [ "$running_pods" -ge "$min_pods" ]; then
            break
        fi
        echo "Waiting for $min_pods pods in namespace '$namespace' to be running..."
        sleep 5
    done
    echo "All required pods in namespace '$namespace' are running."
} 

tmux new-session -d -s k3s_monitor 'python3 ../k3s_monitor.py'
sleep 40

cd ../../src

echo "---> Setting up MinIO object storage and TimescaleDB..."
cd storage
bash run.sh

check_pod_running "minio" 3
check_pod_running "timescaledb" 3
sleep 5

echo "---> Deploying the inference service..."
cd ../service
bash run.sh

check_pod_running "my-service" 1

echo "---> Deploying the collector service..."
cd collector
bash run.sh

check_pod_running "collection" 1

tmux new-session -d -s minio-forwarder 'kubectl port-forward -n minio svc/minio 9001:9001'
echo "Please create the MinIO bucket 'agents' and upload an agent"
press_enter_to_continue
tmux kill-session -t minio-forwarder

cd ../../../test/boot

echo "Stress testing the inference service..."
kubectl create namespace test > /dev/null 2>&1
kubectl delete -f perf.yaml -n test> /dev/null 2>&1
kubectl create -f perf.yaml -n test

check_pod_running "test" 1
press_enter_to_continue

tmux kill-session -t k3s_monitor

TEST_PODNAME=$(kubectl get pods -n test -o jsonpath='{.items[0].metadata.name}')
kubectl logs ${TEST_PODNAME} -n test > test_deploy_results.txt
