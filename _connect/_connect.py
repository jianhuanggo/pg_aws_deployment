import contextlib
import functools
from types import SimpleNamespace
from inspect import currentframe
from typing import Callable, TypeVar
from logging import Logger as Log
from _config import _config as _config_
from _common import _common as _common_
from _meta import _meta as _meta_
from _api import _github


RT = TypeVar("RT")

__version__ = "0.5"


@contextlib.contextmanager
def create_session(object_type: str, logger: Log = None) -> Callable:
    """create an instance of reference object based on input object_type

    Args:
        object_type: type of the object
        logger: whether error msg should be persisted in a log file

    Returns: instance of class object

    """
    _config = _config_.PGConfigSingleton()

    _object_dict = {_object_name.lower(): _object_val for _object_name, _object_val in
                    _meta_.PGObjectSingleton().object_registration.items()}

    if object_type.lower() not in _object_dict.keys():
        _common_.error_logger(currentframe().f_code.co_name,
                              f"{object_type} is not found, currently {' '.join(_object_dict.keys())} are supported",
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
    try:
        yield _object_dict.get(object_type.lower(), None).get("object_ptr")(_config)

    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=logger,
                              mode="error",
                              ignore_flag=False)


def object_binding(object_type: str,
                   object_name: str = "",
                   variable_name: str = "pg_action") -> Callable[[Callable[..., RT]], Callable[..., RT]]:
    """this decorator provides the functionality to bind an instance of object to variable_name
       if variable_name is not associated to an object yet

    Args:
        object_type: type of an object
        object_name: name of an object
        variable_name: the binding variable name

    Returns: a function

    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):

            arg_session = variable_name
            func_params = func.__code__.co_varnames

            session_in_args = arg_session in func_params and func_params.index(arg_session) < len(args)
            session_in_kwargs = arg_session in kwargs

            if (session_in_args or session_in_kwargs) and variable_name in kwargs and object_type in kwargs.get(variable_name).__dict__:
                if object_name is None or object_name in kwargs.get(variable_name).__dict__.get(object_type).__dict__:

                    return func(*args, **kwargs)
            else:

                with create_session(object_type) as session:
                    if session:
                        if object_name:
                            object_name_namespace = SimpleNamespace(**{object_name: session})
                            kwargs[variable_name] = SimpleNamespace(**{object_type: object_name_namespace})
                        else:
                            kwargs[variable_name] = session
                return func(*args, **kwargs)
        return wrapper
    return decorator


def get_object(object_name: str, logger: Log = None):
    try:
        return object_binding(object_name)(lambda pg_action: pg_action)()
    except Exception as err:
        _common_.error_logger(currentframe().f_code.co_name,
                              err,
                              logger=logger,
                              mode="error",
                              ignore_flag=False)
