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
tmux new-session -d -s kubeflow-forward 'kubectl port-forward svc/istio-ingressgateway -n istio-system 8080:80'
cd ../../src

echo "---> Compiling Kubeflow training pipeline..."
cd training
sed -i 's/enableCache: true/enableCache: false/g' pipeline.yaml
python3 pipeline.py

sleep 25

cd ../ # to src
echo "---> Deploying Kubeflow training pipelines..."
for i in {1..50}
do
    echo "Deploying pipeline $i/100..."
    python3 -m training.deploy
    sleep 15
done

kubectl delete pods -n kubeflow-user-example-com --field-selector=status.phase==Succeeded
kubectl delete pods -n kubeflow-user-example-com --field-selector=status.phase==Failed

tmux kill-session -t k3s_monitor
tmux kill-session -t kubeflow-forward

python3 process_events.py