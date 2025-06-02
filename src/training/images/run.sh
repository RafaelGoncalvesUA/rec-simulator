cd builder
echo "===Building the custom image builder..."
docker build -t pipeline-custom-image-builder:latest .

echo "===Building a default image for Kubeflow pipeline..."
cd ../main
cp ../../../utils/*.py .
docker build -t rafego16/pipeline-custom-image:latest .
rm *.py

echo "===Updating the default image with environment variables..."
cd update-env
cp .env .env_bak
PGPOSTGRESPASSWORD=$(kubectl get secret timescaledb-app -n timescaledb -o jsonpath='{.data.password}' | base64 --decode)
echo "DATABASE_PASSWORD=$PGPOSTGRESPASSWORD" >> .env
rm .env && mv .env_bak .env
docker build -t rafego16/pipeline-custom-image:latest .
docker push rafego16/pipeline-custom-image:latest

cd ../../agent-libs
cp ../../../requirements.txt .
mkdir utils & cp -r ../../../utils/* utils/
mkdir logic && mkdir logic/agent & cp -r ../../../logic/agent/* logic/agent/
mkdir forecasting && cp -r ../../../forecasting/* forecasting/
echo "===Building a training image for Kubeflow pipeline..."
docker build -t rafego16/pipeline-custom-image-train:latest .
rm -r logic & rm -r utils & rm -r forecasting
docker push rafego16/pipeline-custom-image-train:latest

docker rmi pipeline-custom-image-builder:latest > /dev/null 2>&1
docker rmi $(docker images -f "dangling=true" -q) --force > /dev/null 2>&1 