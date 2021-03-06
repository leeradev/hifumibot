import ctypes
import hashlib
import os
import platform
import shutil
import socket
import stat
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from __init__ import *
from config import *
from tests.suite import run_tests

try:
    import colorama
    from core.logger import warning, info, error
    from colorlog import ColoredFormatter
    import requests

    # Recycling lines

    colorama.init()
    logger_success = True

except ImportError:
    logger_success = False

try:
    import urllib.request
    from importlib.util import find_spec
except ImportError:
    pass

try:
    import unittest
except ImportError:
    unittest = None

try:
    import pip
except ImportError:
    pip = None

REQS_DIR = "lib"
sys.path.insert(0, REQS_DIR)
REQS_TXT = "./config/requirements.txt"
FFMPEG_BUILDS_URL = "https://ffmpeg.zeranoe.com/builds/"

BOT_VERSION = '{} {}.{}.{}'.format(
    version_info.releaselevel, version_info.major,
    version_info.minor, version_info.micro
)

FFMPEG_FILES = {  # Names encoded to base 32-48
    "ffmpeg.exe": "e0d60f7c0d27ad9d7472ddf13e78dc89",
    "ffplay.exe": "d100abe8281cbcc3e6aebe550c675e09",
    "ffprobe.exe": "0e84b782c0346a98434ed476e937764f"
}


class VersionError(EnvironmentError):
    pass


def is_internet_on():
    """
    Checks if the computer or device that the process
    it's executing in has stable Internet connection.
    This is done by testing the websocket.
    :return: True if Internet is present, otherwise return False.
    """
    try:
        host = socket.gethostbyname('www.google.com')
        socket.create_connection((host, 80), 2)
        return True
    except socket.error:
        return False


def pause():
    """
    Pauses the program.
    :return: A message to request the user to press a key to continue.
    """
    input("Press ENTER key to continue.")


def computer_meets_color():
    """
    Installs the required requirements for the console
    logging in color.
    :return: Pip call, then exit code. 
    0 if everything is fine, 1 if error ocurred.
    """
    interpreter = sys.executable.split('/')[-1]

    if not interpreter:
        error("Python interpreter not found.")
        return

    args = [
        interpreter, "-m",
        "pip", "install",
        "--upgrade", REQS_DIR,
        "colorama"
    ]

    args2 = [
        interpreter, "-m",
        "pip", "install",
        "--upgrade", REQS_DIR,
        "colorlog"
    ]

    args3 = [  # Just recycling lines
        interpreter, "-m",
        "pip", "install",
        "--upgrade", REQS_DIR,
        "requests"
    ]

    code = subprocess.call(args)
    code2 = subprocess.call(args2)
    code3 = subprocess.call(args3)

    if code == 0 and code2 == 0 and code3 == 0:
        pass
    else:
        error("\nUh oh! An error ocurred and installation is going to "
              "be aborted.\nPlease fix the error above basing in the docs.\n")
        exit(1)


def install_reqs():
    """
    Installs the required requirements for the environment.
    :return: Pip call, then exit code. 
    0 if everything is fine, 1 if error ocurred.
    """
    remove_reqs_readonly()
    interpreter = sys.executable.split('/')[-1]

    if not interpreter:
        error("Python interpreter not found.")
        return

    txt = REQS_TXT

    args = [
        interpreter, "-m",
        "pip", "install",
        "--upgrade",
        "--target", REQS_DIR,
        "-r", txt
    ]

    if IS_MAC:
        args.remove("--target")
        args.remove(REQS_DIR)

    code = subprocess.call(args)

    if code == 0:
        info("\nPython requirements installed successfully! "
             "Now installing PM2...")
        pm2_str = subprocess.call(['npm', 'install', 'pm2', '-g'])

        if pm2_str == 0:
            info("\nPM2 installed successfully!")
        else:
            error(
                "\nUh oh! An error ocurred and installation is going to be "
                "aborted.\nPlease fix the error above basing in the docs.\n"
            )
    else:
        error("\nUh oh! An error ocurred and installation is going to "
              "be aborted.\nPlease fix the error above basing in the docs.\n")


def update_pip():
    """
    Updates pip, a.k.a the Python package manager.
    :return: Pip call, then exit code. 
    0 if everything is fine, 1 if error ocurred.
    """
    interpreter = sys.executable.split('/')[-1]

    if not interpreter:
        error("Python interpreter not found.")
        return

    args = [
        interpreter, "-m",
        "pip", "install",
        "--upgrade", "pip"
    ]

    code = subprocess.call(args)

    if code == 0:
        info("\nPip updated successfully to the latest version!")
    else:
        error(
            "\nUh oh! An error ocurred and installation is going "
            "to be aborted.\nPlease fix the error above basing in the docs.\n")


def check_hifumi():
    """
    Checks if Hifumi's version is the latest. 
    :return: True if it's latest, otherwise False. None if an error returned.
    """
    url = 'https://raw.githubusercontent.com/' \
          'hifumibot/hifumibot/master/version.txt'
    r = requests.get(url)
    if r.status_code != 200 or not os.path.isfile("./version.txt"):
        raise VersionError
    online_output = r.text.strip("\n")
    with open("version.txt") as f:
        local_output = f.readline()
        f.close()
    if local_output > online_output:
        raise VersionError
    return local_output == online_output


def update_hifumi():
    """
    Updates Hifumi via Git. 
    Useful if something wents wrong or if a new version comes out.
    :return: Git call, then exit code. 
    0 if went fine, 1 or exception if error ocurred.
    """
    try:
        if check_hifumi():
            info("Hifumi is already the latest version."
                 "No need to perform an update right now!")
        else:
            try:
                code = subprocess.call(("git", "pull", "--ff-only"))
            except subprocess.CalledProcessError:
                error("\nError: Git not found. It's either not installed or "
                      "not in the PATH environment variable. Please fix this!")
                return
            if code == 0:
                info("\nHifumi is now updated successfully!")
                if os.path.isfile("./config/sample_settings.py"):
                    os.remove("./config/sample_settings.py")
            else:
                error("\nUh oh! An error ocurred and "
                      "update is going to be aborted.\n"
                      "This error might be caused from "
                      "the environment edits you made. "
                      "Please fix this by going to the maintenance menu.")
    except VersionError:
        error("An error ocurred because version.txt file is edited or invalid."
              "Please recover the version.txt file from the Git repo.")


def reset_hifumi(reqs=False, data=False, cogs=False, git_reset=False):
    """
    Resets Hifumi or any of its properties (enabled to True boolean).
    If all of the parameters are enabled, Hifumi will get a 'factory reset'.
    :param reqs: Choose to reset the local packages.
    :param data: Choose to reset the data folder.
    :param cogs: Choose to reset the cogs (command modules).
    :param git_reset: Choose to replace all the 
    environment with the latest commit.
    :return: For reqs, data, cogs. Folder removing and result or exception
    (FileNotFoundError or another). 
    If git_reset an exit code. 0 if went fine, 1 if otherwise.
    """
    if reqs:
        try:
            shutil.rmtree(REQS_DIR, onerror=remove_readonly)
            info("Installed local packages wiped successfully!")
        except FileNotFoundError:
            pass
        except Exception as e:
            error("Uh oh! An error ocurred: {}".format(e))
    if data:
        try:
            shutil.rmtree("data", onerror=remove_readonly)
            info("'data' folder has been wiped.")
        except FileNotFoundError:
            pass
        except Exception as e:
            error("Uh oh! An error ocurred: {}".format(e))

    if cogs:
        try:
            shutil.rmtree("cogs", onerror=remove_readonly)
            info("'cogs' folder has been wiped.")
        except FileNotFoundError:
            pass
        except Exception as e:
            error("An error occurred when trying to remove the 'cogs' folder: "
                  "{}".format(e))

    if git_reset:
        code = subprocess.call(("git", "reset", "--hard"))
        if code == 0:
            info(
                "Hifumi repaired successfully! to the last local commit. "
                "If the bot is started, please restart it to make effect.")
        else:
            error("The repair has failed.")


def open_docs():
    """
    Open the documentation in default browser.
    :return: The page opened
    """
    webbrowser.open("http://hifumibot.xyz/docs")


def download_ffmpeg(bitness):
    """
    Downloads FFMPEG from the official page. 
    It's a required tool for music commands.
    :param bitness: Can be 32bit or 64bit in string. 
    This is choosen for the download version.
    :return: FFMPEG download and a message 
    with instructions for the first time use.
    """
    clear_screen()
    repo = "https://github.com/hifumibot/hifumibot"
    verified = []

    if bitness == "32bit":
        info("Please download 'ffmpeg 32bit static' from the page that "
             "is about to open.\nOnce done, open the 'bin' folder located "
             "inside the zip.\nThere should be 3 files: ffmpeg.exe, "
             "ffplay.exe, ffprobe.exe.\nPut all three of them into the "
             "bot's main folder.")
        time.sleep(5)
        webbrowser.open(FFMPEG_BUILDS_URL)
        return

    for filename in FFMPEG_FILES:
        if os.path.isfile(filename):
            warning("{} already present. Verifying integrity... "
                    "".format(filename), end="")
            _hash = calculate_md5(filename)
            if _hash == FFMPEG_FILES[filename]:
                verified.append(filename)
                info("Done!")
                continue
            else:
                warning("Hash mismatch. Redownloading.")
        info("Downloading {}... Please wait.".format(filename))
        with urllib.request.urlopen(repo + filename) as data:
            with open(filename, "wb") as f:
                f.write(data.read())
        info("FFMPEG downloaded! Please follow the instructions! "
             "Open the 'bin' folder located inside the zip.\nThere should "
             "be 3 files: ffmpeg.exe, ffplay.exe, ffprobe.exe.\nPut all "
             "three of them into the bot's main folder.")

    for filename, _hash in FFMPEG_FILES.items():
        if filename in verified:
            continue
        info("Verifying {}... ".format(filename), end="")
        if not calculate_md5(filename) != _hash:
            info("Passed.")
        else:
            warning("Hash mismatch. Please redownload.")

    info("\nAll files have been downloaded.")


def verify_requirements():
    """
    Verifies the status of required requirements.
    :return: False if there's missing packages. Otherwise return True.
    """
    sys.path_importer_cache = {}
    spec1 = find_spec("discord")
    spec2 = find_spec("nacl")
    return spec1 and spec2


def is_ffmpeg_installed():
    """
    Checks if FFMPEG is installed by checking the current version in console.
    :return: True if command is successful, otherwise return False.
    """
    try:
        subprocess.call(["ffmpeg", "-version"], stdout=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def is_git_installed():
    """
    Checks if Git is installed by checking the current version in console.
    :return: True if command is successful, otherwise return False.
    """
    try:
        subprocess.call(["git", "--version"], stdout=subprocess.DEVNULL,
                        stdin=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def requirements_menu():
    """
    Prints the options from the requirement menu.
    :return: The requirements menu.
    """
    clear_screen()
    while True:
        print("Main requirements:\n")
        print("1. Install basic requirements")
        if IS_WINDOWS:
            print("\nffmpeg (required for audio):")
            print("3. Install ffmpeg 32bit")
            if IS_64BIT:
                print("4. Install ffmpeg 64bit (recommended on Windows 64bit)")
        print("\n0. Go back")
        choice = user_choice()
        if choice == "1":
            install_reqs()
            pause()
        elif choice == "2" and IS_WINDOWS:
            download_ffmpeg(bitness="32bit")
            pause()
        elif choice == "3" and (IS_WINDOWS and IS_64BIT):
            download_ffmpeg(bitness="64bit")
            pause()
        elif choice == "0":
            break
        clear_screen()


def update_menu():
    """
    Prints the options from the update menu.
    :return: The update menu.
    """
    clear_screen()
    autoclean()
    while True:
        reqs = verify_requirements()
        if not reqs:
            status = "No requirements installed"
        else:
            status = "Requirements installed"
        print("Status: " + status + "\n")
        print("Update:\n")
        print("Environment:")
        print("1. Update bot + requirements (recommended)")
        print("2. Update bot")
        print("3. Update requirements")
        print("\nOthers:")
        print("4. Update pip (might require admin privileges)")
        print("\n0. Go back")
        choice = user_choice()
        if choice == "1":
            check_hifumi()
            print("Updating requirements...")
            if reqs:
                install_reqs()
            else:
                print("The requirements haven't been installed yet.")
            pause()
        elif choice == "2":
            check_hifumi()
            pause()
        elif choice == "3":
            if reqs:
                install_reqs()
            else:
                print("The requirements haven't been installed yet.\n"
                      "Please install them before continue!")
            pause()
        elif choice == "4":
            update_pip()
            pause()
        elif choice == "0":
            break
        clear_screen()


def maintenance_menu():
    """
    Prints the options from the maintenance menu.
    :return: The maintenance menu.
    """
    clear_screen()
    if not IS_WINDOWS or not IS_MAC:
        warning("Before you continue, please verify this launcher and "
                "the bot are NOT installed in root folder, in '/' or "
                "any other important folder from the system to prevent "
                "that those ones get severely damaged. Proceed?")
        if user_pick_yes_no():
            autoclean()
            clear_screen()
            pass
        else:
            main()
    else:
        warning("Before you continue, please verify this launcher and "
                "the bot are NOT installed in a system important folder "
                "or an instance ran by the system, this to prevent "
                "that those ones get severely damaged. Proceed?")
        if user_pick_yes_no():
            autoclean()
            clear_screen()
            pass
        else:
            main()
    while True:
        print("Maintenance:\n")
        print("1. Repair environment (this won't include data)")
        print("2. Wipe 'data' folder")
        print("3. Wipe 'lib' folder (pip packages and libraries)")
        print("4. Clean Python cache (experimental)")
        print("5. Factory reset (please be careful)")
        print("\n0. Go back")
        choice = user_choice()
        if choice == "1":
            warning("Any code modification you have made will be lost. Data/"
                    "non-default cogs will be left intact. Are you sure?")
            if user_pick_yes_no():
                reset_hifumi(git_reset=True)
                pause()
        elif choice == "2":
            warning("Are you sure? This will wipe the 'data' folder, which "
                    "contains all your settings and cogs' data.\nThe 'cogs' "
                    "folder, however, will be left intact.")
            if user_pick_yes_no():
                reset_hifumi(data=True)
                pause()
        elif choice == "3":
            reset_hifumi(reqs=True)
            pause()
        elif choice == "4":
            warning("Are you sure?")
            if user_pick_yes_no():
                autoclean()
                info("Python cache should be cleaned now.")
                pause()
        elif choice == "5":
            warning("Are you sure? This will wipe ALL the installation "
                    "data.\nYou'll lose all your settings, cogs and any "
                    "modification you have made.\nThere is no going back, "
                    "so please be careful and choose wisely.")
            if user_pick_yes_no():
                reset_hifumi(reqs=True, data=True, cogs=True, git_reset=True)
                pause()
        elif choice == "0":
            break
        clear_screen()


def run_hifumi(autorestart):
    """
    Start Hifumi, autorestart is toggleable.
    :return: Exit code, 0 if fine, else more than 0.
    """
    interpreter = sys.executable.split('/')[-1]
    if not interpreter:
        raise RuntimeError("Couldn't find Python interpreter")

    if not verify_requirements():
        error("You don't have the requirements that are needed to "
              "start the bot. Please install them first and try again.")
        pause()
        main()

    run_script = Path("./run.py")
    # Don't worry about shard mode, that's toggleable via settings.py
    if not run_script.is_file():
        error(
            "Hifumi's main file to run is not available. "
            "Please reinstall Hifumi!")
        pause()
        main()
    try:
        if autorestart:
            cmd = ("pm2", "start", "run.py", "--name=Hifumi",
                   "--interpreter=" + interpreter)
            code = subprocess.call(cmd)
        else:
            cmd = (interpreter, "run.py")
            info("Hifumi is now started as single session! "
                 "To shutdown the bot, press CTRL+Z anytime.")
            code = subprocess.call(cmd)
    except KeyboardInterrupt:  # Triggered!
        code = 0
    if not autorestart and code is 0:  # If no error
        info("Hifumi has been terminated recently. Exit code: %d" % code)
    elif not autorestart and code is not 0:  # If error
        error("Hifumi has been terminated recently. Exit code: %d" % code)
    elif autorestart and code is not 0:
        clear_screen()
        info("Hifumi is already started! Restarting instead...")
        cmd = ("pm2", "restart", "run.py")
        subprocess.call(cmd)
    elif autorestart and code is 0:
        info("Hifumi has been started successfully!")
    else:  # If error
        error("Hifumi has been terminated recently. Exit code: %d" % code)
    pause()


def stop_hifumi():
    """
    Stops Hifumi from running if started with PM2
    :return: Exit code, 0 if fine, else more than 0.
    """
    interpreter = sys.executable.split('/')[-1]
    if not interpreter:
        raise RuntimeError("Couldn't find Python interpreter")

    run_script = Path("./run.py")
    # Don't worry about shard mode, that's toggleable via settings.py
    if not run_script.is_file():
        error(
            "Hifumi's main file to run is not available. "
            "Please reinstall Hifumi!")
        pause()
        main()
    code = subprocess.call(['pm2', 'stop', 'run.py'])
    if code is 0:
        info("Hifumi has been terminated successfully.")
    else:  # If error
        error("Hifumi is not registered into PM2. No need to use this now.")
    pause()


def incorrect_choice():
    """
    Returns an error of menu choose.
    :return: A message to the user 
    telling that the valid (s)he choosed is invalid.
    """
    warning("Incorrect choice! Please try again with a valid choice.")
    pause()


def about():
    """
    Prints the about information and the license
    :return: The about information
    """
    try:
        print("Hifumi ~The Discord bot~\n\n"
              "Developers: {}\nVersion: {}".format(', '.join(__author__),
                                                   BOT_VERSION),
              "\nHelpers: {}\n\n"
              "Website: http://hifumibot.xyz\n"
              "Twitter: @HifumiBot\n\n".format(
                  ', '.join(__helper__)) + LICENSE)
    except UnicodeEncodeError:  # When Umi bugs your own bash >_<
        print("Hifumi ~The Discord bot~\n\n"
              "Developers: {}\nVersion: {}".format(', '.join(__author_plain__),
                                                   BOT_VERSION),
              "\nHelpers: {}\n\n"
              "Website: http://hifumibot.xyz\n"
              "Twitter: @HifumiBot\n\n".format(
                  ', '.join(__helper_plain__)) + LICENSE)

    pause()


def about_system():
    """
    Prints the system information with a cool distro logo in ASCII
    :return: The system information
    """
    clear_screen()
    if IS_WINDOWS:
        os.system("systeminfo")
        pause()
    elif IS_MAC:
        os.system("system_profiler")
        pause()
    else:
        try:
            subprocess.call(["screenfetch"])
            print("\n")  # Ubuntu logo is RIP otherwise
            pause()
        except subprocess.CalledProcessError:
            warning("'screenfetch' package not found!"
                    "Printing simple information.\n")
            subprocess.call(["lsb_release", "-a"])  # This should be valid
            # for all Linux distributions
            pause()


def run_unittest():
    """
    Runs the unit test provider
    :return: Unit test script
    """
    clear_screen()
    warning("You're about to run unit test provider. This "
            "function is aimed for advanced users. Make "
            "sure to use it properly, preferably for testing, "
            "otherwise bad things can happen. Please refer "
            "to the 'Unit testing' section from the docs for "
            "details. Continue?")
    if user_pick_yes_no():
        if unittest is None:
            error("'unittest' module not found. Please install all "
                  "requirements from update menu.")
            pause()
            main()
        else:
            try:
                os.chdir(Path('tests').absolute())
                run_tests(os.curdir)
                os.chdir(Path('..').absolute())
                pause()
            except Exception as e:
                error("Something went wrong. Unit test interrupted!\n")
                error(str(e))
                pause()
    else:
        main()


def edit_settings():
    """
    Opens settings.py file in the notepad if present.
    :return: The action or an exception if an error ocurred.
    """
    path = os.path.join('config', 'settings.py')
    sample_path = os.path.join('config', 'sample_settings.py')
    settings_exist = os.path.isfile(path)
    sample_exist = os.path.isfile(sample_path)
    if settings_exist:
        __edit_settings(path)
    elif not settings_exist and sample_exist:
        info("It looks like it's your first time running Hifumi launcher.\n"
             "sample_settings.py is going to be renamed to settings.py.\n")
        pause()
        os.rename(sample_path, path)
        edit_settings()
    else:
        error(
            "An error ocurred while opening the "
            "settings into editor. If the file does not exist, "
            "please reinstall Hifumi from zero.\n")
        pause()


def __edit_settings(path):
    """
    :param path: the file path to edit
    :return: A helper function to edit_settings()
    """
    if IS_WINDOWS:
        subprocess.call(['start', 'notepad', path])
    elif IS_MAC:
        subprocess.call(['open', '-a', 'TextEdit', path])
    else:
        try:
            import editor
            editor.edit(path)
        except Exception as e:
            print('There was an error with the editor library:\n')
            print(str(e))
            print('Using nano as the editor.')
            time.sleep(3)
            subprocess.call(['sudo', 'nano', path])


def clear_screen():
    """
    Cleans the screen
    :return: The screen cleaned.
    """
    if IS_WINDOWS:
        os.system("cls")
    else:
        os.system("clear")


def user_choice():
    """
    Asks the user to choose something from the menu.
    :return: An input request
    """
    return input("> ").lower().strip()


def user_pick_yes_no():
    """
    A yes/no question to do an action.
    :return: An input request, can be yes or no.
    """
    choice = None
    yes = ("yes", "y", "Y", "YES")
    no = ("no", "n", "N", "NO")
    while choice not in yes and choice not in no:
        choice = input("Yes/No > ").lower().strip()
    return choice in yes


def remove_readonly(func, path):
    """
    Removes the files that are read-only and causes a bug in update.
    :return: Read-only files removed.
    """
    os.chmod(path, 0o755)
    func(path)


def remove_reqs_readonly():
    """
    Removes the packages that are read-only and causes a bug in update.
    :return: Read-only packages removed.
    """
    if not os.path.isdir(REQS_DIR):
        return
    os.chmod(REQS_DIR, 0o755)
    for root, dirs, files in os.walk(REQS_DIR):
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for f in files:
            os.chmod(os.path.join(root, f), 0o755)


def calculate_md5(filename):
    """
    Calculates md5 output to decode from the ffmpeg files during installation.
    :return: Hex digest output into md5.
    """
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def faster_bash():
    """
    Creates scripts for fast boot of Hifumi without going
    through the launcher
    :return: The files created if successful
    """
    interpreter = sys.executable.split('/')[-1]
    if not interpreter:
        return

    call = "\"{}\" run.py".format(interpreter)
    modified = False

    if IS_WINDOWS:
        echo_disabler = "@echo off\n"
        ccd = "pushd %~dp0\n"
        bot_loop = ":hifumi:\n"
        exit_trigger = "\necho Hifumi has been terminated."
        pause_str = "\necho Press any key to continue...\npause>nul"
        goto_loop = "\ngoto hifumi"
        ext = ".bat"
    else:
        echo_disabler = ''
        exit_trigger = ''
        bot_loop = ''
        goto_loop = ''
        ccd = 'cd "$(dirname "$0")"\n'
        pause_str = "\nread -rsp $'Press ENTER to continue...\\n'"
        if not IS_MAC:
            ext = ".sh"
        else:
            ext = ".command"

    start_hifumi = echo_disabler + call + exit_trigger + pause_str
    start_hifumi_autorestart = echo_disabler + bot_loop + call + goto_loop

    files = {
        "run_normal" + ext: start_hifumi,
        "run_autorestart" + ext: start_hifumi_autorestart
    }
    if not IS_WINDOWS:
        files["start_launcher" + ext] = ccd + call

    for filename, content in files.items():
        if not os.path.isfile(filename):
            info("Creating fast start scripts (.bat)")
            modified = True
            with open(filename, "w") as f:
                f.write(content)

    if not IS_WINDOWS and modified:  # Let's make them executable on Unix
        for script in files:
            st = os.stat(script)
            os.chmod(script, st.st_mode | stat.S_IEXEC)


def admin_running():
    """
    Checks if process is running as administrator
    :return: True if yes, False if not.
    """
    try:
        return os.getuid() == 0
    except AttributeError:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0


def detect_errors():
    """
    Detect errors for the program or either warnings that can damage
    or terminate immediately the launcher or Hifumi's process.
    :return: True if errors found, plus errors stringified. Else, return False.
    """
    has_git = is_git_installed()
    has_ffmpeg = is_ffmpeg_installed()
    is_git_installation = os.path.isdir(".git")  # Check if .git folder exists
    pkg = verify_requirements()
    return not is_git_installation or not has_git or not has_ffmpeg or not pkg


def string_errors():
    """
    Returns string errors if found, should be invoked only by detect_errors
    function.
    :return: String errors
    """
    has_git = is_git_installed()
    has_ffmpeg = is_ffmpeg_installed()
    is_git_installation = os.path.isdir(".git")  # Check if .git folder exists
    interpreter = sys.executable.split('/')[-1]
    if not interpreter:
        raise RuntimeError("Couldn't find Python's interpreter")
    if not is_git_installation:
        warning("This installation was not done via Git\n"
                "You probably won't be able to update some things that "
                "require this util, "
                "for example the bot environment. Please "
                "read the license file for more information. "
                "If you got this from another "
                "source, please reinstall Hifumi"
                "as it follows in the guide. "
                "http://www.hifumibot.xyz/docs\n\n")
    if not has_git:
        warning("Git not found. This means that it's either not "
                "installed or not in the PATH environment variable like "
                "it should be.\n\n")
    if not has_ffmpeg:
        error(
            "FFMPEG not found. This means that it's either not "
            "installed or not in the PATH environment variable like "
            "it should be. This program is needed to run music commands, "
            "so please install it before continue!\n\n")
    if not verify_requirements():
        if IS_WINDOWS:
            additional_str = "the required programs"
        elif IS_MAC:
            additional_str = "the required packages and programs"
        else:
            additional_str = "the required packages via terminal"
        error(
            "It looks like you're missing some "
            "packages, please install them or "
            "you won't be able to run Hifumi. "
            "For that, proceed to step 4.\n"
            "Make sure to install the pip modules "
            "and " + additional_str + " to ensure "
                                      "a great run instead of bad things.\n\n")
    if not admin_running():
        if IS_WINDOWS or IS_MAC:
            note = "executing Python shell in administrator mode"
        else:
            note = "doing sudo " + interpreter + " launcher.py or run as root"
        warning("Process is not running as administrator. Administrator "
                "action perfomance can fail sometimes if administrator "
                "permissions are disabled. Please restart Hifumi by " + note +
                ".\n\n")


def main():
    """
    Prints the main menu.
    :return: The main menu or an exception/warning if something is wrong.
    """
    if not is_internet_on():
        print("You're not connected to Internet! Please check your "
              "connection and try again.")
        exit(1)
    title_text = __title__ + ' Version ' + BOT_VERSION + ' ~ Launcher'
    if IS_WINDOWS:
        os.system("TITLE {}".format(title_text))
    elif IS_MAC:
        os.system("echo -n -e \"\033]0;{}\007\""
                  .format(title_text))
    else:
        sys.stdout.write("\x1b]2;{}\x07".format(title_text))
        sys.stdout.write(
            "\033]30;{}\007".format(title_text))
    while True:
        clear_screen()
        try:
            faster_bash()
        except Exception as e:
            error("Failed making fast start scripts: {}\n".format(e))
        print(" __    __   __   _______  __    __   ___  ___   __\n"
              "|  |  |  | |  | |   ____||  |  |  | |   \/   | |  |    _\n"
              "|  |__|  | |  | |  |__   |  |  |  | |  \  /  | |  |  _| |_\n"
              "|   __   | |  | |   __|  |  |  |  | |  |\/|  | |  | |_   _|\n"
              "|  |  |  | |  | |  |     |  `--'  | |  |  |  | |  |   |_|\n"
              "|__|  |__| |__| |__|      \______/  |__|  |__| |__|\n\n")
        print("Bot options:")
        print("1. Start Hifumi with autorestart")
        print("2. Stop Hifumi if started with autorestart")
        print("3. Start Hifumi with no autorestart\n")
        print("Core options:")
        print("4. Run unit test")
        print("5. Update environment")
        print("6. Install requirements")
        print("7. Edit settings")
        print("8. Maintenance")
        print("9. About the program")
        print("10. About the system")
        print("11. Open documentation")
        print("\n12. Quit")
        choice = user_choice()
        if choice == "1":
            run_hifumi(autorestart=True)
        elif choice == "2":
            stop_hifumi()
        elif choice == "3":
            run_hifumi(autorestart=False)
        elif choice == "4":
            run_unittest()
        elif choice == "5":
            update_menu()
        elif choice == "6":
            requirements_menu()
        elif choice == "7":
            edit_settings()
        elif choice == "8":
            maintenance_menu()
        elif choice == "9":
            about()
        elif choice == "10":
            about_system()
        elif choice == "11":
            open_docs()
        elif choice == "12":
            print("Are you sure you want to quit?")
            if user_pick_yes_no():
                clear_screen()
                exit(0)
            else:
                main()
        else:
            incorrect_choice()


def run():
    """
    Main function of the program
    :return: An initialization request to the 
    program or an error if Python/pip is wrong.
    """
    abspath = os.path.abspath(__file__)
    dirname = os.path.dirname(abspath)
    os.chdir(dirname)
    if not logger_success:
        computer_meets_color()  # lol
        main()
    if not SYSTEM_OK:
        error("Sorry! This operation system is not compatible with "
              "Hifumi's environment and might not run at all. Hifumi "
              "is only supported for Windows, Mac, Linux and "
              "Raspberry Pi. Please install one of those OS and try "
              "again.")
        exit(1)
    elif not PYTHON_OK:
        error("Sorry! This Python version is not compatible. Hifumi needs "
              "Python 3.6 or higher. You have Python version {}.\n"
              .format(platform.python_version()) + " Install the required "
                                                   "version and try again.\n")
        exit(1)
    elif not pip:
        error("Hey! Python is installed but you are missing the pip module."
              "\nPlease reinstall Python without "
              "unchecking any option during the setup >_<")
        exit(1)
    else:
        info("Initializating...")
        if detect_errors():
            clear_screen()
            print("You got some warnings/errors. It's highly recommended "
                  "to fix them before you continue.\n")
            string_errors()
            pause()
            clear_screen()
        main()


if __name__ == '__main__':
    run()
