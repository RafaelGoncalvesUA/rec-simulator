DOCKER_USER=rafego16

cd builder
docker build -t pipeline-custom-image-builder:latest .

cd ../main
cp ../../../utils/*.py .
docker build -t $DOCKER_USER/pipeline-custom-image:latest .
cd update-env
docker build -t $DOCKER_USER/pipeline-custom-image:latest .
rm *.py
docker push $DOCKER_USER/pipeline-custom-image:latest

cd ../../agent-libs
docker build -t $DOCKER_USER/pipeline-custom-image-train:latest .
docker push $DOCKER_USER/pipeline-custom-image-train:latest