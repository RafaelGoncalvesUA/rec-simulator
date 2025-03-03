echo "Reorganising directory and building the agent server image..."
cp ../utils/*.py .
cp ../agent/*.py .
docker build -t rafego16/rl-agent-server:latest .
docker push rafego16/rl-agent-server:latest

echo "Restoring directory structure..."
mv server.py server && rm *.py && mv server server.py

echo "Applying the inference service..."
kubectl create namespace test > /dev/null 2>&1 # create ns if does not exist
kubectl delete -f inference-service.yaml -n test > /dev/null 2>&1 # delete if exists
kubectl apply -f inference-service.yaml -n test