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

echo "---> Compiling Kubeflow training pipeline..."
cd ../training
python3 pipeline.py
press_enter_to_continue

cd ../ # to src
echo "---> Deploying Kubeflow training pipelines..."
for i in {1..100}
do
    echo "Deploying pipeline $i/100..."
    python3 -m training.deploy
    press_enter_to_continue
done