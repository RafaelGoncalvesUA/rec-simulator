# remove previous deployment
kubectl delete -f inference-service.yaml -n test > /dev/null

cd ../utils/*.py .
cd ../agent/*.py .
docker build -t rafego16/rl-agent-server:latest .
docker push rafego16/rl-agent-server:latest
mv server.py server && rm *.py && mv server server.py

kubectl apply -f inference-service.yaml -n test
