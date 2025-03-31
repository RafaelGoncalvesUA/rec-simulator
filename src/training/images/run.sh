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
docker build -t rafego16/pipeline-custom-image:latest .
docker push rafego16/pipeline-custom-image:latest

cd ../../agent-libs
cp ../../../utils/*.py .
cp ../../../requirements.txt .
mkdir agent && cp -r ../../../agent/ agent/
echo "===Building a training image for Kubeflow pipeline..."
docker build -t rafego16/pipeline-custom-image-train:latest .
rm *.py && rm -r agent
docker push rafego16/pipeline-custom-image-train:latest

docker rmi pipeline-custom-image-builder:latest > /dev/null 2>&1
docker rmi $(docker images -f "dangling=true" -q) --force > /dev/null 2>&1