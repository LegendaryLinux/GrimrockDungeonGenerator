import unittest
from lib.DungeonFloor import DungeonFloor
from time import time


class TestDungeonFloor(unittest.TestCase):
    def test_floor_size(self):
        floor = DungeonFloor(1)
        self.assertEqual(len(floor.floor_grid), 32, f"Invalid row count in floor: {len(floor.floor_grid)}")

        for col in floor.floor_grid:
            self.assertEqual(len(col), 32, f"Invalid column count {col} in floor: {len(col)}")

    # Generate one thousand floors and make sure they all succeed
    def test_generation_consistency(self, floor_count: int = 10000):
        print(f"Generating {floor_count} floors...")
        start_time = time()

        for i in range(floor_count):
            DungeonFloor(i)

        total_time = time() - start_time

        print(f"Generation completed in {total_time} seconds.")
        print(f"Average generation time per floor: {total_time / floor_count}")
