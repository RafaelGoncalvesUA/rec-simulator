helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Minio
# API: kubectl port-forward -n minio svc/minio 9000:9000
# CONSOLE: kubectl port-forward -n minio svc/minio 9001:9001

helm install minio oci://registry-1.docker.io/bitnamicharts/minio -f minio-values.yaml -n minio --create-namespace
kubectl delete -f minio-ingress.yaml -n minio > /dev/null 2>&1 # delete if exists
kubectl delete -f minio-hpa.yaml -n minio > /dev/null 2>&1 # delete if exists
kubectl apply -f minio-ingress.yaml -n minio
kubectl apply -f minio-hpa.yaml -n minio

# TimescaleDB
# === Port forwarding ===
# kubectl port-forward timescaledb-1 6432:5432 -n timescaledb
# PGPASSWORD=$PGPOSTGRESPASSWORD psql -U app -h localhost -p 6432 app
# ======= Service =======
# PGPASSWORD=$PGPOSTGRESPASSWORD psql -U app -h timescaledb-r.timescaledb.svc.cluster.local -p 5432 app

kubeclt create namespace timescaledb > /dev/null 2>&1 # Create namespace if it doesn't exist
kubectl delete -f timescaledb.yaml -n timescaledb > /dev/null 2>&1 # delete if exists
kubectl delete -f timescaledb-hpa.yaml -n timescaledb > /dev/null 2>&1 # delete if exists

kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml # Install metrics server
kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.23/releases/cnpg-1.23.2.yaml
kubectl apply -f timescaledb.yaml -n timescaledb
kubectl apply -f timescaledb-hpa.yaml -n timescaledb
PGPOSTGRESPASSWORD=$(kubectl get secret timescaledb-app -n timescaledb -o jsonpath='{.data.password}' | base64 --decode)
