from lib.HelperMethods import generate_id


class DungeonRoom:
    room_id = None
    floor_number = None
    occupied_tiles = None

    connected = None

    def __init__(self, floor_number: int, occupied_tiles: list):
        self.room_id = generate_id()
        self.floor_number = floor_number
        self.occupied_tiles = occupied_tiles

    def set_connected(self, connected: bool):
        self.connected = connected
