# LASSY

## Overview

LASSY (Latency-Aware SLOs-Sufficing Scheduling System) is a novel scheduling system designed for cloud/edge computing environments. It addresses the challenge of network latency in cloud-hosted applications, particularly for latency-sensitive services such as Edge AI. By integrating queuing theory, LASSY predicts and optimizes end-to-end tail latency to ensure compliance with Service Level Objectives (SLOs).

Key features of LASSY include:

- **Latency-Aware Scheduling**: Predicts and minimizes network and queuing delays for optimal service performance.
- **SLO Compliance**: Ensures applications meet latency constraints by managing deployments across cloud and edge nodes.
- **Resource Optimization**: Reduces operational costs by balancing workloads efficiently between cloud and edge infrastructure.

## Prerequisites

Before running LASSY, ensure you have the following dependencies installed:

- **Python 3.7+** (Required to run the script)
- **Required Python Libraries**:
  - `gurobipy` (for optimization modeling)
  - `scipy` (for scientific computing and optimization)
  - `math`, `os`, `sys` (built-in modules for various functionalities)
  - `json` (for handling input data)
  - `decimal` (for high-precision calculations)
  - `datetime` (for timestamp handling)

### Installation Instructions

1. **Install Python dependencies**:

   ```bash
   pip install gurobipy scipy
   ```

## Usage

### Running the LASSY Script

To run the LASSY script, use the following command:

```bash
python LASSY.py
```

### Running the MatrixP Script

To run the MatrixP script, use the following command:

```bash
sudo ./run_matrixp.sh -u <user> -r <rate> -s <service_ip> -p <port> -o <round> [repeat for multiple users]
```

Example:

```bash
sudo ./run_matrixp.sh -u u1 -r 50 -s 172.16.66.104 -p 31111 -o 1 -u u2 -r 100 -s 172.16.66.104 -p 31111 -o 1
```

### Kubernetes Deployment

#### Deploying TNpy

To deploy the TNpy application, use the following Kubernetes configuration:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tnpy
spec:
  replicas: 1
  selector:
    matchLabels:
      app: tnpy
  template:
    metadata:
      labels:
        app: tnpy
    spec:
      containers:
      - name: tnpy
        image: yinantsao/tnpy:latest
        resources:
          requests:
            cpu: "1"
            memory: 4Gi
          limits:
            cpu: "1"
            memory: 4Gi
        ports:
        - containerPort: 8081

---
apiVersion: v1
kind: Service
metadata:
  name: tnpy
spec:
  type: NodePort
  selector:
    app: tnpy
  ports:
    - protocol: TCP
      port: 8081
      nodePort: 31111
```

#### Deploying PyTess

To deploy the PyTess application, use the following Kubernetes configuration:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pytess
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pytess
  template:
    metadata:
      labels:
        app: pytess
    spec:
      containers:
      - name: pytess
        image: yinantsao/pytess:latest
        resources:
          requests:
            cpu: "2"
            memory: 2Gi
          limits:
            cpu: "2"
            memory: 2Gi
        ports:
        - containerPort: 8081
        
---
apiVersion: v1
kind: Service
metadata:
  name: pytess
spec:
  type: NodePort
  selector:
    app: pytess
  ports:
    - protocol: TCP
      port: 8081
      nodePort: 31112
```

## Input Data

### TNpy Input Data

The input data for TNpy is specified in the `init_tnpy.json` file:

```json
{
  "nodes": ["C1", "E1", "E2", "E3"],
  "pricing": {"C1": 6, "E1": 10, "E2": 8, "E3": 8},
  "users": ["u1", "u2", "u3", "u4", "u5"],
  "capacities": {"C1": 15, "E1": 5, "E2": 8, "E3": 8},
  "latency_node_user": {
    "('C1', 'u1')": 40, "('C1', 'u2')": 50, "('C1', 'u3')": 60, "('C1', 'u4')": 60, "('C1', 'u5')": 50,
    "('E1', 'u1')": 5, "('E1', 'u2')": 5, "('E1', 'u3')": 65, "('E1', 'u4')": 65, "('E1', 'u5')": 5,
    "('E2', 'u1')": 45, "('E2', 'u2')": 10, "('E2', 'u3')": 5, "('E2', 'u4')": 20, "('E2', 'u5')": 60,
    "('E3', 'u1')": 50, "('E3', 'u2')": 60, "('E3', 'u3')": 20, "('E3', 'u4')": 5, "('E3', 'u5')": 10
  },
  "request_rates": {"u1": 0.045, "u2": 0.045, "u3": 0.045, "u4": 0.045, "u5": 0.045},
  "service_rate": 0.040,
  "slo": 100,
  "deployment_name": "tngo",
  "opti_pref": 1
}
```

### PyTess Input Data

The input data for PyTess is specified in the `init_pytess.json` file:

```json
{
  "nodes": ["C1", "E1", "E2", "E3"],
  "pricing": {"C1": 6, "E1": 10, "E2": 8, "E3": 8},
  "users": ["u1", "u2", "u3", "u4", "u5"],
  "capacities": {"C1": 15, "E1": 5, "E2": 8, "E3": 8},
  "latency_node_user": {
    "('C1', 'u1')": 40, "('C1', 'u2')": 50, "('C1', 'u3')": 60, "('C1', 'u4')": 60, "('C1', 'u5')": 50,
    "('E1', 'u1')": 5, "('E1', 'u2')": 5, "('E1', 'u3')": 65, "('E1', 'u4')": 65, "('E1', 'u5')": 5,
    "('E2', 'u1')": 45, "('E2', 'u2')": 10, "('E2', 'u3')": 5, "('E2', 'u4')": 20, "('E2', 'u5')": 60,
    "('E3', 'u1')": 50, "('E3', 'u2')": 60, "('E3', 'u3')": 20, "('E3', 'u4')": 5, "('E3', 'u5')": 10
  },
  "request_rates": {"u1": 0.006, "u2": 0.004, "u3": 0.004, "u4": 0.004, "u5": 0.004},
  "service_rate": 0.007,
  "slo": 400,
  "deployment_name": "tngo",
  "opti_pref": 1
}
```