import re
import os
import importlib.util
import inspect
from _common import _common as _common_
from _code import _generate_common
from _util import _util_file as _util_file_


@_common_.exception_handlers(logger=None)
def extract_from_statements(source_code: str):
    """
    Extracts all lines from the source code that start with the keyword 'from'.
    """

    # Regular expression to match lines that start with 'from', ignoring leading spaces
    from_pattern = re.compile(r'^\s*from\s+.+', re.MULTILINE)

    # Find all matches in the source code
    matches = from_pattern.findall(source_code)

    return matches

@_common_.exception_handlers(logger=None)
def convert_lambda_function(declare_variables: str,
                            variables_extraction: str,
                            return_statement: str,
                            check_variables: str,
                            from_imports: str = "",
                            template_name: str = "generic_lambda_handler") -> str:
    lambda_handler_template = _generate_common.get_function(template_name)

    _params = {
        "from_imports": from_imports,
        "declare_variables": declare_variables,
        "variables_extraction": variables_extraction,
        "check_variables": check_variables,
        "return_statement": return_statement
    }
    return _generate_common.apply_template(lambda_handler_template, _params)




@_common_.exception_handlers(logger=None)
def generate_lambda_handler(filepath: str) -> bool:
    """
    Generate a lambda handler function from a given Python file.
    """

    lambda_handler_filepath = os.path.join(filepath, "lambda_function.py")
    if _util_file_.is_file_exist(lambda_handler_filepath):
        return
    else:
        _common_.info_logger(f"lambda_function.py does not exists in {filepath}, generating it...")

    module_name = 'main'
    module = _generate_common.load_module_from_path(module_name, os.path.join(filepath, "main.py"))

    returned_function_name = ""
    _declare_variables = ""
    _variables_extraction=""
    _from_imports =""
    main_function = None

    # Assuming 'main' is defined in the loaded module
    if hasattr(module, 'main'):
        main_function = getattr(module, 'main')

        # Extract and print the function name returned by the 'main' function
        returned_function_name = _generate_common.extract_returned_function_name_with_inspect(main_function)
        _common_.info_logger(f"The function returned in main() is: {returned_function_name}")
    else:
        _common_.error_logger(f"No 'main' function found in {filepath}", "MainFunctionNotFoundError")

    _function_params = _generate_common.extract_main_param_with_inspect(main_function)
    _declare_variables = '\n'.join([f"    {param} = None" for param in _function_params])
    _variables_extraction = '\n'.join([f"            {param} = query_params.get('{param}', 'default_value_if_missing')" for param in _function_params])
    _check_variables = "        if" + ' or'.join([f" {param} is None" for param in _function_params]) + ":"

    _from_imports = '\n'.join(extract_from_statements(inspect.getsource(main_function)))


    # print(_declare_variables)
    # print(returned_function_name)
    # print(_variables_extraction)
    # print(_from_imports)
    #
    # print(convert_lambda_function(declare_variables=_declare_variables,
    #         variables_extraction=_variables_extraction,
    #         return_statement=returned_function_name,
    #         check_variables=_check_variables,
    #         from_imports=_from_imports.strip()))
    #
    # exit(0)

    _util_file_.write_file(os.path.join(filepath, "lambda_function.py"),
                           convert_lambda_function(declare_variables=_declare_variables,
                                                   variables_extraction=_variables_extraction,
                                                   return_statement=returned_function_name,
                                                   check_variables=_check_variables,
                                                   from_imports=_from_imports.strip())
                           )
    return True







