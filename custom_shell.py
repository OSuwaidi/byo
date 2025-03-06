import sys
import os
import subprocess
from typing import Callable

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


def find_executable(cmd: str) -> str:
    for path in os.environ["PATH"].split(os.pathsep):  # "os.pathsep" is ";" for Windows and ":" for Unix)
        if os.path.isfile((full_path := os.path.join(path, cmd))) and os.access(full_path, os.X_OK):  # if file exists and is an executable...
            return full_path


def exit_cmd(args: list[str]) -> None:
    if args:
        exit_status: str = args[0]
        exit(int(exit_status)) if exit_status.isdigit() else exit()
    else:
        exit()


def echo(args: list[str]) -> None:
    print(*args)  # unpack the elements of the list "args"


def type_cmd(args: list[str]) -> None:
    if not args:
        return

    for cmd in args:
        if cmd in CMDS:
            print(f"{cmd} is a shell builtin")

        elif cmd_path := find_executable(cmd):
            print(f"{cmd} is {cmd_path}")

        else:
            print(f"{cmd}: not found", file=sys.stderr)


CMDS: dict[str, Callable[[list[str]], None]] = {
    "exit": exit_cmd,
    "echo": echo,
    "type": type_cmd,
}


def main():
    while True:
        sys.stdout.write("$ ")

        # Wait for user input
        if usr_cmd := input().strip().split():
            cmd, *args = usr_cmd  # assign the first element of "usr_cmd" to "cmd", and the rest (*) of the elements to the list "args"

            if find_executable(cmd):
                subprocess.run([cmd, *args])

            else:
                CMDS.get(
                    cmd.lower(), lambda _: print(f"{cmd}: command not found", file=sys.stderr)
                )(args)


if __name__ == "__main__":
    main()
