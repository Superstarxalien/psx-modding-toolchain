"""
Reads in the all the diretories
Does stuff with them
Runs in basically an infinite while loop
TODO: Replace with Click
"""
import _files # check_file, check_files, delete_file, create_directory, delete_directory
from makefile import Makefile, clean_pch
from compile_list import CompileList, free_sections, print_errors
from syms import Syms
from redux import Redux
from common import MOD_NAME, GAME_NAME, LOG_FILE, COMPILE_LIST, DEBUG_FOLDER, BACKUP_FOLDER, OUTPUT_FOLDER, COMPILATION_RESIDUES, TEXTURES_FOLDER, TEXTURES_OUTPUT_FOLDER, RECURSIVE_COMP_PATH, ABORT_PATH, CONFIG_PATH, IS_WINDOWS_OS, request_user_input, cli_clear, cli_pause, DISC_PATH, SETTINGS_PATH, CONFIG_PATH
from mkpsxiso import Mkpsxiso
from nops import Nops
from game_options import game_options
from image import create_images, clear_images, dump_images
from clut import clear_cluts, dump_cluts
from c import export_as_c

import logging
import os
import pathlib
import subprocess
import sys
from glob import glob

logger = logging.getLogger(__name__)

class Main:
    def __init__(self) -> None:
        self.redux = Redux()
        self.mkpsxiso = Mkpsxiso()
        self.nops = Nops()
        self.nops.load_config()
        self.redux.load_config(SETTINGS_PATH)
        self.actions = {
            1   :   self.compile,
            2   :   self.clean_files,
            3   :   self.mkpsxiso.extract_iso, # makes it awkward to pass arguments
            4   :   self.mkpsxiso.build_iso,
            5   :   self.mkpsxiso.xdelta,
            6   :   self.mkpsxiso.clean,
            7   :   self.redux.hot_reload,
            8   :   self.redux.restore,
            9   :   self.patch_disc_files,
            10  :   self.restore_disc_files,
            11  :   self.replace_textures,
            12  :   self.redux.restore_textures,
            13  :   self.redux.start_emulation, # would like to pass settings path here
            14  :   self.nops.hot_reload,
            15  :   self.nops.restore,
            16  :   self.clean_pch,
            17  :   self.disasm,
            18  :   export_as_c,
            19  :   self.clean_all,
            20  :   self.shutdown
        }
        self.num_options = len(self.actions)
        self.window_title = f"{GAME_NAME} - {MOD_NAME}"
        self.python = None
        if IS_WINDOWS_OS:
            self.python = "python"
        else:
            self.python = "python3"
        self.update_title()

    def shutdown(self):
        logger.info("EXITING")
        sys.exit(0)

    def update_title(self):
        """ TODO: Identify these commands """
        if IS_WINDOWS_OS:
            os.system("title " + self.window_title)
        else:
            os.system('echo -n -e "\\033]0;' + self.window_title + '\\007"')

    def get_options(self) -> int:
        intro_msg = """
        Please select an action:
        Mod:
        1 - Compile
        2 - Clean Files

        Iso:
        3 - Extract ISO
        4 - Build ISO
        5 - Generate xdelta patch
        6 - Clean Build

        PCSX-Redux:
        7 - Hot Reload Code
        8 - Hot Reload Code Restore
        9 - Hot Reload Disc Files
        10 - Hot Reload Disc Files Restore
        11 - Replace Textures
        12 - Restore Textures
        13 - Start Emulation

        NotPSXSerial:
        14 - Hot Reload Code
        15 - Hot Reload Code Restore

        General:
        16 - Clean Precompiled Header
        17 - Disassemble Elf
        18 - Export textures as C file
        19 - Clean All
        20 - Quit
        """
        error_msg = f"ERROR: Wrong option. Please type a number from 1-{self.num_options}.\n"
        return request_user_input(first_option=1, last_option=self.num_options, intro_msg=intro_msg, error_msg=error_msg)

    def abort_compilation(self, is_root: bool, is_warning: bool) -> None:
        if is_warning:
            logger.warning("Aborting ongoing compilations.")
            cli_pause()
        if is_root:
            _files.delete_file(RECURSIVE_COMP_PATH)
            return
        else:
            with open(ABORT_PATH, "w") as _:
                return

    def compile(self) -> None:
        if ABORT_PATH.exists(): # Shouldn't log ERROR for this one
            return # Abort ongoing compilation chain due to an error that occured
        if not _files.check_file(COMPILE_LIST):
            return
        is_root = False
        if not _files.check_file(RECURSIVE_COMP_PATH, quiet=True):
            with open(RECURSIVE_COMP_PATH, "w") as _:
                is_root = True
        else:
            with open(RECURSIVE_COMP_PATH, "r") as file:
                if MOD_NAME in file.readline().split():
                    return # checking whether the mod was already compiled
        instance_symbols = Syms()
        make = Makefile(instance_symbols.get_build_id(), instance_symbols.get_files())
        dependencies = []
        # parsing compile list
        free_sections()
        with open(COMPILE_LIST, "r") as file:
            for line in file:
                cl = CompileList(line, instance_symbols, "./")
                if cl.is_cl():
                    dependencies.append(cl.path_build_list)
                if not cl.should_ignore():
                    make.add_cl(cl)
        if print_errors[0]:
            intro_msg = "[Compile-py] Would you like to continue to compilation process?\n\n1 - Yes\n2 - No\n"
            error_msg = "ERROR: Wrong option. Please type a number from 1-2.\n"
            if request_user_input(first_option=1, last_option=2, intro_msg=intro_msg, error_msg=error_msg) == 2:
                self.abort_compilation(is_root, is_warning=False)
        if make.build_makefile():
            if make.make():
                with open(RECURSIVE_COMP_PATH, "a") as file:
                    file.write(MOD_NAME + " ")
            else:
                self.abort_compilation(is_root, is_warning=True)
        else:
            self.abort_compilation(is_root, is_warning=True)
        curr_dir = pathlib.Path.cwd()
        for dep in dependencies: # Does this matter since we know the full path?
            os.chdir(dep)
            path_module = CONFIG_PATH.parents[1] / "tools" / "mod-builder" / "main.py"
            # use to use get_distance_to_file(False, CONFIG_FILE), same as CONFIG_PATH?
            command = [self.python, str(path_module), "1", instance_symbols.version]
            result = subprocess.call(command) # only returns code
            if result != 0:
                logger.critical("Couldn't run the symbols version")
        os.chdir(curr_dir)
        if is_root:
            _files.delete_file(RECURSIVE_COMP_PATH)
            _files.delete_file(ABORT_PATH)
            self.update_title()

    def clean_files(self) -> None:
        _files.delete_directory(DEBUG_FOLDER)
        _files.delete_directory(BACKUP_FOLDER)
        _files.delete_directory(OUTPUT_FOLDER)
        _files.delete_directory(TEXTURES_OUTPUT_FOLDER)
        for file in COMPILATION_RESIDUES:
            _files.delete_file(file)
        _files.delete_file(ABORT_PATH)
        _files.delete_file(RECURSIVE_COMP_PATH)
        leftovers = glob("**/*.o", recursive=True) + glob("**/*.dep", recursive=True)
        for leftover in leftovers:
            _files.delete_file(leftover)

    def clean_pch(self) -> None:
        clean_pch()

    def clean_all(self) -> None:
        self.mkpsxiso.clean(all=True)
        self.clean()
        self.clean_pch()

    def patch_disc_files(self) -> None:
        self.redux.patch_disc_files(restore_files=False)

    def restore_disc_files(self) -> None:
        intro_msg = """
        WARNING: Make sure you're running the original ISO.
        Would you like to restore patched files to the original ones?
        1 - Yes
        2 - No
        """
        error_msg = "ERROR: Invalid input. Please enter 1 for Yes or 2 for No."
        willRestore = request_user_input(first_option=1, last_option=2, intro_msg=intro_msg, error_msg=error_msg) == 1
        if (willRestore):
            self.redux.patch_disc_files(restore_files=willRestore)

    def replace_textures(self) -> None:
        _files.create_directory(TEXTURES_OUTPUT_FOLDER)
        img_count = create_images(TEXTURES_FOLDER)
        if img_count == 0:
            logger.warning("0 images found. No textures were replaced")
            return
        dump_images(TEXTURES_OUTPUT_FOLDER)
        dump_cluts(TEXTURES_OUTPUT_FOLDER)
        self.redux.replace_textures()
        clear_images()
        clear_cluts()

    def disasm(self) -> None:
        path_in = DEBUG_FOLDER / 'mod.elf'
        path_out = DEBUG_FOLDER / 'disasm.txt'
        with open(path_out, "w") as file:
            command = ["mipsel-none-elf-objdump", "-d", str(path_in)]
            subprocess.call(command, stdout=file, stderr=subprocess.STDOUT)
        logger.info(f"Disassembly saved at {path_out}")

    def exec(self):
        while not _files.check_files([COMPILE_LIST, DISC_PATH, SETTINGS_PATH]):
            cli_pause()
        game_options.load_config()
        while True:
            cli_clear()
            i = self.get_options()
            self.actions[i]()
            cli_pause()

if __name__ == "__main__":
    try:
        main = Main()
        main.exec()
    except Exception as e:
        _files.delete_file(RECURSIVE_COMP_PATH)
        _files.delete_file(ABORT_PATH)
        logging.basicConfig(filename=LOG_FILE, filemode="w", format='%(levelname)s:%(message)s')
        logging.exception(e)