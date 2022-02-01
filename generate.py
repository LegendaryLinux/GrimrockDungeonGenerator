from lib.DungeonFloor import DungeonFloor

floor = DungeonFloor(1)

for row in floor.floor_grid:
    output = ""
    for col in row:
        output += ("X " if col else "- ")

    print(output)

