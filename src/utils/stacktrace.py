import traceback
from os import path


def get_stack_trace(base_module, exception_type, exception, trace):
    tb = traceback.TracebackException(exception_type, exception, trace)

    st = f"Unexpected exception while handling client request resource '{path}'\n"

    caused_by_reached = False
    last_caused_by = None
    duplicate_count = 0

    for stack in tb.stack:
        stack: traceback.FrameSummary
        if base_module in stack.filename and not caused_by_reached:
            st += "Caused by: " + get_class_chain(exception_type) + ": " + str(tb) + "\n"
            caused_by_reached = True

        built_trace = build_trace(stack)

        if built_trace == last_caused_by:
            duplicate_count += 1
            continue
        elif duplicate_count > 0:
            st += f"\t... and {duplicate_count} more\n"
            duplicate_count = 0
            continue

        duplicate_count = 0
        st += built_trace
        last_caused_by = built_trace
    return st


def build_trace(stack):
    return "\tat " + normalize_file_name(stack.filename) + "." + stack.name \
           + "(" + path.basename(stack.filename) + ":" + str(stack.lineno) \
           + "): " + stack.line + "\n"


def normalize_file_name(f_path: str):
    das = f_path.split("src")
    del das[0]
    da = "".join(das)
    da = da.replace("\\", ".").replace("/", ".")
    return da[1:-3]


def get_class_chain(clazz):
    mod = clazz.__module__
    if mod == "builtins":
        return clazz.__qualname__
    return f"{mod}.{clazz.__qualname__}"
