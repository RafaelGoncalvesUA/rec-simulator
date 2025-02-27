kubectl create namespace kafka
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install kafka oci://registry-1.docker.io/bitnamicharts/kafka -f values.yaml -n kafka

# update with new values
# helm upgrade kafka oci://registry-1.docker.io/bitnamicharts/kafka -f values.yaml -n kafka