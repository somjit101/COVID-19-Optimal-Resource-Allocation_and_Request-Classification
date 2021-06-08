import xlrd
from ortools.sat.python import cp_model
from ortools.linear_solver import pywraplp
from itertools import product
from flask import Flask, jsonify, Response
from flask_cors import CORS
import mpu

import os


# read data

def read_data(path):
    names, coords, supply, demand = [], [], [], []
    wb = xlrd.open_workbook(path)
    sheet = wb.sheet_by_index(0)
    for i in range(1, sheet.nrows):
        names.append(sheet.cell_value(i, 0))
        supply.append(sheet.cell_value(i, 1))
        demand.append(sheet.cell_value(i, 2))
        coords.append((sheet.cell_value(i, 3), sheet.cell_value(i, 4)))
    return names, coords, supply, demand


def get_target_values(supply, demand, node=None):
    adjusted_supply = [s - min(d, s) for s, d in zip(supply, demand)]
    adjusted_demand = [d - min(d, s) for s, d in zip(supply, demand)]

    supply_sum = float(sum(adjusted_supply))
    demand_sum = float(sum(adjusted_demand))
    # short, target = sorted(supply_tup, demand_tup, key=lembda l: l[1])
    supply_ratio = min(demand_sum / supply_sum, 1.0)

    if node and adjusted_demand[node] <= supply_sum:
        demand_ratio = min((supply_sum - adjusted_demand[node]) / (demand_sum - adjusted_demand[node]), 1.0)
    else:
        demand_ratio = min(supply_sum/demand_sum, 1.0)


    sources = [s * supply_ratio for s in adjusted_supply]
    targets = [d * demand_ratio for d in adjusted_demand]
    if node: targets[node] = adjusted_demand[node]

    return sources, targets


# %%
# prepare distance_matrix
# sources, targets = get_target_values(supply, demand, 2)
# distance_matrix = {(i, j): dist, .. }
# distance_matrix = [[1 for s in sources] for t in targets]
# print (sources)
# print (targets)


# %%
# Contraints

# model = cp_model.CpModel()
def buid_optimization_model(sources, targets, distance_matrix):
    solver = pywraplp.Solver('ResourceAllocation', pywraplp.Solver.GLOP_LINEAR_PROGRAMMING)
    # sources, targets = get_target_values(supply, demand)

    source_upper_bound = max(sources)
    target_upper_bound = max(targets)

    transfers = {}
    # bin_transfers = {}

    for i, j in product(range(len(sources)), range(len(targets))):
        transfers[(i, j)] = solver.NumVar(0, int(source_upper_bound) + 1, 'transfer_%i_to_%i' % (i, j))

    # bin_transfers[(i, j)] = model.NewIntVar(0, 1, 'bin_transfer_%i_to_%i' % (i,j))
    # model.Add(bin_transfers[(i, j)] <= transfers[(i, j)])
    # model.Add(bin_transfers[(i, j)] * int(source_upper_bound) >= transfers[(i, j)])
    cons1 = {}
    cons2 = {}
    for i in range(len(sources)):
        cons1[i] = solver.Constraint(sources[i], sources[i])
        cons2[i] = solver.Constraint(targets[i], targets[i])
        for j in range(len(targets)):
            cons1[i].SetCoefficient(transfers[(i, j)], 1)
            cons2[i].SetCoefficient(transfers[(j, i)], 1)
    # model.Add(sources[i] >= sum(transfers[(i, j)] for j in range(len(sources))))
    # model.Add(targets[i] <= sum(transfers[(j, i)] for j in range(len(sources))))

    # objective function
    objective = solver.Objective()

    for i in range(len(sources)):
        for j in range(len(targets)):
            objective.SetCoefficient(transfers[(i, j)], distance_matrix[i][j])

    solver.Solve()

    result = {}
    for i, j in product(range(len(sources)), range(len(targets))):
        result[(i, j)] = transfers[(i, j)].solution_value()

    return result


# %%

# optimizer

# %%
# postprocess


app = Flask(__name__)
CORS(app)
cf_port = os.getenv("PORT")


# Only get method by default
@app.route('/')
def WelcomeScreen():
    return 'Hi ! Welcome to COVID19 Resource Allocation Optimizer by SAP'


@app.route('/display', defaults={'resource': None}, methods=['GET'])
@app.route('/display/<resource>', methods=['GET'])
def display(resource):
    path = 'Food_Allocation.xlsx'
    names, coords, supply, demand = read_data(path)
    # sources, targets = get_target_values(supply, demand)
    nodes_list = [{'nodeID': i, 'nodeName': names[i], 'lat': coords[i][0], 'long': coords[i][1], 'supply': supply[i],
                   'demand': demand[i]} for i in range(len(names))]
    return jsonify({'nodes': nodes_list})


@app.route('/optimize', defaults={'nodeID': None}, methods=['GET'])
@app.route('/optimize/<nodeID>', methods=['GET'])
def ResourceOptimizer(nodeID=None):
    # Logic Body
    #
    if nodeID != None:
        nodeID = int(nodeID)

    path = 'Food_Allocation.xlsx'
    names, coords, supply, demand = read_data(path)
    sources, targets = get_target_values(supply, demand, node=nodeID)
    distance_matrix = [[mpu.haversine_distance(coords[s], coords[t]) for s in range(len(sources))] for t in range(len(targets))]
    # print (distance_matrix)
    result = buid_optimization_model(sources, targets, distance_matrix)
    #
    # End Body

    transferList = []
    postTransferDeficit = [d - min(d, s) for s, d in zip(supply, demand)]

    # transferList = [{'source': i, 'target': j, 'quantity': result[(i, j)]} for (j, i) in
    #                 product(range(len(sources)), range(len(targets))) if result[(i, j)] > 0]

    if(nodeID == None): ######### No Focus Node specified

        for (j, i) in product(range(len(sources)), range(len(targets))):
            if round(result[(i, j)]) > 0:
                postTransferDeficit[j] -= round(result[(i, j)])
                transferList.append({'source': i, 'target': j, 'quantity': round(result[(i, j)]),
                                     'currentDeficit': postTransferDeficit[j]} )


    else: ######## Focus Node specified

        for i in range(len(sources)):
            if(round(result[(i, nodeID)]) > 0):
                postTransferDeficit[nodeID] -= round(result[(i, nodeID)])
                transferList.append({'source': i, 'target': nodeID, 'quantity': round(result[(i, nodeID)]),
                                     'currentDeficit': postTransferDeficit[nodeID]} )


        for (j, i) in product(range(len(sources)), range(len(targets))):
            if (round(result[(i, j)]) > 0 and j != nodeID):
                postTransferDeficit[j] -= round(result[(i, j)])
                transferList.append({'source': i, 'target': j, 'quantity': round(result[(i, j)]),
                                     'currentDeficit': postTransferDeficit[j]} )


    return jsonify({'itemTransfers': transferList})


if __name__ == '__main__':
    if cf_port is None:
        app.run(host='0.0.0.0', port=5002, debug=True)
    else:
        app.run(host='0.0.0.0', port=int(cf_port), debug=True)

