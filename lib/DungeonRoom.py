from lib.HelperMethods import generate_id


class DungeonRoom:
    room_id = None
    floor_number = None
    occupied_tiles = None

    is_connected = None
    is_expansive = None

    def __init__(self, floor_number: int, occupied_tiles: list):
        self.room_id = generate_id()
        self.floor_number = floor_number
        self.occupied_tiles = occupied_tiles

    def set_connected(self, is_connected: bool):
        self.is_connected = is_connected

    def set_expansive(self, is_expansive: bool):
        self.is_expansive = is_expansive

    """Delete a tile from the list of occupied tiles"""
    def remove_tile(self, tile_coords: tuple):
        for i in range(len(self.occupied_tiles)):
            if self.occupied_tiles[i][0] == tile_coords[0] and self.occupied_tiles[i][1] == tile_coords[1]:
                del self.occupied_tiles[i]
                return
