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

tmux kill-session -t k3s_monitor

cd ../../src

cd storage
helm uninstall minio -n minio
for file in minio*.yaml; do
    kubectl delete -f "$file" -n minio --ignore-not-found
done
for file in timescaledb*.yaml; do
    kubectl delete -f "$file" -n timescaledb --ignore-not-found
done

press_enter_to_continue

cd ../service
for file in *.yaml; do
    kubectl delete -f "$file" -n my-service --ignore-not-found
done

press_enter_to_continue

cd collector
for file in *.yaml; do
    kubectl delete -f "$file" -n collection --ignore-not-found
done
press_enter_to_continue

kubectl delete pods --all -n minio -n timescaledb  -n my-service -n collection
press_enter_to_continue

kubectl delete namespace minio timescaledb my-service collection
press_enter_to_continue

NS=`kubectl get ns |grep Terminating | awk 'NR==1 {print $1}'` && kubectl get namespace "$NS" -o json   | tr -d "\n" | sed "s/\"finalizers\": \[[^]]\+\]/\"finalizers\": []/"   | kubectl replace --raw /api/v1/namespaces/$NS/finalize -f -

minio_pods=$(kubectl get pods -n minio --no-headers | wc -l)
timescaledb_pods=$(kubectl get pods -n timescaledb --no-headers | wc -l)
my_service_pods=$(kubectl get pods -n my-service --no-headers | wc -l)
collection_pods=$(kubectl get pods -n collection --no-headers | wc -l)

if [ "$minio_pods" -eq 0 ] && [ "$timescaledb_pods" -eq 0 ] && [ "$my_service_pods" -eq 0 ] && [ "$collection_pods" -eq 0 ]; then
    echo "All pods have been deleted successfully."
else
    echo "Some pods are still running. Please check manually."
fi