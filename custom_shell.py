import sys
import os
import subprocess
from typing import Callable
from functools import partial

# PATH is an environment variable that specifies the set of *directories* where executable files are located
# It is incorrect to parse the PATH only once because PATH can be modified dynamically (during runtime).
"""
EXECUTABLES: dict[str, str] = {
    exe_file: path
    for path in os.environ["PATH"].split(os.pathsep)  # "os.pathsep" is ";" for Windows and ":" for Unix)
    if os.path.isdir(path)
    for exe_file in os.listdir(path)
    if os.path.isfile(os.path.join(path, exe_file))
}
"""
# Hence, everytime "type some_exe" is run, the implementation should re-evaluate PATH, ensuring it reflects any potential updates!

type Completed = subprocess.CompletedProcess  # type hinting alias


def parse(string: str, remove_spaces=False) -> list[str]:
    parsed = []
    str_length = len(string)
    i = 0

    def tokenize_quote(quote: str) -> bool:
        nonlocal i, start  # use the "i" from the enclosing scope, otherwise modifying an enclosed variable within a child function makes it local (creates a copy) to that child function
        if string[i] == quote:
            i += 1
            start = i
            while i < str_length and string[i] != quote:
                i += 1

            white_space = " " if i + 1 < str_length and string[i + 1] == " " else ""  # we can't always add a whitespace because you could have two neighboring quotes: 'text1''text2'
            parsed.extend((string[start: i], white_space))  # use ".extend()" rather than + " " as not to have the whitespace part of the string token
            return True

        return False

    while i < str_length:
        if tokenize_quote("\'"):
            pass

        elif tokenize_quote("\""):
            pass

        elif string[i] != " ":
            start = i
            i += 1
            while i < str_length and string[i] != " ":
                i += 1

            parsed.extend((string[start: i], " "))

        i += 1

    return parsed if not remove_spaces else [part for part in parsed if part not in (" ", "")]


def r_executable(exe: str, args: str = None, run: bool = True) -> Completed | str | int:
    """
    r_executable: runs the executable or returns its path according to bool parameter "run"
    :param exe: string object labeling the given executable name
    :param args: string object containing arguments passed along with their associated executable
    :param run: boolean dictating whether to run the executable or not
    :return: CompletedProcess if the executable is found and run, or the executable's path as a string if it's found but
    not run (depending on truthiness of "run"), else return 0 if executable is not found.
    """
    for path in os.environ["PATH"].split(os.pathsep):  # "os.pathsep" is ";" for Windows and ":" for Unix (posix))
        full_paths = (os.path.join(path, exe) + extension for extension in os.environ.get("PATHEXT", "").split(os.pathsep))

        for full_path in full_paths:
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):  # if file exists and is an executable...
                if run:
                    return subprocess.run([exe, *parse(args, remove_spaces=True)])  # unpacks (flattens) the elements or args as comma-separated values
                else:
                    return full_path

    return 0  # if command was not found


def exit_cmd(args: str) -> None:
    if args:
        exit(int(args)) if args.isdigit() else exit()
    else:
        exit()


def echo(args: str) -> None:
    print("".join(parse(args)).rstrip())


def type_cmd(args: str) -> None:
    if not args:
        return

    for cmd in args.split():
        if cmd in CMDS:
            print(f"{cmd} is a shell builtin")

        elif cmd_path := r_executable(cmd, run=False):
            print(f"{cmd} is {cmd_path}")

        else:
            print(f"{cmd}: not found", file=sys.stderr)


def pwd(_) -> None:
    print(os.getcwd())


def cd(args: str) -> None:
    if args:
        target_path = args.lstrip()
        if target_path.startswith("~"):
            home = os.environ["HOME"] if os.name == "posix" else os.environ["HOMEPATH"]
            target_path = target_path.replace("~", home)

        if os.path.isdir(target_path):
            os.chdir(target_path)
        else:
            print(f"cd: {target_path}: No such file or directory")


def ls(args: str) -> None:
    if args:
        target_path = args.lstrip()
        if os.path.isdir(target_path):
            print(*os.listdir(target_path))
        else:
            print(f"ls: {target_path}: No such file or directory", file=sys.stderr)

    else:
        print(*os.listdir())


CMDS: dict[str, Callable[[str], None]] = {
    "exit": exit_cmd,
    "echo": echo,
    "type": type_cmd,
    "pwd": pwd,
    "cd": cd,
    "ls": ls
}


def main():
    while True:
        sys.stdout.write("$ ")

        # Wait for user input (recall: "input()" is a blocking (hanging) call)
        if usr_cmd := input().strip().partition(" "):  # partitions the string on 1st separator encounter, returning part before, sep, and part after, as a tuple
            # Assign the 1st element of "usr_cmd" to "cmd", the 2nd element (sep) to nothing (_), and the 3rd element to "args"
            cmd, _, args = usr_cmd

            if CMDS.get(cmd.lower(), partial(r_executable, cmd))(args) == 0:  # if no shell command was executed
                print(f"{cmd}: command not found", file=sys.stderr)


if __name__ == "__main__":
    main()
