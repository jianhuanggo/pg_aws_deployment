
from functools import wraps
import inspect
def print_call_stack(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Inspect the current call stack
        stack = inspect.stack()
        print(f"Call stack for {func.__name__}:")
        for frame in stack[1:]:  # Exclude the wrapper function itself from the output
            # Extract information about each frame in the call stack
            info = frame.frame.f_globals.get("__name__", "<unknown>"), frame.function, frame.lineno
            print(f"Module: {info[0]}, Function: {info[1]}, LineNo: {info[2]}")
        result = func(*args, **kwargs)  # Execute the wrapped function
        return result
    return wrapper

# place above decorator to the target function (target function usually resides in another file) which we know it will invoke
# the decorator will print out all the function calls or dependent function it invoked to get to the target function from main
# this great improve the ability to understand the code, use chatgpt to 
# this is not a production version, to modify me to get better

# library_file.py
# ----------------
# @print_call_stack
# def target_function():
#     # set_trace()
#
#     function1()
#
#
#
# my_function.py
# ----------------


def main():
   test()



if __name__ == "__main__":
    my_function()



# set trace is another way to see dependency function
# place set_trace() 
# and unset_trace()




def trace_calls(frame, event, arg):
    if event != "call":
        return
    code = frame.f_code
    func_name = code.co_name
    if func_name == "write":
        # Ignore write() calls from printing
        return
    func_line_no = frame.f_lineno
    func_filename = code.co_filename
    caller = frame.f_back
    caller_line_no = caller.f_lineno
    caller_filename = caller.f_code.co_filename
    print(f"Call to {func_name} on line {func_line_no} of {func_filename} from line {caller_line_no} of {caller_filename}")
    return trace_calls

def set_trace():
    sys.settrace(trace_calls)

def unset_trace():
    sys.settrace(None)


def test():
    set_trace()


   function_call()


    unset_trace()

if __name__ == "__main__":
    test()
