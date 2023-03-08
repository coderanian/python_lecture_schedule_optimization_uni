import pandas as pd
from gurobipy import *
import networkx as nx


def solve(full_path_instance):
    df = pd.read_csv(full_path_instance, header=None)

    for i in df.index:
        if "Days" in df.loc[i, 0]:
            num_days = int(df.loc[i, 0][-1].split()[-1])
        elif "Periods_per_day" in df.loc[i, 0]:
            num_periods = int(df.loc[i, 0][-1].split()[-1])
        elif "COURSES" in df.loc[i, 0]:
            c = i
        elif "ROOMS" in df.loc[i, 0]:
            r = i
        elif "UNAVAILABILITY_CONSTRAINTS" in df.loc[i, 0]:
            u = i
        elif "CURRICULA" in df.loc[i, 0]:
            cu = i

    if c + 1 <= r - 1:
        Courses = df.loc[c + 1:r - 1, 0].str.split(expand=True)
        Courses.columns = ["CourseID", "Teacher", "#Lecture", "MinWorkingDays", "#Students"]
        Courses["#Lecture"] = Courses["#Lecture"].astype(int)
        Courses["MinWorkingDays"] = Courses["MinWorkingDays"].astype(int)
        Courses["#Students"] = Courses["#Students"].astype(int)
        Courses.reset_index(inplace=True, drop=True)

    if r + 1 <= cu - 1:
        Rooms = df.loc[r + 1:cu - 1, 0].str.split(expand=True)
        Rooms.columns = ["RoomID", "Capacity"]
        Rooms["Capacity"] = Rooms["Capacity"].astype(int)
        Rooms = Rooms.set_index("RoomID")

    if cu + 1 <= u - 1:
        Curricula = df.loc[cu + 1:u - 1, 0].str.split(n=2, expand=True)
        Curricula.columns = ["CurriculumID", "#Courses", "MemberID"]
        Curricula["#Courses"] = Curricula["#Courses"].astype(int)
        Curricula = Curricula.set_index("CurriculumID")

    Unavailability = pd.DataFrame([], index=Courses["CourseID"], columns=[0])
    if u + 1 <= len(df) - 2:
        temp = df.loc[u + 1:len(df) - 2, 0].str.split(expand=True)
        temp.columns = ["CourseID", "Day", "Day_Period"]
        temp["Day"] = temp["Day"].astype(int)
        temp["Day_Period"] = temp["Day_Period"].astype(int)
        for k in Courses["CourseID"]:
            Unavailability.loc[k, 0] = list(
                (temp.loc[i, "Day"], temp.loc[i, "Day_Period"]) for i in temp.index if temp.loc[i, "CourseID"] == k)
    else:
        Unavailability[0] = list([] for i in range(len(Unavailability)))

    LecturerList = []
    for k in Courses.index:
        if Courses.loc[k, "Teacher"] in LecturerList:
            continue
        else:
            LecturerList.append(Courses.loc[k, "Teacher"])  # Liste aller Dozenten
    # print(LecturerList)
    LecturerAppointments = {}
    for i in LecturerList:
        LecturerAppointments[i] = []
        for k in Courses.index:
            if Courses.loc[k, "Teacher"] == i:
                LecturerAppointments[i].append(
                    k)  # dictionary, keys: Dozenten, values:Liste zugehöriger Verasntaltungen

    conflicts = []
    for k in Courses.index:
        for l in Courses.index:
            if k < l:
                for c in Curricula.index:
                    if Courses.loc[k, "CourseID"] in Curricula.loc[c, "MemberID"] and Courses.loc[l, "CourseID"] in \
                            Curricula.loc[c, "MemberID"]:
                        conflicts.append((l, k))
    conflicts = list(set(conflicts))

    model = Model("timetable")
    model.modelSense = GRB.MINIMIZE

    """Variables"""

    x = {}
    z_unavailability = {}
    working_days = {}
    z_workingdays = {}
    z_lecturer = {}
    z_curricula = {}

    for k in Courses.index:
        for i in range(num_days):
            for j in range(num_periods):
                x[k, i, j] = model.addVar(name="x_%s_(%s,%s)" % (Courses.loc[k, "CourseID"], i, j), vtype="B")

    for k in Courses.index:
        for i in range(num_days):
            for j in range(num_periods):
                if (i, j) in Unavailability.loc[Courses.loc[k, "CourseID"], 0]:
                    z_unavailability[k, i, j] = model.addVar(
                        name="z_unavailability_%s_%s,%s" % (Courses.loc[k, "CourseID"], i, j), vtype="B", obj=10)

    for k in Courses.index:
        for i in range(num_days):
            working_days[k, i] = model.addVar(name="working_days_%s_%s" % (Courses.loc[k, "CourseID"], i), vtype="B")

    for k in Courses.index:
        z_workingdays[k] = model.addVar(name="z_workingdays_%s" % (Courses.loc[k, "CourseID"]), vtype="I", obj=0.1)

    for k, l in conflicts:
        for i in range(num_days):
            for j in range(num_periods):
                z_curricula[k, l, i, j] = model.addVar(
                    name="z_curricula_(%s,%s)_(%s,%s)" % (Courses.loc[k, "CourseID"], Courses.loc[l, "CourseID"], i, j),
                    vtype="B", lb=0, obj=0.1)

    for n in LecturerList:
        for i in range(num_days):
            for j in range(num_periods):
                z_lecturer[n, i, j] = model.addVar(name="z_lecturer_(%s)_(%s,%s)" % (n, i, j), vtype="I", lb=0, obj=1)

    """Constraints"""

    for k in Courses.index:
        model.addConstr(
            quicksum(x[k, i, j] for i in range(num_days) for j in range(num_periods)) == Courses.loc[k, "#Lecture"],
            name="Anzahl_Lectures_%s" % (Courses.loc[k, "CourseID"]))

    for k in Courses.index:
        model.addConstr(
            quicksum(working_days[k, i] for i in range(num_days)) >= Courses.loc[k, "MinWorkingDays"] - z_workingdays[
                k], name="MinWorkingDays_%s" % (Courses.loc[k, "CourseID"]))

    for k in Courses.index:
        for i in range(num_days):
            model.addConstr(quicksum(x[k, i, j] for j in range(num_periods)) >= working_days[k, i],
                            name="linkingUb_x_working_days_%s_%s" % (Courses.loc[k, "CourseID"], i))

    for k in Courses.index:
        for i in range(num_days):
            for j in range(num_periods):
                if (i, j) in Unavailability.loc[Courses.loc[k, "CourseID"], 0]:
                    model.addConstr(x[k, i, j] <= z_unavailability[k, i, j],
                                    name="unavailability_%s_%s,%s" % (Courses.loc[k, "CourseID"], i, j))

    for k, l in conflicts:
        for i in range(num_days):
            for j in range(num_periods):
                model.addConstr(x[k, i, j] + x[l, i, j] - 1 <= z_curricula[k, l, i, j],
                                name="doppelt_curriculum_%s,%s_%s,%s" % (Courses.loc[k, "CourseID"], l, i, j))

    for n in LecturerList:
        for i in range(num_days):
            for j in range(num_periods):
                if len(LecturerAppointments[n]) > 0:
                    model.addConstr(quicksum(x[k, i, j] for k in LecturerAppointments[n]) - 1 <= z_lecturer[n, i, j],
                                    name="Teacher_Concurrent_Appointments_(%s,%s)_%s" % (i, j, n))

    """                            
    model.setObjective(quicksum(0.1*z_workingdays[k]
                                +quicksum(10*z_unavailability[k,i,j] for i in range(num_days) for j in range(num_periods)  if (i,j) in Unavailability.loc[Courses.loc[k,"CourseID"],0])
                                +quicksum(0.1*z_curricula[k,l,i,j] for l in Courses.index if k < l for i in range(num_days) for j in range(num_periods))
                                for k in Courses.index)
                       +quicksum(1*z_lecturer[n,i,j] for n in LecturerList for i in range(num_days) for j in range(num_periods)))
    """

    model.update()

    """Callback"""

    model.params.LazyConstraints = 1

    G = nx.DiGraph()
    G.add_node("s")
    G.add_nodes_from(Courses.index)
    G.add_nodes_from(Rooms.index)
    G.add_node("t")

    G.add_edges_from([(r, "t") for r in Rooms.index], capacity=1)
    G.add_edges_from([("s", k) for k in Courses.index])

    def room_constraint(model, where):
        if where == GRB.Callback.MIPSOL:
            rel = model.cbGetSolution(x)

            found = False
            for i in range(num_days):
                if found:
                    break
                for j in range(num_periods):

                    # Construct Graph
                    for k in Courses.index:
                        for r in Rooms.index:

                            if Rooms.loc[r, "Capacity"] >= Courses.loc[k, "#Students"]:
                                G.add_edge(k, r, capacity=1)

                        G.edges[("s", k)]["capacity"] = round(rel[k, i, j])

                    flow = int(nx.maximum_flow_value(G, "s", "t"))

                    # Halls Marriage
                    if sum(round(rel[k, i, j]) for k in Courses.index) > flow:
                        for l in range(num_days):
                            for m in range(num_periods):
                                model.cbLazy(
                                    quicksum(x[k, l, m] for k in Courses.index if round(rel[k, i, j]) == 1) <= flow)
                        found = True
                        break

    model.optimize(room_constraint)

    """
    def print_solution():
        if model.Status == 2:
            df = pd.DataFrame(index=Courses["CourseID"])
            for k in Courses.index:
                df.loc[Courses.loc[k,"CourseID"],"x"]= str(list((i,j) for i in range(num_days) for j in range(num_periods) if x[k,i,j].x == 1))
                df.loc[Courses.loc[k,"CourseID"],"MinWorkingdays/z/workingdays"]= str([Courses.loc[k, "MinWorkingDays"], z_workingdays[k].x, list(i for i in range(num_days) if working_days[k,i].x==1)])
                df.loc[Courses.loc[k,"CourseID"],"num_lectures"] = Courses.loc[k,"#Lecture"]
                df.loc[Courses.loc[k,"CourseID"], "unavailability"] = str(Unavailability.loc[Courses.loc[k,"CourseID"],0])
                df.loc[Courses.loc[k,"CourseID"], "z_unavailability"] = str(list((i,j) for i in range(num_days) for j in range(num_periods) if (i,j) in [Unavailability.loc[Courses.loc[k,"CourseID"],0]] if z_unavailability[k,i,j].x == 1))
                                                                                                
            df.to_csv("./df.csv")
            
            import matplotlib.pyplot as plt
            
            for i in range(num_days):
                for j in range(num_periods):
                    
                    G= nx.DiGraph()
                    G.add_node("s")
                    G.add_nodes_from(Courses.index)
                    G.add_nodes_from(Rooms.index)
                    G.add_node("t")

                    for k in Courses.index:
                        for r in Rooms.index:       
                            if Rooms.loc[r,"Capacity"] >= Courses.loc[k,"#Students"]:
                                G.add_edge(k, r, capacity=1)

                    G.add_edges_from([(r,"t") for r in Rooms.index], capacity=1)
                    G.add_edges_from([("s",k) for k in Courses.index])
                    for k in Courses.index:
                        G.edges[("s",k)]["capacity"] = x[k,i,j].x
                        
                    pos={}
                    pos["s"]= (len(Courses)/2, 0)
                    pos["t"]= (len(Courses)/2, 3)

                    for k in Courses.index:
                        pos[k]= (k, 1)
                    for r in enumerate(Rooms.index):
                        pos[r[1]]= (r[0]*len(Courses.index)/len(Rooms.index), 2)
                        

                    nx.set_node_attributes(G,pos, "pos")
                    edge_labels = nx.get_edge_attributes(G, "capacity")
                    f, ax = plt.subplots(figsize=(15,5))
                    plt.title("Periode: (%s,%s)"%(i,j))
                    nx.draw_networkx(G, pos, ax=ax, with_labels=True, node_color="#86d46e")
                    nx.draw_networkx_edge_labels(G, pos, edge_labels = edge_labels)
                    plt.savefig("Graph1.svg", format="svg")
            
            #for var in model.getVars():
                #print(var)
         
                            
        model.write("model.lp")
    """
    # print_solution()
    return (model)


solve("dataset5.ctt")
