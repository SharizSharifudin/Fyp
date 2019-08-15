import os
import sys
import time
from xml.dom import minidom as md

from ACO import ACO, Graph
from random import randint

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Missing SUMO_HOME env var!")

sumoGui = "sumo-gui"
sumoCmd = [sumoGui, "-c", "../maps/kt2.sumocfg"]

import traci
import traci.constants as tc


def main():
    xmldoc = md.parse('../maps/kt2.net.xml')

    find_junction = xmldoc.getElementsByTagName('junction')
    find_edge = xmldoc.getElementsByTagName('edge')

    edge_num = len(find_edge)
    check = bool
    count = 0

    junc_list, from_node, to_node, edge_list = insertIntoList(
        find_junction, edge_num, find_edge)

    rank = len(junc_list)

    traci.start(sumoCmd)

    step = 0
    end = "e40"
    weight_list = []

    '''while step < 1:
        for i in range(len(edge_list)):
            weight = traci.edge.getTraveltime(edge_list[i])
            weight_list.append(weight)
        step += 1
        traci.simulationStep()'''

    while traci.simulation.getMinExpectedNumber() > 0:
        if step == 70:
            for i in range(len(edge_list)):
                weight = traci.edge.getTraveltime(edge_list[i])
                weight_list.append(weight)

            cost_matrix = createMatrix(
                junc_list, from_node, to_node, weight_list, check)

            aco = ACO(5, 100, 0.6, 0.4, 0.3, 10)
            graph = Graph(cost_matrix, rank)
            path, cost = aco.solve(graph)

            route = createRoute(path, junc_list)
            edge = selectEdges(edge_num, find_edge, route, count)

            traci.route.add("optRoute", edge)
            traci.vehicle.add('veh0', "optRoute", typeID='DEFAULT_VEHTYPE')
            traci.vehicle.setColor('veh0', (255, 0, 0))
            # traci.vehicle.setRoute('veh0', edge)

            while traci.simulation.getMinExpectedNumber() > 0:

                if "veh0" in traci.simulation.getArrivedIDList():
                    break
                traci.simulationStep()
            break

        step += 1
        traci.simulationStep()

    traci.close()

    display(cost, route, edge)
    # print(weight_list)


def insertIntoList(find_junction, edge_num, find_edge):
    Junction = []
    From = []
    To = []
    Edge = []
    for i in range(len(find_junction)):
        if len(find_junction[i].attributes['id'].value) <= 3:
            Junction.append(find_junction[i].attributes['id'].value)

    for i in range(edge_num):
        if find_edge[i].attributes['id'].value.startswith("e"):
            From.append(find_edge[i].attributes['from'].value)
            To.append(find_edge[i].attributes['to'].value)
            Edge.append(find_edge[i].attributes['id'].value)

    return Junction, From, To, Edge


def createMatrix(junc_list, from_node, to_node, weight_list, check):
    Matrix = []
    for i in junc_list:
        row = []
        for j in junc_list:
            for x, y, w in zip(from_node, to_node, weight_list):
                if x == i and y == j:
                    row.append(float(w))
                    check = True
                    break
                else:
                    check = False

            if check == True:
                pass
            else:
                row.append(0.0)
        Matrix.append(row)
    return Matrix


def createRoute(path, junc_list):
    Route = []
    for p in path:
        Route.append(junc_list[p])
    return Route


def selectEdges(edge_num, find_edge, route, count):
    Edge = []
    for i in range(edge_num):
        if find_edge[i].attributes['id'].value.startswith("e"):
            try:
                if route[count] == find_edge[i].attributes['from'].value and route[count + 1] == find_edge[i].attributes['to'].value:
                    Edge.append(find_edge[i].attributes['id'].value)
                    count += 1
            except IndexError:
                pass
    return Edge


def display(cost, route, edge):
    print(f"Cost is : {cost}\n")
    print(f"Path is : {route} through edges {edge}")


if __name__ == '__main__':
    main()
