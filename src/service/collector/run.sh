echo "===Reorganising directory..."
cp .env .env_bak
cp ../../utils/kfp_client_manager.py .
cp ../../utils/db.py .
PGPOSTGRESPASSWORD=$(kubectl get secret timescaledb-app -n timescaledb -o jsonpath='{.data.password}' | base64 --decode)
echo "DATABASE_PASSWORD=$PGPOSTGRESPASSWORD" >> .env

echo "==Building the data collector image..."
docker build -t rafego16/data-collector:latest .
docker push rafego16/data-collector:latest

echo "===Restoring directory structure..."
rm kfp_client_manager.py db.py
rm .env && mv .env_bak .env

echo "===Applying the data collection service..."
kubectl create namespace collection > /dev/null 2>&1 # create ns if does not exist
kubectl delete -f collector.yaml -n collection > /dev/null 2>&1 # delete if exists
kubectl apply -f collector.yaml -n collection
