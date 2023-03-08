import pandas as pd
from gurobipy import *


df = pd.read_csv("dataset5.ctt", header=None, on_bad_lines='skip')

for i in df.index:
    if "Days" in df.loc[i,0]:
        num_days = int(df.loc[i,0][-1].split()[-1])
    elif "Periods_per_day" in df.loc[i,0]:
        num_periods = int(df.loc[i,0][-1].split()[-1])               
    elif "COURSES" in df.loc[i,0]:
        c = i
    elif "ROOMS" in df.loc[i,0]:
        r = i
    elif "UNAVAILABILITY_CONSTRAINTS" in df.loc[i,0]:
        u = i
    elif "CURRICULA" in df.loc[i,0]:
        cu = i

if c+1 <= r-1:
    Courses= df.loc[c+1:r-1,0].str.split(expand=True)
    Courses.columns= ["CourseID","Teacher","#Lecture","MinWorkingDays","#Students"]
    Courses["#Lecture"]= Courses["#Lecture"].astype(int)
    Courses["MinWorkingDays"]= Courses["MinWorkingDays"].astype(int)
    Courses["#Students"]= Courses["#Students"].astype(int)
    Courses.reset_index(inplace=True, drop=True)

if r+1 <= cu-1:
    Rooms= df.loc[r+1:cu-1,0].str.split(expand=True)
    Rooms.columns= ["RoomID", "Capacity"]
    Rooms["Capacity"]= Rooms["Capacity"].astype(int)
    Rooms = Rooms.set_index("RoomID")

if cu+1 <= u-1:
    Curricula= df.loc[cu+1:u-1,0].str.split(n=2, expand=True)
    Curricula.columns= ["CurriculumID","#Courses","MemberID"]
    Curricula["#Courses"]= Curricula["#Courses"].astype(int)
    Curricula = Curricula.set_index("CurriculumID")

Unavailability=pd.DataFrame([], index=Courses["CourseID"], columns=[0])
if u+1 <= len(df)-2:
    temp= df.loc[u+1:len(df)-2,0].str.split(expand=True)
    temp.columns= ["CourseID", "Day", "Day_Period"]
    temp["Day"]= temp["Day"].astype(int)
    temp["Day_Period"]= temp["Day_Period"].astype(int)
    for k in Courses["CourseID"]:
        Unavailability.loc[k,0] = list((temp.loc[i,"Day"],temp.loc[i,"Day_Period"]) for i in temp.index if temp.loc[i,"CourseID"]==k)
else:
    Unavailability[0] = [[] for i in range(len(Unavailability))]

    
    
import networkx as nx
import matplotlib.pyplot as plt


    
G= nx.DiGraph()
G.add_node("s")
G.add_nodes_from(Courses.index)
G.add_nodes_from(Rooms.index)
G.add_node("t")

for k in Courses.index:
    for r in Rooms.index:       
        if Rooms.loc[r,"Capacity"] >= Courses.loc[k,"#Students"]:

            G.add_edge(k, r, Capacity=1)

G.add_edges_from([(r,"t") for r in Rooms.index], Capacity=1)
G.add_edges_from([("s",k) for k in Courses.index])          


pos={}
pos["s"]= (len(Courses)/2, 0)
pos["t"]= (len(Courses)/2, 3)

for k in Courses.index:
    pos[k]= (k, 1)
for r in enumerate(Rooms.index):
    pos[r[1]]= (r[0]*len(Courses.index)/len(Rooms.index), 2)
    

nx.set_node_attributes(G,pos, "pos")
edge_labels = nx.get_edge_attributes(G, "Capacity")
f, ax = plt.subplots(figsize=(30,10))
nx.draw_networkx(G, pos, ax=ax, with_labels=True, node_color="#86d46e")
nx.draw_networkx_edge_labels(G, pos, edge_labels = edge_labels)
plt.savefig("Graph1.svg", format="svg")
            

    
  
    
  
    
  
    
  