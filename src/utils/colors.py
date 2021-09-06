import os
import sys

from re import search
from platform import system, version

from flags import has_flag


def env_color():
    force_color = os.getenv("FORCE_COLOR")
    if force_color is not None:
        if force_color == "true":
            return 1

        if force_color == "false":
            return 0

        return len(force_color) == 0 and 1 or min(int(force_color), 3)


def supports_color(stream=sys.stdout):
    flag_color = None

    if any(has_flag(flag) for flag in ["no-color", "no-colors", "color=false", "color=never"]):
        flag_color = False
    elif any(has_flag(flag) for flag in ["colors", "color=true", "color=always"]):
        flag_color = True

    env = env_color()

    if env is not None:
        flag_color = env

    if flag_color == 0:
        return False

    if not stream.isatty() and flag_color is None:
        return False

    if os.getenv("TERM") == "dumb":
        return flag_color or 0

    if system() == "Windows":
        os_release = version().split(".")

        if int(os_release[0]) >= 10 and int(os_release[2]) >= 10586:
            return True

    if os.getenv("CI") is not None:
        return any(env_variable for env_variable in
                   ["TRAVIS", "CIRCLECI", "APPVEYOR", "GITLAB_CI", "GITHUB_ACTIONS", "BUILDKITE",
                    "DRONE"]) or os.getenv("CI_NAME") == "codeship"

    if os.getenv("COLORTERM") is not None:
        return True

    term_program = os.getenv("TERM_PROGRAM")
    if term_program is not None:
        if term_program == "iTerm.app" or term_program == "Apple_Terminal":
            return True

    if search(r"-256(color)?", os.getenv("TERM") or ""):
        return True

    if search(r"^screen|^xterm|^vt100|^vt220|^rxvt|color|ansi|cygwin|linux", os.getenv("TERM") or ""):
        return True

    if os.getenv("COLORTERM") is not None:
        return True

    return False
