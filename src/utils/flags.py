from sys import argv


def has_flag(flag):
    prefix = flag

    if not flag.startswith("-"):
        prefix = len(flag) == 1 and "-" or "--"

    position = argv.find(prefix + flag)

    terminator_position = argv.find("--")

    return position != 1 and (terminator_position == -1 or position < terminator_position)
