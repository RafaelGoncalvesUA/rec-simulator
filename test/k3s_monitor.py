import csv
import subprocess
import time
from datetime import datetime
import sys

INTERVAL_SECONDS = 10  # Collect every 10 seconds
OUTPUT_CSV = sys.argv[1] if len(sys.argv) > 1 else "k3s_resource_usage.csv"

def get_number_of_pods(namespace):
    try:
        output = subprocess.check_output(["kubectl", "get", "pods", "-n", namespace]).decode("utf-8")
        lines = output.strip().split("\n")
        return len(lines) - 1  # Subtract 1 for the header line
    except Exception as e:
        print("Error getting number of pods:", e)
        return 0

def get_metrics():
    try:
        output = subprocess.check_output(["kubectl", "top", "nodes", "--no-headers"]).decode("utf-8")
        lines = output.strip().split("\n")

        service_pods = get_number_of_pods("test")
        minio_pods = get_number_of_pods("minio")
        timescaledb_pods = get_number_of_pods("timescaledb")

        metrics = []
        timestamp = datetime.now().isoformat()

        for line in lines:
            cols = line.split()
            node, cpu, cpu_per, memory, memory_per = cols
            metrics.append([timestamp, node, cpu, cpu_per, memory, memory_per, service_pods, minio_pods, timescaledb_pods])
    
        return metrics
    
    except Exception as e:
        print("Error collecting metrics:", e)
        return []


ctr = 0

with open(OUTPUT_CSV, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["timestamp", "node", "cpu", "cpu_per", "memory", "memory_per", "service_pods", "minio_pods", "timescaledb_pods"])
    while True:
        metrics = get_metrics()
        for row in metrics:
            writer.writerow(row)
        file.flush()
        print("Ctr:", ctr)
        time.sleep(INTERVAL_SECONDS)

        ctr += 1
