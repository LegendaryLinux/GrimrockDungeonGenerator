import unittest
from lib.DungeonFloor import DungeonFloor


class TestDungeonFloor(unittest.TestCase):
    def test_floor_size(self):
        floor = DungeonFloor(1)
        self.assertEqual(len(floor.floor_grid), 32, f"Invalid row count in floor: {len(floor.floor_grid)}")

        for col in floor.floor_grid:
            self.assertEqual(len(col), 32, f"Invalid column count {col} in floor: {len(col)}")

    # Generate fifty thousand floors and make sure they all succeed
    def test_generation_consistency(self):
        for i in range(50000):
            DungeonFloor(i)
