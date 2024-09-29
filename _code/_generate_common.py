import inspect
import re
import importlib
from typing import Dict
from jinja2 import Template
from _common import _common as _common_

@_common_.exception_handlers(logger=None)
def extract_returned_function_name_with_inspect(function: callable) -> str:
    """
    Extracts the function name that is returned in the provided function using inspect.
    """
    # Get the source code of the provided function using inspect
    source_code = inspect.getsource(function)

    # Use a regular expression to search for a return statement that calls a function
    pattern = re.compile(r'return\s+(.+)')  # Adjust this if needed for different cases
    match = pattern.findall(source_code)

    if match:
        # Return the function name (the second part of the matched group)
        return match[0]  # Group 2 contains the method/function name after the dot
    return "No function returned in the main function."

@_common_.exception_handlers(logger=None)
def apply_template(template: str, params: Dict) -> str:
    return Template(template).render(params)

@_common_.exception_handlers(logger=None)
def load_module_from_path(module_name, filepath):
    """
    Dynamically load a module from the given file path.
    """

    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if spec is None:
        raise ImportError(f"Cannot load the module from the path: {filepath}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@_common_.exception_handlers(logger=None)
def get_function(function_name: str):
    """
    Dynamically load a function from a module.
    """
    module = importlib.import_module("_code._generate_template")
    if hasattr(module, function_name):
        return getattr(module, function_name)()
    else:
        _common_.error_logger(f"No function named {function_name} found in the module.", "FunctionNotFoundError")

@_common_.exception_handlers(logger=None)
def extract_main_param_with_inspect(function: callable) -> list:
    # Get the signature of the function
    signature = inspect.signature(function)

    # Extract parameter names
    return list(signature.parameters.keys())