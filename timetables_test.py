from pathlib import Path
from gurobipy import *
import unittest
import timetables as tt


def assertCloseTo(x, y):
    assert (
        abs(x - y) < 1e-6
    ), f"expected {x} (actual value) to be close to {y} (expected value)"


class TestInstances(unittest.TestCase):
    path = Path(__file__).parent

    def test01(self):
        print("=== test01.ctt ===")
        model = tt.solve(self.path / "./data/test01.ctt")
        assert model.status == GRB.OPTIMAL
        assertCloseTo(model.ObjVal, 2)

    def test02(self):
        print("=== test02.ctt ===")
        model = tt.solve(self.path / "./data/test02.ctt")
        assert model.status == GRB.OPTIMAL
        assertCloseTo(model.ObjVal, 0.2)

    def test03(self):
        print("=== test03.ctt ===")
        model = tt.solve(self.path / "./data/test03.ctt")
        assert model.status == GRB.OPTIMAL
        assertCloseTo(model.ObjVal, 0.3)

    def test04(self):
        print("=== test04.ctt ===")
        model = tt.solve(self.path / "./data/test04.ctt")
        assert model.status == GRB.OPTIMAL
        assertCloseTo(model.ObjVal, 11.1)

    def test05(self):
        print("=== test05.ctt ===")
        model = tt.solve(self.path / "./data/test05.ctt")
        assert (
            model.status == GRB.INFEASIBLE
        ), f"model should be infeasible but has optimal solution {model.ObjVal}"


if __name__ == "__main__":
    unittest.main()
