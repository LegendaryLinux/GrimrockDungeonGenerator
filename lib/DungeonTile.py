from lib.HelperMethods import generate_id


class DungeonTile:
    tile_id = None
    room_id = None

    # Info
    has_pitfall = None
    has_stairs = None
    has_teleporter = None
    is_connector = None
    is_alcove = None

    # Movement
    can_move_north = None
    can_move_south = None
    can_move_east = None
    can_move_west = None
    can_move_up = None
    can_move_down = None

    def __init__(self, room_id: str = None, is_connector: bool = False, is_alcove: bool = False):
        self.tile_id = generate_id()
        self.room_id = room_id
        self.is_connector = is_connector
        self.is_alcove = is_alcove
