import os
import sys
import uuid
import zlib
import fnvhash
import re


class DungeonInfo:
    """
    an object that stores information contained in the `.dungeon_editor` file

    Attributes
    ----------
    dungeon_uuid : str
        uuid that is assigned randomly, official editor uses a random one each time.
    dungeon_name : str
        name of the dungeon.
    author : str
        name of the author.
    description : str
        description of the dungeon.
    dungeon_folder : str
        location of where the init.lua is located. this is almost always `mod_assets/scripts`
    """
    dungeon_uuid: str
    dungeon_name: str
    author: str
    description: str
    dungeon_folder: str

    def __init__(self, dungeon_name: str, author: str, description: str, dungeon_folder: str):
        self.dungeon_uuid = str(uuid.uuid4())
        self.dungeon_name = dungeon_name
        self.author = author
        self.description = description
        self.dungeon_folder = dungeon_folder

    def get_bytes(self):
        # creates our bytechunk each value is a string here
        # it puts an int of 4 bytes that tells you how long the following string is
        # and just repeats this for each value in the order of
        # UUID, NAME, AUTHOR, DESCRIPTION, DUNGEON FOLDER

        byte_array = len(self.dungeon_uuid.encode('utf-8')).to_bytes(4, "little")
        byte_array += self.dungeon_uuid.encode('utf-8')

        byte_array += len(self.dungeon_name.encode('utf-8')).to_bytes(4, "little")
        byte_array += self.dungeon_name.encode('utf-8')

        byte_array += len(self.author.encode('utf-8')).to_bytes(4, "little")
        byte_array += self.author.encode('utf-8')

        byte_array += len(self.description.encode('utf-8')).to_bytes(4, "little")
        byte_array += self.description.encode('utf-8')

        byte_array += len(self.dungeon_folder.encode('utf-8')).to_bytes(4, "little")
        byte_array += self.dungeon_folder.encode('utf-8')
        return byte_array


class File:
    """
    an object that stores information about a file as well as compressing it using zlib.compress()

    Attributes
    ----------
    compressed_size : int
        number of bytes in the file after compression
    uncompressed_size : int
        number of bytes in the file before compression
    file_name : str
        name of the path + file used by Grimrock2 to fetch this file in lua
    file_name_hash : int
        FNV1a-32 hash of the `file_name`
    file : bytearray
        the compressed file
    """

    compressed_size: int
    uncompressed_size: int
    file_name: str
    file_name_hash: int
    file: bytearray

    def __init__(self, file_path: str):
        """must be given a relative path starting from the location of the `.dungeon_editor` file"""

        # given the path it reads the file saves the size, compresses it saves the compressed size and calculates the
        # FNV1a-32 hash of the path_filename all for use later
        with open(file_path, "rb") as f:
            uncompressed_file = bytearray(f.read())
            self.uncompressed_size = len(uncompressed_file)
            self.file = bytearray(zlib.compress(uncompressed_file))
            self.compressed_size = len(self.file)
            self.file_name = '/'.join(file_path.split(os.path.sep))
            self.file_name_hash = fnvhash.fnv1a_32(self.file_name.encode())


def __get_header_bytes():
    """static header information that should be at the start of the file

    Returns
    -------
    bytearray
        bytes of the header
    """

    log2_file_header = bytearray("GRA2".encode('utf-8'))
    # ive seen this number switch between 11 and 12 not sure what the difference is. but it always seems to start at 11
    editor_version = bytearray(int(11).to_bytes(4, "little"))
    return bytearray(log2_file_header + editor_version)


def __scan_mod_directory(root_dir: str):
    """scans the provided directory to gather information about all the files sizes and compresses them for
    use later

    Parameters
    ----------
    root_dir : str
        directory that should contain the `.dungeon_editor` file

    Returns
    -------
    info : DungeonInfo
        the DungeonInfo object that contains the informatin inside of the `.dungeon_editor` file
    file_list : list
        a list containing the compressed files in `root_dir` as well as information about those files.
    """

    # save our cwd and then change it to be local to the .dungeon_editor file so that os.walk returns good values
    # that I don't have to edit directly to make a valid path for hashing
    original_dir = os.path.abspath(os.curdir)
    os.chdir(root_dir)
    file_list = []

    for root, subFolders, files in os.walk("."):
        for file in files:
            path = os.path.join(root, file)
            file_name = os.path.normpath(path)

            # don't add our dungeon_editor file to our package
            # read the dungeon editor file and save its information into our DungeonInfo
            if os.path.splitext(file_name)[1] == ".dungeon_editor":
                with open(file_name, "r") as editor_file:
                    lines = editor_file.readlines()
                    for line in lines:
                        if line.startswith("dungeonName"):
                            dungeon_name = re.findall(r'"([^"]*)"', line)[0]
                        if line.startswith("author"):
                            author = re.findall(r'"([^"]*)"', line)[0]
                        if line.startswith("description"):
                            description = re.findall(r'"([^"]*)"', line)[0]
                        if line.startswith("dungeonFolder"):
                            dungeon_folder = re.findall(r'"([^"]*)"', line)[0]

                    info = DungeonInfo(dungeon_name, author, description, dungeon_folder)
            else:
                # add the file to our directory variable. the file object handles reading info and compressing the file
                file_list.append(File(file_name))

    # restore our original cwd
    os.chdir(original_dir)
    return info, file_list


def __get_mod_info_header_bytes(directory: list, dungeon_info: DungeonInfo):
    """creates the mod info header which contains information about where the other headers are in the .dat file

    Parameters
    ----------
    directory : list
        list of File objects that should be added to the directory listing
    dungeon_info : DungeonInfo
        DungeonInfo object contains some needed information to complete this task

    Returns
    -------
    byte_array : bytearray
        the mod info header byte chunk
    """

    byte_array = bytearray()

    # unknown Hash in mod info header possibly fixed value? 4124689887
    byte_array += int(4124689887).to_bytes(4, "little")

    # position of start of Mod Info Section its after our directory listing so 20 bytes per listing
    # plus 28 bytes from header and mod header stuff
    byte_array += int(len(directory) * 20 + 28).to_bytes(4, "little")

    # 4 unknown bytes. Set all to x00
    byte_array += int(0).to_bytes(4, "little")

    # length of Mod_Info_Bytes
    byte_array += len(dungeon_info.get_bytes()).to_bytes(4, "little")

    # 4 unknown bytes. Set all to x00
    byte_array += int(0).to_bytes(4, "little")

    return byte_array


def __create_directory_bytes(directory: list, dungeon_info: DungeonInfo):
    """creates the directory listing and combines the compressed files into a single bytearray for use later

    Parameters
    ----------
    directory : list
        list of File objects that should be added to the directory listing
    dungeon_info : DungeonInfo
        DungeonInfo object contains some needed information to complete this task

    Returns
    -------
    byte_array : bytearray
        the directory listing byte chunk
    compressed_files : bytearray
        the compressed files byte chunk
    """

    # this adds what will the section we are making right now + mod info + header so that we can tell the game
    # what byte each file will start at in our .dat file
    # 28 is the length of the header + mod info section
    # and every file adds 20 to this directory
    # the size of dungeon_info changes based on what is in the .dungeon_editor
    # file, so we fetch the size from it directly
    start_of_data = 28 + len(directory) * 20 + len(dungeon_info.get_bytes())

    byte_array = bytearray()
    compressed_files = bytearray()
    for archive_file in directory:

        # fnv1a hash of the filename
        byte_array += archive_file.file_name_hash.to_bytes(4, "little")

        # position of the start of data in the file
        byte_array += (start_of_data + len(compressed_files)).to_bytes(4, "little")

        compressed_files += archive_file.file
        # number of bytes in file (compressed size)
        byte_array += archive_file.compressed_size.to_bytes(4, "little")

        # number of bytes when uncompressed
        byte_array += archive_file.uncompressed_size.to_bytes(4, "little")

        # unknown value seems to be set to 1 by official editor
        byte_array += int(1).to_bytes(4, "little")

    return byte_array, compressed_files


def package_dat_file(mod_directory: str) -> bytes:
    """packages files in `mod_directory` into a Legend of Grimrock 2 dat file.

    Parameters
    ----------
    mod_directory : string
        directory that contains the '.dungeon_editor' file.

    Returns
    -------
    bytes
        bytes of the .dat file that should be written to disk.
    """

    dungeon_info, directory = __scan_mod_directory(mod_directory)
    directory_data, compressed_files_bytes = __create_directory_bytes(directory, dungeon_info)
    output = __get_header_bytes()
    output += __get_mod_info_header_bytes(directory, dungeon_info)
    output += directory_data
    output += dungeon_info.get_bytes()
    output += compressed_files_bytes
    return bytes(output)


if __name__ == '__main__':
    data = package_dat_file(sys.argv[1])

    f = open("out/testpackage.dat", "wb")
    f.write(data)
    f.close()

