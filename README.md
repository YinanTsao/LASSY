# LASSY (Latency-Aware SLOs-Sufficing Scheduling System)

## Overview

LASSY is a novel scheduling system designed for cloud/edge computing environments. It addresses the challenge of network latency in cloud-hosted applications, particularly for latency-sensitive services such as Edge AI. By integrating queuing theory, LASSY predicts and optimizes end-to-end tail latency to ensure compliance with Service Level Objectives (SLOs).

Key features of LASSY include:

- **Latency-Aware Scheduling**: Predicts and minimizes network and queuing delays for optimal service performance.
- **SLO Compliance**: Ensures applications meet latency constraints by managing deployments across cloud and edge nodes.
- **Resource Optimization**: Reduces operational costs by balancing workloads efficiently between cloud and edge infrastructure.

## Prerequisites

Before running LASSY, ensure you have the following dependencies installed:

- **Python 3.7+** (Required to run the script)
- **Gurobi Optimizer** (for optimization modeling). You can download it from the [Gurobi website](https://www.gurobi.com), remember to get a license for large scale test.
- **Kubernetes Cluster** (Required to deploy applications). For more information, visit the [Kubernetes website](https://kubernetes.io).
- **httperf** (Required for performance testing). You can find more information on the [httperf website](https://linux.die.net/man/1/httperf).

    IMPORTANT: To obtain correct results, it is necessary to run at most one httperf process per client machine. Also, there should be as few background processes as possible both on the client and server machines.


### Installation Instructions

1. **Install Python dependencies**:

   ```bash
   pip install gurobipy scipy
   ```

2. **Install httperf on the client machine**

   ```bash
   cd httperf-master \
   make && make install
   ```


## Usage

### Kubernetes Deployment

The deployment yaml file of the target application should be prepared. We offer 2 different applications as we used in our experiments, both are monolithic and single-threaded. Based on the same characteristics, other applications are also available for verification.

#### Deploying thumbnailing application (tnpy)

To deploy the tnpy application, use the following Kubernetes configuration:

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
            memory: 1Gi
          limits:
            cpu: "1"
            memory: 1Gi
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

#### Deploying OCR application (pytess)

To deploy the pytess application, use the following Kubernetes configuration:

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

The input data for LASSY should be defined in the following format:

### tnpy Input Data

The input data for tnpy is specified in the `init_tnpy.json` file:

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

### pytess Input Data

The input data for pytess is specified in the `init_pytess.json` file:

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

Note that the service rate of applications vary in a small range, instead of a constant. make sure to have the lowest estimated service rate as redundancy for the best performance.

### Running the LASSY Script

Change the theta for different percentage of the tail latency, here the preset is 99% percentile (P99)

```python
theta = 0.99
```

To run the LASSY script, use the following command:

```bash
python LASSY.py
```
