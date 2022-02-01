import unittest
from lib.DungeonFloor import DungeonFloor


class TestDungeonFloor(unittest.TestCase):
    def test_floor_size(self):
        floor = DungeonFloor()
        self.assertEqual(len(floor.floor_grid), 32, f"Invalid row count in floor: {len(floor.floor_grid)}")

        for col in floor.floor_grid:
            self.assertEqual(len(col), 32, f"Invalid column count {col} in floor: {len(col)}")
