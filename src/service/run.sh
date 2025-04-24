echo "===Reorganising directory and building the agent server image..."
cp ../utils/ .
mkdir agent && cp ../logic/agent/ agent/
cp ../training/pipeline.yaml .
docker build -t rafego16/rl-agent-server:latest .
docker push rafego16/rl-agent-server:latest

echo "===Restoring directory structure..."
rm pipeline.yaml
rm -r agent
mv server.py server
rm *.py
mv server server.py

echo "===Applying the inference service..."
kubectl create namespace my-service > /dev/null 2>&1 # create ns if does not exist
kubectl delete -f inference-service.yaml -n my-service > /dev/null 2>&1 # delete if exists
kubectl apply -f inference-service.yaml -n my-service

# echo "===Waiting for the service to be ready..."
# while true; do
#     response=$(curl -s -o /dev/null -w "%{http_code}" http://random-predictor.my-service.svc.cluster.local/v1/models/my-agent:predict -d @./init.json)
#     if [ $response -eq 200 ]; then
#         break
#     fi
#     sleep 2
# done
