kubectl create namespace minio
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install minio oci://registry-1.docker.io/bitnamicharts/minio -f values.yaml -n minio

# API: kubeclt port-forward -n minio svc/minio 9000:9000
# CONSOLE: kubectl port-forward -n minio svc/minio 9001:9001
