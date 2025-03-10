import math
from gurobipy import Model, GRB
import scipy.optimize as spo
import os
import sys
import json
from decimal import Decimal, getcontext
from datetime import datetime

###################
# Queueing time distribution
###################

# P(waiting time <= t) for an instance arrival rate lm
def waitingTimeDistr(t, lm): 
    mu = service_rate
    if lm>=mu:
        return 0.0
    if lm<=0:
        return 1.0
    
    ## Old version, not numerically stable
    # s = 0
    # for i in range(int(t*mu)):
        # s = s + math.exp(-lm*(i/mu-t)) * pow(i/mu-t,i) * pow(lm,i) / math.factorial(i)
    # return (1-lm/mu)*s
    
    getcontext().prec = 80
    s = Decimal(0)
    dlm = Decimal(lm)
    dmu = Decimal(mu)
    dt = Decimal(t)
    for i in range(int(t*mu)+1):
        di = Decimal(i)
        t1 = di / dmu - dt
        f1 = Decimal.exp(-dlm*t1)
        f2 = t1 ** di
        f3 = dlm ** di
        f4 = math.factorial(i)
        s = s + f1 * f2 * f3 / f4    
    return float( (Decimal(1)-dlm/dmu) * s )


script_dir = os.path.dirname(os.path.realpath(__file__))

# Path to the JSON file
json_file = os.path.join(script_dir, 'input/init_pytess.json')

# Load the JSON file
with open(json_file, 'r') as f:
    data = json.load(f)


sites = data["nodes"]
pricing = data["pricing"] # price per instance on each site
users = data["users"]
capacities = data["capacities"]
latency_node_user = {(i, j): data["latency_node_user"][f"('{i}', '{j}')"] for i in sites for j in users}
service_rate = data["service_rate"] # req/ms
# request_rate = data["rps"] / 1e3  # req/ms
slo = data["slo"]  # ms
deployment_name = data["deployment_name"]
opti_pref = data["opti_pref"]
arrivalRateOfUser = data["request_rates"] # req/ms


theta = 0.99

service_time = 1 / service_rate # Service time per instance

# Setup the big-M value00
M = slo + max(latency_node_user.values()) + max(capacities.values()) + 1e6 # Upper bound for the latency

# Initialize the model
model = Model("PlacementPlan")

# Decision variables
x = model.addVars(sites, users, vtype=GRB.BINARY, name="x")  # Assignment of users to sites
y = model.addVars(sites, vtype=GRB.BINARY, name="y")  # Site is open
u = model.addVars(sites, vtype=GRB.INTEGER, name="u")  # Number of users per site

arrivalRateFromUserToSite = model.addVars(sites, users, vtype=GRB.CONTINUOUS, name="arrivalRateFromUserToSite")  # arrival rate from user to site
instance_per_site = model.addVars(sites, vtype=GRB.INTEGER,name="instance_per_site") # Number of instances per site
instance_arrival_rate = model.addVars(sites, vtype=GRB.CONTINUOUS, name="utilization") # Arrival rate at instance
response_time = model.addVars(sites, vtype=GRB.CONTINUOUS, name="response_times") # Response time per site
queuing_time = model.addVars(sites, vtype=GRB.CONTINUOUS, name="queuing_time") # Queuing time per site
rtt = model.addVars(sites, users, lb=-M, vtype=GRB.CONTINUOUS, name="rtt") # Round trip time

###################
if opti_pref == 1:
# # Objective: Minimize the number of open sites
    model.setObjective(y.sum(), GRB.MINIMIZE)
elif opti_pref == 2:
# Objective: Minimize the number of instances
    model.setObjective(instance_per_site.sum(), GRB.MINIMIZE)
elif opti_pref == 3:
# Objective: Minimize the latency
    model.setObjective(rtt.sum(), GRB.MINIMIZE)
else:
    print("No optimization preference selected.")
    sys.exit(1)
##################





# This gives the maximum total lambda that an instance at a specific site
# can receive without breaking the SLO of one of the users (assuming that
# the user sends their requests to this site)
lambdaLimits = { i: { j: spo.brentq(lambda lm: waitingTimeDistr(slo-latency_node_user[i,j]-service_time, lm)-theta, 0.0, service_rate) for j in users } for i in sites }


###################
  # Constraints #
###################

# Each user is assigned to exactly one site
model.addConstrs((x.sum('*', j) == 1 for j in users), name="assignToOne")

# Users can only be linked to the open sites
model.addConstrs((x[i, j] <= y[i] for i in sites for j in users), name="linkToOpen")

# Capacity constraints: number of instance shouldn't be bigger than the number of slots
model.addConstrs((instance_per_site[i] * y[i] <= capacities[i] for i in sites), name="capacity")
# If a site is open, it should have at least one instance deployed
model.addConstrs((instance_per_site[i] >= y[i] for i in sites), name="atLeastOneInstanceIfOpen")

# Number of users per site
model.addConstrs((u[i] == x.sum(i, '*') for i in sites), name="numUsers")

# Enforce instance arrival rate
#model.addConstrs((instance_arrival_rate[i] * instance_per_site[i] == u[i] * request_rate for i in sites), name="instance_arrival_rate")

model.addConstrs((arrivalRateFromUserToSite[i,j] == x[i,j]*arrivalRateOfUser[j] for i in sites for j in users), name="user_site_arrival_rate")

model.addConstrs((instance_arrival_rate[i] * instance_per_site[i] == arrivalRateFromUserToSite.sum(i,'*') for i in sites), name="instance_arrival_rate")

# Enforce maximum lambda
for j in users:
    for i in sites:
        model.addConstr(x[i, j] * instance_arrival_rate[i] <= lambdaLimits[i][j], name="lambdaMax")

# Optimize the model
model.optimize()

# Print the optimal solution
print("------------------------------------------")
if model.status == GRB.OPTIMAL:
    print("Model parameters are:")
    print(f"  Instance service rate: {service_rate} requests/s")
    print(f"  SLO RTT: {slo} ms")
    print(f"  SLO theta: {theta*100}%")
    print("Optimal solution found:")
    for i in sites:
        if y[i].X > 0.5:
            rho = instance_arrival_rate[i].X / service_rate
            print(f"Node {i} is open with {math.ceil(instance_per_site[i].X)} instances deployed and {u[i].X} users assigned.")
            print(f"  Arrival rate at instances of this site is {instance_arrival_rate[i].X}")
            print(f"  Utilization of instances of this site is {rho}")
            for j in users:
                if x[i,j].X > 0.5:                    
                    rtt = latency_node_user[i,j] + service_time + rho/(2*service_rate*(1-rho))
                    perc = spo.brentq(lambda t: waitingTimeDistr(t-latency_node_user[i,j]-service_time, instance_arrival_rate[i].X)-theta, 0, slo+1)                                    
                    print(f"  User {j} for site: {i}, with average RTT {rtt} and {theta*100}% percentile {perc}.")
                    print(f"    Probability that the requests of this user will stay below the SLO-RTT: {waitingTimeDistr(slo, instance_arrival_rate[i].X)}")
                    
        else:
            print(f"Node {i} is closed.")
else:
    print("No optimal solution found.")


