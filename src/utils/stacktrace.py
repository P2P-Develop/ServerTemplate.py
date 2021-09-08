import traceback
from os import path


def get_stack_trace(base_module, exception_type, exception, trace):
    tb = traceback.TracebackException(exception_type, exception, trace)

    st = f"Unexpected exception while handling client request resource '{path}'\n"

    flag = False

    for stack in tb.stack:
        stack: traceback.FrameSummary
        if base_module in stack.filename and not flag:
            flag = True
            st += "Caused by: " + get_class_chain(exception_type) + ": " + str(tb) + "\n"
        st += build_trace(stack)

    if not flag:
        st = f"Unexpected exception while handling client request resource '{path}'\n"

        for stack in tb.stack[:len(tb.stack) - 1]:
            st += build_trace(stack)

        st += "Caused by: " + get_class_chain(exception_type) + ": " + str(tb) + "\n"

        stack = tb.stack[len(tb.stack) - 1]

        st += build_trace(stack)

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
