"""
Contains all of the global directory names and functions for user input
TODO: Make the user pass in the game dir
"""
import copy
import logging
import os
import pathlib
import sys
import textwrap

import _files

logging.basicConfig(level = logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_build_id(list_tokens):
    """
    Assumes -DBUILD=value
    TODO: Is the build id always from DBUILD?
    """
    for token in list_tokens:
        if "DBUILD" in token.upper():
            return int(token.split("=")[-1].strip())

    return None

def get_build_id(fname = "Makefile") -> int:
    """
    Assumes only one set of CPPFLAGS
    """
    path_file = pathlib.Path(fname)
    if not _files.check_file(path_file):
        return None
    with open(path_file, "r") as file:
        for line in file:
            list_tokens = line.split()
            if len(list_tokens) and list_tokens[0] == "CPPFLAGS":
                return extract_build_id(list_tokens[1:])

remaining_args = copy.deepcopy(sys.argv[1:])
using_cl_args = len(sys.argv) > 1

def cli_pause() -> None:
    """
    Continues to prompt user unless they manually kill it.
    TODO: Replace with click()
    TODO: Give the user the option to exit
    """
    if using_cl_args:
        if len(remaining_args) == 0:
            sys.exit(0)
    else:
        print("Press Enter to continue...")
        input()

IS_WINDOWS_OS = sys.platform == "win32"
LOG_FILE = "crash.log"
CONFIG_FILE = "config.json"
DIR_GAME = _files.get_file_directory(fname = "config.json", folder = "games")
CONFIG_PATH = DIR_GAME / CONFIG_FILE
logger.debug(f"FOLDER_DISTANCE: {DIR_GAME}")
logger.debug(f"CWD: {pathlib.Path.cwd()}")
DISTANCE_LENGTH = str(DIR_GAME)[1:].count("/") + 1
ISO_PATH = DIR_GAME / "build"
DIR_SYMBOLS = DIR_GAME / "symbols"
PLUGIN_PATH = DIR_GAME / "plugins"
GAME_INCLUDE_PATH = DIR_GAME / "include"
MOD_PATH = DIR_GAME / "mods"
MAKEFILE = "Makefile"
COMPILE_LIST = "buildList.txt"
FILE_LIST = "fileList.txt"
SRC_FOLDER = "src/"
OUTPUT_FOLDER = "output/"
BACKUP_FOLDER = "backup/"
DEBUG_FOLDER = pathlib.Path("debug") # TODO: Change to MOD_DIR / MOD name
OBJ_FOLDER = DEBUG_FOLDER / "obj/"
DEP_FOLDER = DEBUG_FOLDER / "dep/"
COMP_SOURCE = DEBUG_FOLDER / "source.txt"
TEXTURES_FOLDER = pathlib.Path("newtex")
TEXTURES_OUTPUT_FOLDER = TEXTURES_FOLDER / "output"
GCC_MAP_FILE = DEBUG_FOLDER / "mod.map"
GCC_OUT_FILE = DEBUG_FOLDER / "gcc_out.txt"
TRIMBIN_OFFSET = DEBUG_FOLDER / "offset.txt"
COMPILATION_RESIDUES = ["overlay.ld", MAKEFILE, "comport.txt"]
REDUX_MAP_FILE = DEBUG_FOLDER / "redux.map"
SETTINGS_FILE = "settings.json"
SETTINGS_PATH = DIR_GAME.parent / SETTINGS_FILE
DISC_FILE = "disc.json"
DISC_PATH = DIR_GAME / DISC_FILE
TOOLS_PATH = DIR_GAME.parents[1] / "tools"
COMMENT_SYMBOL = "//"
MOD_NAME = pathlib.Path.cwd().name # TODO: Pass this as an arg
MOD_DIR = str(pathlib.Path.cwd()).replace("\\", "/") + "/"
try:
    GAME_NAME = pathlib.Path.cwd().parents[DISTANCE_LENGTH].name # not sure, number of folders?
    logger.debug(f"GAME_NAME: {GAME_NAME}")
except IndexError as error:
    logger.exception("No GAME_NAME found")

HEXDIGITS = ["A", "B", "C", "D", "E", "F"]

def request_user_input(first_option: int, last_option: int, intro_msg: str, error_msg: str) -> int:
    """
    TODO: Convert this to click
    """
    if using_cl_args and len(remaining_args) == 0:
        raise Exception("ERROR: Not enough arguments to complete command.")

    if not using_cl_args:
        print(textwrap.dedent(intro_msg))

    raise_exception = False
    i = 0
    while True:
        try:
            i = int(input()) if not using_cl_args else int(remaining_args.pop(0))
            if (i < first_option) or (i > last_option):
                if using_cl_args:
                    raise_exception = True
                    break
                else:
                    print(textwrap.dedent(error_msg))
            else:
                break
        except:
            if using_cl_args:
                raise_exception = True
                break
            else:
                print(textwrap.dedent(error_msg))

    if raise_exception:
        raise Exception(textwrap.dedent(error_msg))

    return i

def is_number(s: str) -> bool:
    is_hex = False
    if len(s) > 1 and s[0] == "-":
        s = s[1:]
    if len(s) > 2 and s[:2] == "0x":
        s = s[2:]
        is_hex = True
    if len(s) == 0:
        return False
    for char in s:
        if not ((char.isdigit()) or (is_hex and char.upper() in HEXDIGITS)):
            return False
    return True

def cli_clear() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")
