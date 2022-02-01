class DungeonTile:
    # Info
    is_alcove = None
    is_connector = None
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

    def __init__(self, is_alcove: bool):
        self.is_alcove = is_alcove
