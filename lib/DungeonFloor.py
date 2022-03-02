import logging
import math
import random

from lib.DungeonRoom import DungeonRoom
from lib.DungeonTile import DungeonTile


class DungeonFloor:
    # Shared among all class instances
    TOTAL_AREA = 32 * 32
    MIN_ROOMS = 10
    MAX_ROOMS = 18

    # Instance variables
    floor_number = None
    floor_grid = None
    rooms = None
    tiles = None

    # Debugging data
    last_room_connection_args = None
    last_room_connection_paths = None

    def __init__(self, floor_number: int):
        self.floor_number = floor_number
        self.floor_grid = []
        self.rooms = {}
        self.tiles = {}

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
                logging.debug(f"Unable to place room with dimensions ({room_width}, {room_height}) " +
                              f"on floor {self.floor_number}.")
                continue

            # Save tiles, save room, reduce the remaining area
            new_room = self.create_room(*create_room_args)
            self.rooms[new_room.room_id] = new_room
            remaining_area -= room_area

        # Rooms with twenty or more tiles should have some randomly removed
        for key in tuple(self.rooms.keys()):
            room = self.rooms[key]
            # Only rooms with 20 or more tiles are modified
            if len(room.occupied_tiles) < 20:
                continue

            # There is a fifteen percent chance to just have a massive empty room
            if random.randint(0, 99) < 15:
                room.set_expansive(True)
                continue

            # Remove a chunk of tiles from the room
            self.carve_room(room.room_id)

        # Connect all rooms with a path
        room_keys = tuple(self.rooms.keys())
        self.rooms[room_keys[0]].set_connected(True)

        try:
            for i in range(1, len(room_keys)):
                self.last_room_connection_args = (room_keys[i - 1], room_keys[i])
                self.last_room_connection_paths = []
                self.connect_room(room_keys[i - 1], room_keys[i])
        except Exception:
            print(f"Last room connection coords: ")
            print(self.rooms[self.last_room_connection_args[0]].occupied_tiles[0])
            print(self.rooms[self.last_room_connection_args[1]].occupied_tiles[0])
            print(f"Room connection paths: {self.last_room_connection_paths}")

            for row in self.floor_grid:
                output = ""
                for col in row:
                    tile = self.tiles[col] if col else None
                    output += ("O " if (tile and tile.is_connector) else ("X " if tile else "- "))

                print(output)
            raise

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
        alcove_tiles = []
        for x in range(x_pos, x_pos + width):
            for y in range(y_pos, y_pos + height):
                occupied_tiles.append([x, y])

        # TODO: Allow alcoves to be placed on left and top of rooms

        # Place the alcove in the expanded width
        if alcove_placement == 1:
            alcove_x = x_pos + width
            alcove_y = random.randint(y_pos, y_pos + height - alcove_size)
            for i in range(alcove_y, alcove_y + alcove_size):
                alcove_tiles.append([alcove_x, i])

        # Place the alcove in the expanded height
        if alcove_placement == 2:
            alcove_x = random.randint(x_pos, x_pos + width - alcove_size)
            alcove_y = y_pos + height
            for i in range(alcove_x, alcove_x + alcove_size):
                alcove_tiles.append([i, alcove_y])

        new_room = DungeonRoom(self.floor_number, occupied_tiles + alcove_tiles)

        for tile in occupied_tiles:
            new_tile = DungeonTile(room_id=new_room.room_id, is_alcove=False)
            self.floor_grid[tile[0]][tile[1]] = new_tile.tile_id
            self.tiles[new_tile.tile_id] = new_tile

        for tile in alcove_tiles:
            new_tile = DungeonTile(room_id=new_room.room_id, is_alcove=True)
            self.floor_grid[tile[0]][tile[1]] = new_tile.tile_id
            self.tiles[new_tile.tile_id] = new_tile

        return new_room

    @staticmethod
    def find_closest_tiles(room_a: DungeonRoom, room_b: DungeonRoom):
        # TODO: Optimize me!
        a_coord_final = None
        b_coord_final = None
        shortest_distance = None
        for a_coord in room_a.occupied_tiles:
            for b_coord in room_b.occupied_tiles:
                distance = math.sqrt((a_coord[0] - b_coord[0])**2 + (a_coord[1] - b_coord[1])**2)
                if (shortest_distance is None) or (distance < shortest_distance):
                    shortest_distance = distance
                    a_coord_final = a_coord
                    b_coord_final = b_coord

        return a_coord_final, b_coord_final

    def connect_room(self, room_id_a: str, room_id_b: str):
        # If the start room is the same as the destination room, do nothing
        if room_id_a == room_id_b:
            return

        # Find the two tiles with the shortest distance between the two rooms
        room_a = self.rooms[room_id_a]
        room_b = self.rooms[room_id_b]

        # Room A must be considered connected already
        if not room_a.is_connected:
            raise Exception(f"Room A with id {room_id_a} is not connected.")

        # If room has already been connected, no action is necessary
        if room_b.is_connected:
            return

        # Find the two tiles with the shortest distance between the rooms
        start_coord, end_coord = self.find_closest_tiles(room_a, room_b)

        # Debugging info
        self.last_room_connection_paths.append((start_coord, end_coord))

        # Traverse X-coords until another tile is found, or until they match
        increment = 1 if start_coord[0] < end_coord[0] else -1
        current_x = start_coord[0]
        while current_x != end_coord[0]:
            # Analyze adjacent tiles and determine if a connector should be added here
            current_x += increment

            # Determine if this coordinate is a tile
            if self.floor_grid[current_x][start_coord[1]] is not None:
                # Determine if this tile is part of a room
                if self.tiles[self.floor_grid[current_x][start_coord[1]]].room_id is not None:
                    discovered_room = self.rooms[self.tiles[self.floor_grid[current_x][start_coord[1]]].room_id]

                    # If the discovered room is the starting room, continue
                    if discovered_room.room_id == room_id_a:
                        continue

                    # Mark this discovered room as connected if it is not already
                    if not discovered_room.is_connected:
                        discovered_room.set_connected(True)

                    # Restart pathfinding from this room
                    return self.connect_room(discovered_room.room_id, room_id_b)

                else:
                    # This tile is not part of a room, which means it is a connector. Connectors are allowed
                    # to cris-cross with each other, so no action is necessary
                    pass

            else:
                # This coordinate is not a tile, but is on the way to the destination. Place a tile here
                new_tile = DungeonTile(room_id=None, is_connector=True)
                self.floor_grid[current_x][start_coord[1]] = new_tile.tile_id
                self.tiles[new_tile.tile_id] = new_tile

            # Analyze the adjacent Y-coords to determine if either of those are rooms
            for y_coord in (start_coord[1] - 1, start_coord[1] + 1):
                # Ignore coordinates which would be off the grid
                if y_coord < 0 or y_coord > 31:
                    continue

                # Determine if a tile exists at this coordinate
                if self.floor_grid[current_x][y_coord] is not None:
                    # Determine if this tile is part of a room
                    if self.tiles[self.floor_grid[current_x][y_coord]].room_id:
                        discovered_room = self.rooms[self.tiles[self.floor_grid[current_x][y_coord]].room_id]

                        # If the discovered room is the starting room, continue
                        if discovered_room.room_id == room_id_a:
                            continue

                        # Mark this discovered room as connected if it is not already
                        if not discovered_room.is_connected:
                            discovered_room.set_connected(True)

                        # Determine the distance to the target coordinate from both the current coordinate
                        # and the adjacent coordinate
                        current_distance = math.sqrt(
                            (current_x - end_coord[0]) ** 2 + (start_coord[1] - end_coord[1]) ** 2)
                        adjacent_distance = math.sqrt(
                            (current_x - end_coord[0]) ** 2 + (y_coord - end_coord[1]) ** 2)

                        # If the discovered room's coordinate is closer to the destination than the current
                        # tile's coordinate, restart pathfinding from the discovered room
                        if current_distance > adjacent_distance:
                            return self.connect_room(discovered_room.room_id, room_id_b)

                    else:
                        # This tile is not part of a room, which means it is a connector. Connectors are allowed
                        # to cris-cross with each other, so no action is necessary
                        pass

        # Traverse Y-coords until another tile is found, or until they match
        increment = 1 if start_coord[1] < end_coord[1] else -1
        current_y = start_coord[1]
        while current_y != end_coord[1]:
            # Analyze adjacent tiles and determine if a connector should be added here
            current_y += increment

            # Determine if this coordinate is a tile
            if self.floor_grid[end_coord[0]][current_y] is not None:
                # Determine if this tile is part of a room
                if self.tiles[self.floor_grid[end_coord[0]][current_y]].room_id is not None:
                    discovered_room = self.rooms[self.tiles[self.floor_grid[end_coord[0]][current_y]].room_id]

                    # If the discovered room is the starting room, continue
                    if discovered_room.room_id == room_id_a:
                        continue

                    # Mark this discovered room as connected if it is not already
                    if not discovered_room.is_connected:
                        discovered_room.set_connected(True)

                    # Restart pathfinding from this room
                    return self.connect_room(discovered_room.room_id, room_id_b)

                else:
                    # This tile is not part of a room, which means it is a connector. Connectors are allowed
                    # to cris-cross with each other, so no action is necessary
                    pass

            else:
                # This coordinate is not a tile, but is on the way to the destination. Place a tile here
                new_tile = DungeonTile(room_id=None, is_connector=True)
                self.floor_grid[end_coord[0]][current_y] = new_tile.tile_id
                self.tiles[new_tile.tile_id] = new_tile

            # Analyze the adjacent X-coords to determine if either of those are rooms
            for x_coord in (end_coord[0] - 1, end_coord[0] + 1):
                # Ignore coordinates which would be off the grid
                if x_coord < 0 or x_coord > 31:
                    continue

                # Determine if a tile exists at this coordinate
                if self.floor_grid[x_coord][current_y] is not None:
                    # Determine if this tile is part of a room
                    if self.tiles[self.floor_grid[x_coord][current_y]].room_id:
                        discovered_room = self.rooms[self.tiles[self.floor_grid[x_coord][current_y]].room_id]

                        # If the discovered room is the starting room, continue
                        if discovered_room.room_id == room_id_a:
                            continue

                        # Mark this discovered room as connected if it is not already
                        if not discovered_room.is_connected:
                            discovered_room.set_connected(True)

                        # Determine the distance to the target coordinate from both the current coordinate
                        # and the adjacent coordinate
                        current_distance = math.sqrt(
                            (end_coord[0] - end_coord[0]) ** 2 + (current_y - end_coord[1]) ** 2)
                        adjacent_distance = math.sqrt(
                            (x_coord - end_coord[0]) ** 2 + (current_y - end_coord[1]) ** 2)

                        # If the discovered room's coordinate is closer to the destination than the current
                        # tile's coordinate, restart pathfinding from the discovered room
                        if current_distance > adjacent_distance:
                            return self.connect_room(discovered_room.room_id, room_id_b)

                    else:
                        # This tile is not part of a room, which means it is a connector. Connectors are allowed
                        # to cris-cross with each other, so no action is necessary
                        pass

    def carve_room(self, room_id):
        room = self.rooms[room_id]

        # Remove between fifteen and thirty percent of tiles in the room
        tiles_to_remove = math.ceil(len(room.occupied_tiles) * (random.randint(15, 30) / 100))

        # Find alcove tiles in this room and remove them first, thus converting the room into a rectangle
        occupied_tiles = room.occupied_tiles.copy()
        for tile_coords in occupied_tiles:
            tile = self.tiles[self.floor_grid[tile_coords[0]][tile_coords[1]]]
            if tile.is_alcove:
                self.floor_grid[tile_coords[0]][tile_coords[1]] = None
                room.remove_tile(tile_coords)
                del self.tiles[tile.tile_id]
                tiles_to_remove -= 1

        # Analyze the room to determine corner coordinates
        min_x = max_x = min_y = max_y = None
        for tile_coords in room.occupied_tiles:
            min_x = tile_coords[0] if (min_x is None or min_x > tile_coords[0]) else min_x
            max_x = tile_coords[0] if (max_x is None or max_x < tile_coords[0]) else max_x
            min_y = tile_coords[1] if (min_y is None or min_y > tile_coords[1]) else min_y
            max_y = tile_coords[1] if (max_y is None or max_y < tile_coords[1]) else max_y

        algorithm_choice = random.randint(0, 98)

        # Thirty-three percent chance we take the L-Shape algorithm. This removes a set of tiles from the corner
        # of a room, causing it to take on an L-shape
        # Addendum:
        # Sufficiently small rooms aren't viable for more destructive algorithms, so we only use the L-Shape algorithm
        if (len(room.occupied_tiles) < 31) or (algorithm_choice < 33):
            square_dimension = math.floor(math.sqrt(tiles_to_remove))
            remainder = math.ceil(math.sqrt(tiles_to_remove) % square_dimension)
            reverse = True if (random.randint(0, 1) == 1) else False

            # Determine starting coordinates
            x_coord = max_x if reverse else min_x
            y_coord = max_y if reverse else min_y
            increment = -1 if reverse else 1

            # Traverse horizontally if the room is wider than tall
            if (max_x - min_x) > (max_y - min_y):
                # Remove tiles from each coordinate
                target_x = (x_coord + (square_dimension * increment))
                while x_coord != target_x:
                    target_y = (y_coord + (square_dimension * increment))
                    while y_coord != target_y:
                        room.remove_tile((x_coord, y_coord))
                        del self.tiles[self.floor_grid[x_coord][y_coord]]
                        self.floor_grid[x_coord][y_coord] = None
                        y_coord += increment
                    y_coord = max_y if reverse else min_y
                    x_coord += increment

                # Remove any remaining tiles from the next column, which will always be fewer than
                # the square_dimension
                if remainder > 0:
                    target_y = (y_coord + (remainder * increment))
                    while y_coord != target_y:
                        room.remove_tile((x_coord, y_coord))
                        del self.tiles[self.floor_grid[x_coord][y_coord]]
                        self.floor_grid[x_coord][y_coord] = None
                        y_coord += increment

            # Traverse vertically if the room is taller than wide
            else:
                # Remove tiles from each coordinate
                target_y = (y_coord + (square_dimension * increment))
                while y_coord != target_y:
                    target_x = (x_coord + (square_dimension * increment))
                    while x_coord != target_x:
                        room.remove_tile((x_coord, y_coord))
                        del self.tiles[self.floor_grid[x_coord][y_coord]]
                        self.floor_grid[x_coord][y_coord] = None
                        x_coord += increment
                    x_coord = max_x if reverse else min_x
                    y_coord += increment

                # Remove and remaining tiles from the next row, which will always be fewer than
                # the square dimension
                if remainder > 0:
                    target_x = (x_coord + (remainder * increment))
                    while x_coord != target_x:
                        room.remove_tile((x_coord, y_coord))
                        del self.tiles[self.floor_grid[x_coord][y_coord]]
                        self.floor_grid[x_coord][y_coord] = None
                        x_coord += increment

            return

        # Minimum room size = 31
        # Remove a 3x3 or 4x4 square from the room, based on total room size
        # Ignores the target number of tiles to remove
        elif algorithm_choice < 66:
            square_edge = 3 if (len(room.occupied_tiles) < 16) else 4
            start_x = min_x
            start_y = min_y

            if min_x == (max_x - square_edge):
                start_x = random.randint(min_x, max_x - square_edge)

            if min_y == (max_y - square_edge):
                random.randint(min_y, max_y - square_edge)

            for x in range(start_x, start_x + square_edge):
                for y in range(start_y, start_y + square_edge):
                    room.remove_tile((x, y))
                    del self.tiles[self.floor_grid[x][y]]
                    self.floor_grid[x][y] = None
            return

        # Minimum room size = 31
        # Random tile removal algorithm
        else:
            while tiles_to_remove > 0:
                # Remove random tiles from the room
                x, y = room.occupied_tiles[random.randint(0, len(room.occupied_tiles) - 1)]

                # Do not remove the edges of a room in this manner
                if x == max_x or x == min_x or y == max_y or y == min_y:
                    continue

                # Remove this tile
                room.remove_tile((x, y))
                del self.tiles[self.floor_grid[x][y]]
                self.floor_grid[x][y] = None
                tiles_to_remove -= 1

            # Find any inaccessible tiles and remove them
            for (x, y) in room.occupied_tiles:
                if \
                        ((x+1 < 33) and (self.floor_grid[x+1][y] is None)) and \
                        ((x-1 > 0) and (self.floor_grid[x-1][y] is None)) and \
                        ((y+1 < 33) and (self.floor_grid[x][y+1] is None)) and \
                        ((y-1 > 0) and (self.floor_grid[x][y-1] is None)):
                    room.remove_tile((x, y))
                    del self.tiles[self.floor_grid[x][y]]
                    self.floor_grid[x][y] = None
            return
