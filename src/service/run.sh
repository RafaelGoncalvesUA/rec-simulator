echo "===Reorganising directory and building the agent server image..."
cp ../utils/ .
mkdir agent && cp ../agent/ agent/
cp ../training/pipeline.yaml .
docker build -t rafego16/rl-agent-server:latest .
docker push rafego16/rl-agent-server:latest

echo "===Restoring directory structure..."
rm pipeline.yaml
rm -r agent
mv server.py server && rm *.py && mv server server.py

echo "===Applying the inference and data collection service..."
kubectl create namespace test > /dev/null 2>&1 # create ns if does not exist
kubectl delete -f inference-service.yaml -n test > /dev/null 2>&1 # delete if exists
kubectl apply -f inference-service.yaml -n test

echo "===Waiting for the service to be ready..."
while true; do
    response=$(curl -s -o /dev/null -w "%{http_code}" http://random-predictor.test.svc.cluster.local/v1/models/my-agent:predict -d @./init.json)
    if [ $response -eq 200 ]; then
        break
    fi
    sleep 2
done
