import os
import importlib
import asyncio
from typing import Dict, List, Any
from inspect import currentframe, getmembers, isfunction
from logging import Logger as Log
from functools import wraps
from _util import _util_file as _util_file_
from _common import _common as _common_


def cache_result(filepath: str):
    def wrapper(func):
        @wraps(func)
        def function(*args, **kwargs):
            if os.path.isfile(filepath):
                _common_.info_logger(f"found {filepath}, loading cached result")
                return _util_file_.json_load(filepath)
            try:
                _ret = func(*args, **kwargs)
                _common_.info_logger(f"save result to {filepath}")
                _util_file_.json_dump(filepath, _ret)
                return _ret
            except Exception as err:
                _common_.error_logger(func.__name__,
                                      err,
                                      logger=kwargs.get("logger"),
                                      mode="error",
                                      ignore_flag=False)
        return function
    return wrapper


def load_func(dirpath: str, func_dict: Dict, logger: Log = None):
    """

    :param func_dict:
    :param dirpath:
    :param logger:
    :return:

    make sure file doesn't have . in the filename

    importlib format:  from pythonpath which is set the root dir for the python script, in this case pgcommon + . + python filename (w/o .py)

    """
    # def find_relative_path(abs_filepath: str):
    #     return ''.join([a for a, b in zip_longest(abs_filepath,  os.path.abspath(os.curdir)) if a != b])

    _func_parameter = {}
    try:
        for _each_file in _util_file_.files_in_dir(dirpath):
            # find the path of the file relative to python root directory
            _rel_filepath = _common_.find_relative_path(os.path.join(dirpath, _each_file))

            # remove file extension
            _rel_filepath = ''.join(_rel_filepath.split(".")[:-1]) if _rel_filepath.count(".") > 0 else _rel_filepath

            # remove leading / if exists
            _rel_filepath = _rel_filepath.strip("/")

            # convert /s into dots
            _rel_filepath = _rel_filepath.replace("/", ".")

            print(f"this is a function: {_rel_filepath}")

            # extract callable into a map
            try:
                for _each_callable in (a for a in getmembers(importlib.import_module(_rel_filepath)) if callable(a[1])):
                    func_dict[_each_callable[0]] = _each_callable[1]
            except Exception as err:
                # remove the file if file can't be parsed
                _util_file_.remove_file(_each_file)
                _common_.error_logger(currentframe().f_code.co_name,
                                      err,
                                      logger=logger,
                                      mode="error",
                                      ignore_flag=True)
        return func_dict

    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=logger,
                              mode="error",
                              ignore_flag=False)


def func_call(func_filepath: str, func_name: str, func_parameter: Any, logger: Log = None):
    try:

        # find the path of the file relative to python root directory
        _rel_filepath = _common_.find_relative_path(func_filepath)

        # remove file extension
        _rel_filepath = ''.join(_rel_filepath.split(".")[:-1]) if _rel_filepath.count(".") > 0 else _rel_filepath

        # remove leading / if exists
        _rel_filepath = _rel_filepath.strip("/")

        # convert /s into dots
        _rel_filepath = _rel_filepath.replace("/", ".")

        if isinstance(func_parameter, List):
            getattr(importlib.import_module(_rel_filepath), func_name)(*func_parameter)
        elif isinstance(func_parameter, Dict):
            getattr(importlib.import_module(_rel_filepath), func_name)(**func_parameter)
        else:
            getattr(importlib.import_module(_rel_filepath), func_name)(func_parameter)

    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=logger,
                              mode="error",
                              ignore_flag=False)


def version(version_num: int = 1, logger: Log = None):
    """ This is a safeguard mechanism to safely maintaining A/B version of the code and switch between them,
        if corresponding version 2 is not avaiable, it will automatically switch the version 1

    Parameters:
    :param version_num: there are two versions of code
    :param logger: logger object
    :Returns:
        None

   """
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if version_num == 1:
                return function(*args, **kwargs)
            elif version_num == 2:
                try:
                    return getattr(importlib.import_module(
                        function.__code__.co_filename[_common_.string_search(function.__code__.co_filename, "panoptes"):]
                        .split(".")[0].replace("/", ".").replace("data_collector", "data_collector2"))
                        , function.__qualname__)(*args, **kwargs)
                except Exception as err:
                    return function(*args, **kwargs)

            else:
                _common_.error_logger("version",
                                      f"version number {version_num} is not supported.  "
                                      f"Valid version number supported below:\n"
                                      f"version 1 -> {function.__code__.co_filename}.{function.__qualname__} function\n"
                                      f"version 2 -> {function.__code__.co_filename.replace('data_collector', 'data_collector2')}"
                                      f".{function.__qualname__} function\n",
                                      logger=logger,
                                      mode="critical",
                                      ignore_flag=False)
        return wrapper
    return decorator


def async_decorator(func):
    async def wrapper(*args, **kwargs):
        return await asyncio.run_coroutine_threadsafe(func(*args, **kwargs), asyncio.get_event_loop())
    return wrapper


def sync_to_async(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args, **kwargs)
    return wrapper


def trace_ancestor(class_method):
    """
    this decorator defines a decorator trace_ancestor, which can be applied to methods within classes.
    The decorator captures the execution path and prints details of each function call in reverse order,
    including the file name, class/module name, and method name. The decorator then calls the original
    method and returns its result. This can be useful for debugging and tracing the flow of execution in a program.

    :param class_method:
    :return: modified class_method
    """
    import inspect
    def get_call_stack(class_method_name):

        _execution_object = {}
        call_stack = inspect.stack()
        _execution_path_num = 1

        for frame_info in call_stack[::-1]:
            frame, file_name, line_number, function_name, code_context, *_ = frame_info
            # print(f"File: {file_name}, Line: {line_number}, Function: {function_name}")
            # if code_context:
            #     print("Code Context:")
            #     for line in code_context:
            #         print(line.strip())
            # print("\n")
            locals_dict = frame_info.frame.f_locals
            if 'self' in locals_dict:
                _class_name = locals_dict.get('self', None).__class__.__name__
            elif 'cls' in locals_dict:
                _class_name = locals_dict.get('cls', None).__name__
            else:
                _class_name = None
            _method_name = frame_info.function if frame_info.function != "pg_exe_path_finder" else class_method_name
            _save_parameter = {"filename": file_name,
                               "module": _class_name,
                               "method": _method_name,
                               # "object": frame_info
                               }
            _execution_object[_execution_path_num] = _save_parameter
            _execution_path_num += 1
        return _execution_object

    def pg_exe_path_finder(cls, *args, **kwargs):
        for _call_no, _call_detail in get_call_stack(class_method.__name__).items():
            print(f"call {_call_no}: {_call_detail}")
        ret = class_method(cls, *args, **kwargs)
        return ret

    return pg_exe_path_finder