from lib.HelperMethods import generate_id


class DungeonTile:
    tile_id = None
    room_id = None

    # Info
    has_pitfall = None
    has_stairs = None
    has_teleporter = None

    # Movement
    can_move_north = None
    can_move_south = None
    can_move_east = None
    can_move_west = None
    can_move_up = None
    can_move_down = None

    def __init__(self, room_id: str):
        self.tile_id = generate_id()
        self.room_id = room_id
