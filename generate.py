from lib.DungeonFloor import DungeonFloor

floor = DungeonFloor(1)

for row in floor.floor_grid:
    output = ""
    for col in row:
        tile = floor.tiles[col] if col else None
        output += ("O " if (tile and tile.is_connector) else ("X " if tile else "- "))

    print(output)

