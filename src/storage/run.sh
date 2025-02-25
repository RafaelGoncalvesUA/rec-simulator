kubectl create namespace minio
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install minio oci://registry-1.docker.io/bitnamicharts/minio -f values.yaml -n minio

# kubectl port-forward --namespace minio svc/minio 9001:9001