from gurobipy import *
import timetables as ttable

tests = ["HA_assistants.ctt", "HA_curriculum.ctt", "HA_mindays.ctt", "HA_rooms.ctt", "HA_unavail.ctt"]

res = dict()
for test in tests:
    resmodel = ttable.solve(test)
    if resmodel.status == GRB.OPTIMAL:
        res[test] = resmodel.ObjVal
    else:
        res[test] = "INFEASIBLE"

for key in res.keys():
    print(key, "|", res[key])
    