echo "Reorganising directory and building the producer image..."
cp -r ../../data . && mv .env .env_bak
echo "SERVICE_BASE_URL=http://random-predictor.test.svc.cluster.local" > .env
echo "DATA_BASE_PATH=/app/data/" >> .env
docker build -t rafego16/rec-producer .
docker push rafego16/rec-producer

echo "Restoring directory structure..."
rm -r data && rm .env && mv .env_bak .env

echo "Applying the producer service..."
kubectl create namespace test > /dev/null 2>&1 # create ns if does not exist
kubectl delete -f producer.yaml -n test > /dev/null 2>&1 # delete if exists
kubectl apply -f producer.yaml -n test
