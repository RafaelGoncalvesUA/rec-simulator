cp ../../data . -r mv .env .env_bak
echo "SERVICE_BASE_URL=http://random-predictor.test.svc.cluster.local" > .env
docker build -t producer .
rm -r data && rm .env && mv .env_bak .env

kubectl create namespace test
kubectl apply -f producer.yaml -n test
