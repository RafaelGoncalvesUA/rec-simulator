echo "===Reorganising directory..."
cp -r ../../data . && cp .env .env_bak
echo "SERVICE_BASE_URL=http://random-predictor.test.svc.cluster.local" >> .env
echo "DATABASE_HOST=timescaledb-r.timescaledb.svc.cluster.local" >> .env
echo "DATABASE_PORT=5432" >> .env
PGPOSTGRESPASSWORD=$(kubectl get secret timescaledb-app -n timescaledb -o jsonpath='{.data.password}' | base64 --decode)
echo "DATABASE_PASSWORD=$PGPOSTGRESPASSWORD" >> .env

echo "==Building the producer image..."
docker build -t rafego16/rec-producer .
docker push rafego16/rec-producer

echo "===Restoring directory structure..."
rm -r data
rm .env && mv .env_bak .env

echo "===Applying the producer service..."
kubectl create namespace test > /dev/null 2>&1 # create ns if does not exist
kubectl delete -f producer.yaml -n test > /dev/null 2>&1 # delete if exists
kubectl apply -f producer.yaml -n test
