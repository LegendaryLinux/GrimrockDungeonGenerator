import logging
import random

from lib.DungeonRoom import DungeonRoom
from lib.DungeonTile import DungeonTile


class DungeonFloor:
    TOTAL_AREA = 32 * 32
    MIN_ROOMS = 10
    MAX_ROOMS = 18

    floor_number = None
    floor_grid = []
    rooms = {}
    tiles = {}

    def __init__(self, floor_number: int):
        # Generate the initial empty floor grid
        for x in range(0, 32):
            self.floor_grid.append([])
            for y in range(0, 32):
                self.floor_grid[x].append(None)

        # Determine the number of desired rooms on this floor
        room_count = random.randint(self.MIN_ROOMS, self.MAX_ROOMS)

        # Create rooms
        remaining_area = self.TOTAL_AREA * .75  # Leave room for connectors, alcoves, secrets, etc
        for room in range(0, room_count):
            # Determine how large this room will be
            room_width = random.randint(2, 8)
            room_height = random.randint(2, 8)
            alcove_size = random.randint(1, 2) if (random.randint(1, 100) < 26) else 0
            room_area = (room_width * room_height) + alcove_size

            # If there is not enough area for more rooms, don't add any more rooms
            if room_area > remaining_area:
                continue

            # Find available space on the floor and place the room
            create_room_args = self.determine_room_placement(room_width, room_height, alcove_size)

            # Occasionally the generator may create a room layout which is highly inefficient in its use of space.
            # In these cases, we simply do skip placing this room
            if create_room_args is None:
                print(f"Unable to place room with dimensions ({room_width}, {room_height}) on floor {floor_number}.")
                continue

            # Save tiles, save room, reduce the remaining area
            new_room = self.create_room(*create_room_args)
            self.rooms[new_room.room_id] = new_room
            remaining_area -= room_area

        # TODO: Connect all rooms with paths or teleporters

    def determine_room_placement(self, width: int, height: int, alcove_size: int):
        # Effective width and height of the room. If an alcove is present, either may be increased to ensure
        # enough room is reserved for the alcove to be placed
        effective_width = width
        effective_height = height

        # If an alcove is present in this room, expand the effective size of the room. Start by determining
        # whether the alcove will be vertical or horizontal
        alcove_placement = None  # None= no alcove, 1 = width expanded, 2 = height expanded
        if alcove_size > 0:
            alcove_placement = 1 if (random.randint(0, 1)) else 2

        # Perform the boundary expansion
        if alcove_placement == 1:
            effective_width += 1

        if alcove_placement == 2:
            effective_height += 1

        # Pick a random starting point on the grid where it might be possible to place this room.
        # If the room can be placed in that location, place it there. Attempt this random placement twenty-five times.
        for i in range(1, 26):
            x_pos = random.randint(0, 31 - effective_width)
            y_pos = random.randint(0, 31 - effective_height)

            # If the placement is valid, update the floor_grid and return lists of occupied spaces
            if self.validate_room_placement(x_pos, y_pos, effective_width, effective_height):
                return x_pos, y_pos, width, height, alcove_placement, alcove_size

        # After ten random placement attempts, scan the floor starting at the top left until a valid placement
        # is located
        for x in range(0, 32 - width):
            for y in range(0, 32 - height):
                if self.validate_room_placement(x, y, effective_width, effective_height):
                    return x, y, width, height, alcove_placement, alcove_size

        # It is possible for the generator to create a layout with highly inefficient space usage, causing a lot
        # of area to be available, but not in such a way as it can be used.
        return None

    def validate_room_placement(self, x_pos, y_pos, width, height):
        # Determine the range of x and y coordinates which must pass validation
        x_bounds = (x_pos, x_pos + (width - 1))
        y_bounds = (y_pos, y_pos + (height - 1))

        # Loop over each grid and determine if the space is a valid space for a new room to occupy
        for x in range(x_bounds[0], x_bounds[1] + 1):
            for y in range(y_bounds[0], y_bounds[1] + 1):
                # If any desired space is occupied by another room, validation fails
                if self.floor_grid[x][y] is not None:
                    return False

                # If this is a room border, all adjacent squares must also be unoccupied
                if x == x_pos or y == y_pos or x == x_bounds[1] or y == y_bounds[1]:
                    # Check left
                    if x > 0 and self.floor_grid[x - 1][y] is not None:
                        return False

                    # Check right
                    if x < 31 and self.floor_grid[x + 1][y] is not None:
                        return False

                    # Check top
                    if y > 0 and self.floor_grid[x][y - 1] is not None:
                        return False

                    # Check bottom
                    if y < 31 and self.floor_grid[x][y + 1] is not None:
                        return False

        return True

    def create_room(self, x_pos: int, y_pos: int, width: int, height: int, alcove_placement: int, alcove_size: int):
        logging.debug(f"Placing room with size ({height}, {width}) at [{y_pos}, {x_pos}] with alcove size" +
                      " {alcove_size}, placement {alcove_placement}.")
        occupied_tiles = []
        for x in range(x_pos, x_pos + width):
            for y in range(y_pos, y_pos + height):
                occupied_tiles.append([x, y])

        # TODO: Allow alcoves to be placed on left and top of rooms

        # Place the alcove in the expanded width
        if alcove_placement == 1:
            alcove_x = x_pos + width
            alcove_y = random.randint(y_pos, y_pos + height - alcove_size)
            for i in range(alcove_y, alcove_y + alcove_size):
                occupied_tiles.append([alcove_x, i])

        # Place the alcove in the expanded height
        if alcove_placement == 2:
            alcove_x = random.randint(x_pos, x_pos + width - alcove_size)
            alcove_y = y_pos + height
            for i in range(alcove_x, alcove_x + alcove_size):
                occupied_tiles.append([i, alcove_y])

        new_room = DungeonRoom(self.floor_number, occupied_tiles)

        for tile in occupied_tiles:
            new_tile = DungeonTile(new_room.room_id)
            self.floor_grid[tile[0]][tile[1]] = new_tile.tile_id
            self.tiles[new_tile.tile_id] = new_tile

        return new_room
