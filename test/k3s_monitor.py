import csv
import subprocess
import time
from datetime import datetime
import sys

INTERVAL_SECONDS = 5  # Collect every 5 seconds
OUTPUT_CSV = sys.argv[1] if len(sys.argv) > 1 else "k3s_resource_usage.csv"
namespaces = ["minio", "timescaledb", "my-service", "collection", "test"]
current_ns_pipeline_pods = 2 # ml pipeline init pods

def get_number_of_running_pods(namespace, extra_field=[]):
    try:
        base_command = ["kubectl", "get", "pods", "-n", namespace, "--no-headers"]
        base_command += extra_field
        output = subprocess.check_output(base_command).decode("utf-8")
        lines = output.strip().split("\n")
        return len(lines) - 1  # Subtract 1 for the header line
    except Exception as e:
        print("Error getting number of pods:", e)
        return 0

def get_metrics():
    try:
        output = subprocess.check_output(["kubectl", "top", "nodes", "--no-headers"]).decode("utf-8")
        lines = output.strip().split("\n")

        stress_test_pods = get_number_of_running_pods("my-service")
        events = {}
        # pods = {ns: get_number_of_running_pods(ns) for ns in namespaces}

        # for ns, count in pods.items():
        #     if count > 0:
        #         events[ns] = count
        #         namespaces.remove(ns)

        pipeline_pods = get_number_of_running_pods("kubeflow-user-example-com")

        if pipeline_pods > current_ns_pipeline_pods:
            events["pipeline"] = pipeline_pods

        print(events)
        print("Stress test pods:", stress_test_pods)
        
        timestamp = datetime.now().isoformat()
        metrics = []

        for line in lines:
            cols = line.split()
            node, cpu, cpu_per, memory, memory_per = cols
            metrics.append([timestamp, node, cpu, cpu_per, memory, memory_per])
    
        return metrics, events, stress_test_pods
    
    except Exception as e:
        print("Error collecting metrics:", e)
        return []

ctr = 0

with open(OUTPUT_CSV, mode='w', newline='') as file, open("events.txt", mode='w') as events_file:
    writer = csv.writer(file)
    writer.writerow(["timestamp", "node", "cpu", "cpu_per", "memory", "memory_per"])
    while True:
        metrics, events, stress_test_pods = get_metrics()
        for row in metrics:
            writer.writerow(row)
        file.flush()
        print("Ctr:", ctr)

        for event, counter in events.items():
            events_file.write(f"{ctr} - {event} has {counter} pods\n")

        if stress_test_pods > 1:
            events_file.write(f"Stress pods: {stress_test_pods}\n")

        events_file.flush()
        time.sleep(INTERVAL_SECONDS)

        ctr += 1
